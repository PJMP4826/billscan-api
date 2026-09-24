from typing import Any

from src.infrastructure.database.sql.sql_database_connection_manager import (
    SQLDatabaseConnectionManager,
)
from src.shared.errors.base_exception import NotFoundError
from src.shared.errors.infrastructure_exceptions import PostgresDBException
from src.domain.ports.repositories.receipt_image_repository_port import ReceiptImageRepositoryPort

class ReceiptImageRepository(ReceiptImageRepositoryPort):
    """Repositorio para `receipt_images` (imágenes originales del ticket,
    1:M, soporta múltiples páginas vía `page_number`).

    Cada imagen se inserta ligada a un `receipt_job_id` en el momento del
    upload -- ANTES de que exista un `receipts.id`. `receipt_id` queda en
    NULL hasta que la extracción completa con éxito, momento en el que
    `backfill_receipt_id` actualiza todas las imágenes de ese job de una
    sola vez.

    Sin VO de dominio: `ImageRecord` (image_bytes + mime_type) representa
    los bytes crudos durante el procesamiento OCR, no la referencia
    persistida (file_key en storage externo). Este repositorio
    trabaja con la referencia ya subida, no con los bytes.
    """

    def __init__(self, manager: SQLDatabaseConnectionManager) -> None:
        self._db_manager = manager

    async def insert(
        self,
        receipt_job_id: int,
        file_key: str,
        mime_type: str = "image/jpeg",
        page_number: int = 1,
        receipt_id: int | None = None,
    ) -> int:
        """Inserta una imagen ligada a un job. `receipt_id` normalmente
        es None aquí (se rellena después vía backfill_receipt_id), pero
        se acepta explícito para casos donde ya se conoce de antemano."""
        sql = """
            INSERT INTO receipt_images (
                receipt_job_id,
                receipt_id,
                file_key,
                mime_type,
                page_number
            )
            VALUES (
                :receipt_job_id,
                :receipt_id,
                :file_key,
                :mime_type,
                :page_number
            )
            RETURNING id;
        """
        params: dict[str, Any] = {
            "receipt_job_id": receipt_job_id,
            "receipt_id": receipt_id,
            "file_key": file_key,
            "mime_type": mime_type,
            "page_number": page_number,
        }
        image_id = await self._db_manager.execute_sql_query_fetch_one(sql, params)

        if not image_id:
            raise PostgresDBException(f"Error al guardar imagen en BD {file_key}")
        return int(image_id)

    async def insert_many(
        self, receipt_job_id: int, images: list[dict[str, Any]]
    ) -> list[int]:
        """Inserta varias imágenes (multi-página) ligadas a un job.

        Cada elemento de `images` debe tener las claves: file_key 
        y opcionalmente mime_type, page_number.
        """
        ids: list[int] = []
        for img in images:
            image_id = await self.insert(
                receipt_job_id=receipt_job_id,
                file_key=img["file_key"],
                mime_type=img.get("mime_type", "image/jpeg"),
                page_number=img.get("page_number", 1),
            )
            ids.append(image_id)
        return ids

    async def backfill_receipt_id(self, receipt_job_id: int, receipt_id: int) -> None:
        """Actualiza receipt_id en todas las imágenes de un job, una vez
        que el Receipt fue creado con éxito (paso 4 del flujo de
        inserción acordado)."""
        sql = """
            UPDATE receipt_images
            SET receipt_id = :receipt_id
            WHERE receipt_job_id = :receipt_job_id;
        """
        await self._db_manager.execute_statement(
            sql, {"receipt_job_id": receipt_job_id, "receipt_id": receipt_id}
        )

    async def find_by_receipt_id(self, receipt_id: int) -> list[dict[str, Any]]:
        sql = """
            SELECT
                id,
                receipt_id,
                receipt_job_id,
                file_key,
                mime_type,
                page_number,
                created_at
            FROM receipt_images
            WHERE receipt_id = :receipt_id
            ORDER BY page_number, id;
        """
        return await self._db_manager.execute_sql_query_fetch_all(
            sql, {"receipt_id": receipt_id}
        )

    async def find_key_by_receipt_uuid(self, receipt_uuid: str) -> dict[str, Any]:
        sql = """
            SELECT
                file_key,
            FROM receipt_images
            WHERE receipt_uuid = :receipt_uuid
            ORDER BY page_number, id;
        """
        result = await self._db_manager.execute_sql_query_fetch_first(
            sql, {"receipt_uuid": receipt_uuid}
        )

        if not result:
            raise NotFoundError("Imagen no encontrada")

        return result

    async def find_by_job_id(self, receipt_job_id: int) -> list[dict[str, Any]]:
        """Útil antes de que exista receipt_id -- p.ej. para que el
        worker recupere las imágenes a procesar dado un job_id."""
        sql = """
            SELECT
                id,
                receipt_id,
                receipt_job_id,
                file_key,
                mime_type,
                page_number,
                created_at
            FROM receipt_images
            WHERE receipt_job_id = :receipt_job_id
            ORDER BY page_number, id;
        """
        return await self._db_manager.execute_sql_query_fetch_all(
            sql, {"receipt_job_id": receipt_job_id}
        )

    async def delete_by_receipt_id(self, receipt_id: int) -> None:
        sql = """
            DELETE FROM receipt_images
            WHERE receipt_id = :receipt_id;
        """
        await self._db_manager.execute_statement(sql, {"receipt_id": receipt_id})

    async def delete_by_job_id(self, receipt_job_id: int) -> None:
        sql = """
            DELETE FROM receipt_images
            WHERE receipt_job_id = :receipt_job_id;
        """
        await self._db_manager.execute_statement(
            sql, {"receipt_job_id": receipt_job_id}
        )
