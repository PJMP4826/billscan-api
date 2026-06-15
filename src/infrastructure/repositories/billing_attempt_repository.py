import json
from typing import Any

from src.infrastructure.database.sql.sql_database_connection_manager import (
    SQLDatabaseConnectionManager,
)


class BillingAttemptRepository:
    """Repositorio para `billing_attempts` (historial/auditoría de
    intentos de facturación con FacturaGPT, 1:M, append-only).

    `response_payload` se serializa con json.dumps() -- mismo caveat de
    doble-codificación señalado en ReceiptItemRepository.
    """

    def __init__(self, manager: SQLDatabaseConnectionManager) -> None:
        self._db_manager = manager

    async def insert(
        self,
        receipt_id: int,
        status: str,
        session_id: str | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
        response_payload: dict[str, Any] | None = None,
    ) -> int | None:
        sql = """
            INSERT INTO billing_attempts (
                receipt_id,
                session_id,
                status,
                error_code,
                error_message,
                response_payload
            )
            VALUES (
                :receipt_id,
                :session_id,
                :status,
                :error_code,
                :error_message,
                :response_payload
            )
            RETURNING id;
        """
        params: dict[str, Any] = {
            "receipt_id": receipt_id,
            "session_id": session_id,
            "status": status,
            "error_code": error_code,
            "error_message": error_message,
            "response_payload": (
                json.dumps(response_payload)
                if response_payload is not None
                else None
            ),
        }
        attempt_id = await self._db_manager.execute_sql_query_fetch_one(sql, params)

        if attempt_id:
            return int(attempt_id)

    async def find_by_receipt_id(self, receipt_id: int) -> list[dict[str, Any]]:
        """Devuelve el historial de intentos, más reciente primero."""
        sql = """
            SELECT
                id,
                receipt_id,
                session_id,
                status,
                attempted_at,
                error_code,
                error_message,
                response_payload
            FROM billing_attempts
            WHERE receipt_id = :receipt_id
            ORDER BY attempted_at DESC;
        """
        return await self._db_manager.execute_sql_query_fetch_all(
            sql, {"receipt_id": receipt_id}
        )

    async def find_latest_by_receipt_id(
        self, receipt_id: int
    ) -> dict[str, Any] | None:
        sql = """
            SELECT
                id,
                receipt_id,
                session_id,
                status,
                attempted_at,
                error_code,
                error_message,
                response_payload
            FROM billing_attempts
            WHERE receipt_id = :receipt_id
            ORDER BY attempted_at DESC
            LIMIT 1;
        """
        return await self._db_manager.execute_sql_query_fetch_first(
            sql, {"receipt_id": receipt_id}
        )
