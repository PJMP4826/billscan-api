from typing import Any

from src.infrastructure.database.sql.sql_database_connection_manager import (
    SQLDatabaseConnectionManager,
)
from src.shared.errors.infrastructure_exceptions import PostgresDBException


class BillingFileRepository:
    """Repositorio para `billing_files` (XML/PDF de factura, 1:M).

    Sin VO de dominio: estos registros son referencias a archivos
    almacenados externamente (S3/equivalente), poblados después de que
    FacturaGPT entrega la factura vía webhook.
    """

    def __init__(self, manager: SQLDatabaseConnectionManager) -> None:
        self._db_manager = manager

    async def insert(
        self,
        receipt_id: int,
        file_type: str | None,
        file_key: str,
        file_url: str,
        mime_type: str | None = None,
    ) -> int:
        sql = """
            INSERT INTO billing_files (
                receipt_id,
                file_type,
                file_key,
                file_url,
                mime_type
            )
            VALUES (
                :receipt_id,
                :file_type,
                :file_key,
                :file_url,
                :mime_type
            )
            RETURNING id;
        """
        params: dict[str, Any] = {
            "receipt_id": receipt_id,
            "file_type": file_type,
            "file_key": file_key,
            "file_url": file_url,
            "mime_type": mime_type,
        }
        file_id = await self._db_manager.execute_sql_query_fetch_one(sql, params)

        if not file_id:
            raise PostgresDBException(
                f"Error guardando archivo de facturacion del tipo {file_type}"
            )
        return int(file_id)

    async def find_by_receipt_id(self, receipt_id: int) -> list[dict[str, Any]]:
        sql = """
            SELECT
                id,
                receipt_id,
                file_type,
                file_key,
                file_url,
                mime_type,
                created_at
            FROM billing_files
            WHERE receipt_id = :receipt_id
            ORDER BY id;
        """
        return await self._db_manager.execute_sql_query_fetch_all(
            sql, {"receipt_id": receipt_id}
        )

    async def delete_by_receipt_id(self, receipt_id: int) -> None:
        sql = """
            DELETE FROM billing_files
            WHERE receipt_id = :receipt_id;
        """
        await self._db_manager.execute_statement(sql, {"receipt_id": receipt_id})
