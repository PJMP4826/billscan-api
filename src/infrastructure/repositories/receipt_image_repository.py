from typing import Any

from src.infrastructure.database.sql.sql_database_connection_manager import (
    SQLDatabaseConnectionManager,
)
from src.shared.errors.infrastructure_exceptions import PostgresDBException


class ReceiptImageRepository:
    """Repositorio para `receipt_images` (imágenes originales del ticket,
    1:M, soporta múltiples páginas vía `page_number`).

    Sin VO de dominio: `ImageRecord` (image_bytes + mime_type) representa
    los bytes crudos durante el procesamiento OCR, no la referencia
    persistida (file_key/file_url en storage externo). Este repositorio
    trabaja con la referencia ya subida, no con los bytes.
    """

    def __init__(self, manager: SQLDatabaseConnectionManager) -> None:
        self._db_manager = manager

    async def insert(
        self,
        receipt_id: int,
        file_key: str,
        file_url: str,
        mime_type: str = "image/jpeg",
        page_number: int = 1,
    ) -> int:
        sql = """
            INSERT INTO receipt_images (
                receipt_id,
                file_key,
                file_url,
                mime_type,
                page_number
            )
            VALUES (
                :receipt_id,
                :file_key,
                :file_url,
                :mime_type,
                :page_number
            )
            RETURNING id;
        """
        params: dict[str, Any] = {
            "receipt_id": receipt_id,
            "file_key": file_key,
            "file_url": file_url,
            "mime_type": mime_type,
            "page_number": page_number,
        }
        image_id = await self._db_manager.execute_sql_query_fetch_one(sql, params)

        if not image_id:
            raise PostgresDBException(
                f"Error al guardar imagen en BD {file_key}"
            )
        return int(image_id)

    async def insert_many(
        self, receipt_id: int, images: list[dict[str, Any]]
    ) -> list[int]:
        """Inserta varias imágenes (multi-página).

        Cada elemento de `images` debe tener las claves: file_key,
        file_url, y opcionalmente mime_type, page_number.
        """
        ids: list[int] = []
        for img in images:
            image_id = await self.insert(
                receipt_id=receipt_id,
                file_key=img["file_key"],
                file_url=img["file_url"],
                mime_type=img.get("mime_type", "image/jpeg"),
                page_number=img.get("page_number", 1),
            )
            ids.append(image_id)
        return ids

    async def find_by_receipt_id(self, receipt_id: int) -> list[dict[str, Any]]:
        sql = """
            SELECT
                id,
                receipt_id,
                file_key,
                file_url,
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

    async def delete_by_receipt_id(self, receipt_id: int) -> None:
        sql = """
            DELETE FROM receipt_images
            WHERE receipt_id = :receipt_id;
        """
        await self._db_manager.execute_statement(sql, {"receipt_id": receipt_id})
