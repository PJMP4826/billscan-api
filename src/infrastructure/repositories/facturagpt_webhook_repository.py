import json
from typing import Any

from src.infrastructure.database.sql.sql_database_connection_manager import (
    SQLDatabaseConnectionManager,
)
from src.domain.ports.repositories.facturagpt_webhook_repository_port import (
    FacturaGPTWebhookRepositoryPort,
)


class FacturaGPTWebhookRepository(FacturaGPTWebhookRepositoryPort):
    """Repositorio para `facturagpt_webhooks` (idempotencia de webhooks,
    PK = idempotency_key).

    `insert_if_new` usa `ON CONFLICT ... DO NOTHING` y devuelve un bool:
    - True  -> el webhook es nuevo, fue insertado, el caller debe procesarlo.
    - False -> idempotency_key ya existía, el caller debe ignorarlo
      (procesamiento duplicado evitado).

    Esto evita que el flujo normal (un webhook duplicado por reintento de
    red de FacturaGPT) dependa de capturar una excepción de violación de
    PK -- la duplicación es un caso esperado, no un error.

    Semántica de `processed_at` (NULLABLE tras la migración ad576528aa27):
    NULL = recibido pero no procesado correctamente (pendiente o falló);
    el worker lo setea al terminar con éxito.
    """

    def __init__(self, manager: SQLDatabaseConnectionManager) -> None:
        self._db_manager = manager

    async def insert_if_new(
        self,
        idempotency_key: str,
        event_type: str,
        session_id: str,
        payload: dict[str, Any],
    ) -> bool:
        sql = """
            INSERT INTO facturagpt_webhooks (
                idempotency_key,
                event_type,
                session_id,
                payload
            )
            VALUES (
                :idempotency_key,
                :event_type,
                :session_id,
                :payload
            )
            ON CONFLICT (idempotency_key) DO NOTHING
            RETURNING idempotency_key;
        """
        params = {
            "idempotency_key": idempotency_key,
            "event_type": event_type,
            "session_id": session_id,
            "payload": json.dumps(payload),
        }
        result = await self._db_manager.execute_sql_query_fetch_one(sql, params)
        return result is not None

    async def find_by_key(self, idempotency_key: str) -> dict[str, Any] | None:
        sql = """
            SELECT
                idempotency_key,
                event_type,
                session_id,
                payload,
                received_at,
                processed_at,
                last_error,
                receipt_id
            FROM facturagpt_webhooks
            WHERE idempotency_key = :idempotency_key;
        """
        return await self._db_manager.execute_sql_query_fetch_first(
            sql, {"idempotency_key": idempotency_key}
        )

    async def find_by_session_id(self, session_id: str) -> list[dict[str, Any]]:
        sql = """
            SELECT
                idempotency_key,
                event_type,
                session_id,
                payload,
                received_at,
                processed_at,
                last_error,
                receipt_id
            FROM facturagpt_webhooks
            WHERE session_id = :session_id
            ORDER BY processed_at;
        """
        return await self._db_manager.execute_sql_query_fetch_all(
            sql, {"session_id": session_id}
        )

    async def mark_processed(self, idempotency_key: str) -> bool:
        """Marca el evento como procesado SOLO si no lo estaba. Devuelve True
        si esta llamada ganó el marcado (evita doble procesamiento)."""
        sql = """
            UPDATE facturagpt_webhooks
            SET processed_at = CURRENT_TIMESTAMP,
                last_error = NULL
            WHERE idempotency_key = :idempotency_key
              AND processed_at IS NULL
            RETURNING idempotency_key;
        """
        result = await self._db_manager.execute_sql_query_fetch_one(
            sql, {"idempotency_key": idempotency_key}
        )
        return result is not None

    async def update_error(
        self, idempotency_key: str, error_message: str | None
    ) -> None:
        """Registra el error del worker dejando `processed_at` en NULL para
        permitir un reintento (duplicado de red o reconciliación)."""
        sql = """
            UPDATE facturagpt_webhooks
            SET last_error = :error_message
            WHERE idempotency_key = :idempotency_key;
        """
        await self._db_manager.execute_statement(
            sql,
            {
                "idempotency_key": idempotency_key,
                "error_message": error_message,
            },
        )
