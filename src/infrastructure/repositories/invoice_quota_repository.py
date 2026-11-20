from sqlalchemy import text

from src.config.logger import logger
from src.domain.enums.invoice_quota_status import InvoiceQuotaStatus
from src.domain.ports.repositories.invoice_quota_repository_port import (
    InvoiceQuotaRepositoryPort,
)
from src.infrastructure.database.sql.sql_database_connection_manager import (
    SQLDatabaseConnectionManager,
)
from src.shared.errors.infrastructure_exceptions import PostgresDBException

_IN_USE_STATUSES = (
    InvoiceQuotaStatus.RESERVED.value,
    InvoiceQuotaStatus.CONSUMED.value,
)


class InvoiceQuotaRepository(InvoiceQuotaRepositoryPort):
    """Repositorio de cuota de facturas por RFC.

    La reserva se hace dentro de una transacción con un advisory lock por
    ``rfc_hash`` para que dos jobs concurrentes del mismo RFC no pasen ambos
    la validación del límite.
    """

    def __init__(self, manager: SQLDatabaseConnectionManager) -> None:
        self._db_manager = manager

    async def try_reserve(
        self, receipt_id: int, rfc_hash: str, max_invoices: int
    ) -> bool:
        if max_invoices <= 0:
            return False

        try:
            async with self._db_manager.engine.begin() as conn:
                await conn.execute(
                    text(
                        "SELECT pg_advisory_xact_lock("
                        "hashtextextended(:rfc_hash, 0));"
                    ),
                    {"rfc_hash": rfc_hash},
                )

                existing = (
                    await conn.execute(
                        text(
                            "SELECT status FROM invoice_quota_usages "
                            "WHERE receipt_id = :receipt_id;"
                        ),
                        {"receipt_id": receipt_id},
                    )
                ).first()

                # Reintento del mismo ticket: ya tenía cupo, no consume otro.
                if existing is not None and existing[0] in _IN_USE_STATUSES:
                    return True

                used = (
                    await conn.execute(
                        text(
                            "SELECT COUNT(*) FROM invoice_quota_usages "
                            "WHERE rfc_hash = :rfc_hash "
                            "AND status IN (:reserved, :consumed);"
                        ),
                        {
                            "rfc_hash": rfc_hash,
                            "reserved": InvoiceQuotaStatus.RESERVED.value,
                            "consumed": InvoiceQuotaStatus.CONSUMED.value,
                        },
                    )
                ).scalar_one()

                if int(used) >= max_invoices:
                    # No se escribe nada: el commit de este bloque es inocuo.
                    return False

                await conn.execute(
                    text(
                        """
                        INSERT INTO invoice_quota_usages (rfc_hash, receipt_id, status)
                        VALUES (:rfc_hash, :receipt_id, :reserved)
                        ON CONFLICT (receipt_id) DO UPDATE
                        SET rfc_hash = EXCLUDED.rfc_hash,
                            status = :reserved;
                        """
                    ),
                    {
                        "rfc_hash": rfc_hash,
                        "receipt_id": receipt_id,
                        "reserved": InvoiceQuotaStatus.RESERVED.value,
                    },
                )
                return True
        except Exception as exc:
            logger.error(
                "Error al reservar cuota de facturación (receipt_id=%s): %s",
                receipt_id,
                exc,
            )
            raise PostgresDBException(
                "Error al reservar cuota de facturación"
            ) from exc

    async def release(self, receipt_id: int) -> None:
        sql = """
            UPDATE invoice_quota_usages
            SET status = :released
            WHERE receipt_id = :receipt_id
              AND status <> :consumed;
        """
        await self._db_manager.execute_statement(
            sql,
            {
                "receipt_id": receipt_id,
                "released": InvoiceQuotaStatus.RELEASED.value,
                "consumed": InvoiceQuotaStatus.CONSUMED.value,
            },
        )

    async def mark_consumed(self, receipt_id: int) -> None:
        sql = """
            UPDATE invoice_quota_usages
            SET status = :consumed
            WHERE receipt_id = :receipt_id;
        """
        await self._db_manager.execute_statement(
            sql,
            {
                "receipt_id": receipt_id,
                "consumed": InvoiceQuotaStatus.CONSUMED.value,
            },
        )

    async def count_in_use(self, rfc_hash: str) -> int:
        sql = """
            SELECT COUNT(*)
            FROM invoice_quota_usages
            WHERE rfc_hash = :rfc_hash
              AND status IN (:reserved, :consumed);
        """
        count = await self._db_manager.execute_sql_query_fetch_one(
            sql,
            {
                "rfc_hash": rfc_hash,
                "reserved": InvoiceQuotaStatus.RESERVED.value,
                "consumed": InvoiceQuotaStatus.CONSUMED.value,
            },
        )
        return int(count) if count is not None else 0
