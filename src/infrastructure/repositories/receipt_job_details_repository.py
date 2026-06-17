from typing import Any

from src.infrastructure.database.sql.sql_database_connection_manager import (
    SQLDatabaseConnectionManager,
)
from src.shared.errors.infrastructure_exceptions import PostgresDBException
from src.domain.ports.repositories.receipt_job_details_repository_port import ReceiptJobDetailsRepositoryPort

class ReceiptJobDetailsRepository(ReceiptJobDetailsRepositoryPort):
    """Repositorio para `receipt_jobs_details`.

    Esta tabla rastrea el ciclo de vida de extracción de un ticket
    (RECEIVED -> EXTRACTING -> COMPLETED/FAILED), independiente del
    agregado `Receipt` -- que no existe hasta que la extracción completa
    con éxito. `receipt_id` permanece NULL hasta entonces.
    """

    def __init__(self, manager: SQLDatabaseConnectionManager) -> None:
        self._db_manager = manager

    async def create(self, user_id: str, job_name: str) -> int:
        """Crea el job en estado RECEIVED. Devuelve el `id` (BIGSERIAL).

        Se llama al recibir la imagen, antes de encolar el worker en
        background.
        """
        sql = """
            INSERT INTO receipt_jobs_details (user_id, status, job_name)
            VALUES (:user_id, 'RECEIVED', :job_name)
            RETURNING id;
        """
        job_id = await self._db_manager.execute_sql_query_fetch_one(
            sql, {"user_id": user_id, "job_name": job_name}
        )

        if not job_id:
            raise PostgresDBException(
                f"Error al crear receipt_jobs_details para user_id {user_id}"
            )
        return int(job_id)

    async def mark_extracting(self, job_id: int) -> None:
        """Transición RECEIVED -> EXTRACTING. Se llama al inicio del
        worker, justo antes de invocar al LLM/OCR."""
        sql = """
            UPDATE receipt_jobs_details
            SET status = 'EXTRACTING',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id;
        """
        await self._db_manager.execute_statement(sql, {"id": job_id})

    async def mark_completed(self, job_id: int, receipt_id: int) -> None:
        """Transición EXTRACTING -> COMPLETED. Backfill de receipt_id una
        vez que el agregado Receipt fue persistido con éxito."""
        sql = """
            UPDATE receipt_jobs_details
            SET status = 'COMPLETED',
                receipt_id = :receipt_id,
                error_message = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id;
        """
        await self._db_manager.execute_statement(
            sql, {"id": job_id, "receipt_id": receipt_id}
        )

    async def mark_failed(self, job_id: int, error_message: str) -> None:
        """Transición RECEIVED/EXTRACTING -> FAILED. No toca receipt_id
        (permanece NULL, nunca se creó un Receipt)."""
        sql = """
            UPDATE receipt_jobs_details
            SET status = 'FAILED',
                error_message = :error_message,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id;
        """
        await self._db_manager.execute_statement(
            sql, {"id": job_id, "error_message": error_message}
        )

    async def find_by_id(self, job_id: int) -> dict[str, Any] | None:
        sql = """
            SELECT
                id,
                user_id,
                status,
                error_message,
                receipt_id,
                created_at,
                updated_at
            FROM receipt_jobs_details
            WHERE id = :id;
        """
        return await self._db_manager.execute_sql_query_fetch_first(sql, {"id": job_id})

    async def find_by_user_id(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Lista jobs de un usuario, más recientes primero. Útil para que
        la app móvil muestre 'tickets en proceso' en tiempo real."""
        sql = """
            SELECT
                id,
                user_id,
                status,
                error_message,
                receipt_id,
                created_at,
                updated_at
            FROM receipt_jobs_details
            WHERE user_id = :user_id
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset;
        """
        return await self._db_manager.execute_sql_query_fetch_all(
            sql, {"user_id": user_id, "limit": limit, "offset": offset}
        )

    async def find_by_user_id_with_images(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Igual que find_by_user_id, pero incluye las imágenes de cada
        job (clave 'images' en cada dict). Pensado para la vista de la
        app móvil donde se necesita mostrar miniaturas de tickets en
        proceso, incluso antes de que exista receipt_id.

        Usa UNA sola query adicional con `receipt_job_id IN (...)` en
        lugar de una query por job (evita N+1).
        """
        jobs = await self.find_by_user_id(user_id, limit=limit, offset=offset)
        if not jobs:
            return jobs

        job_ids = [job["id"] for job in jobs]

        sql_get_images = """
            SELECT
                id,
                receipt_id,
                receipt_job_id,
                file_key,
                file_url,
                mime_type,
                page_number
            FROM receipt_images
            WHERE receipt_job_id = ANY(:job_ids)
            ORDER BY receipt_job_id, page_number, id;
        """
        images = await self._db_manager.execute_sql_query_fetch_all(
            sql_get_images, {"job_ids": job_ids}
        )

        images_by_job: dict[int, list[dict[str, Any]]] = {jid: [] for jid in job_ids}
        for img in images:
            images_by_job[img["receipt_job_id"]].append(img)

        for job in jobs:
            job["images"] = images_by_job.get(job["id"], [])

        return jobs

    async def find_pending(self, limit: int = 100) -> list[dict[str, Any]]:
        """Jobs en RECEIVED o EXTRACTING -- útil para detectar jobs
        atascados (p.ej. el worker murió a mitad de proceso)."""
        sql = """
            SELECT
                id,
                user_id,
                status,
                created_at,
                updated_at
            FROM receipt_jobs_details
            WHERE status IN ('RECEIVED', 'EXTRACTING')
            ORDER BY created_at ASC
            LIMIT :limit;
        """
        return await self._db_manager.execute_sql_query_fetch_all(sql, {"limit": limit})
