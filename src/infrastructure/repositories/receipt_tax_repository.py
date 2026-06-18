from typing import Any

from src.domain.value_objects.tax_detail import TaxDetail
from src.infrastructure.database.sql.sql_database_connection_manager import (
    SQLDatabaseConnectionManager,
)
from src.shared.errors.infrastructure_exceptions import PostgresDBException
from src.domain.ports.repositories.receipt_tax_repository_port import (
    ReceiptTaxRepositoryPort,
)


class ReceiptTaxRepository(ReceiptTaxRepositoryPort):
    """Repositorio para la tabla `receipt_taxes` (desglose de impuestos 1:M)."""

    def __init__(self, manager: SQLDatabaseConnectionManager) -> None:
        self._db_manager = manager

    async def insert(self, receipt_id: int, tax: TaxDetail) -> int:
        """Inserta una línea de impuesto y devuelve su `id` (BIGSERIAL)."""
        sql = """
            INSERT INTO receipt_taxes (
                receipt_id,
                tax_name,
                tax_rate,
                amount
            )
            VALUES (
                :receipt_id,
                :tax_name,
                :tax_rate,
                :amount
            )
            RETURNING id;
        """
        params: dict[str, Any] = {
            "receipt_id": receipt_id,
            "tax_name": tax.name,
            "tax_rate": tax.rate,
            "amount": tax.amount,
        }
        tax_id = await self._db_manager.execute_sql_query_fetch_one(sql, params)

        if not tax_id:
            raise PostgresDBException("" "Error al guardar los impuestos del Ticket")

        return int(tax_id)

    async def insert_many(self, receipt_id: int, taxes: list[TaxDetail]) -> list[int]:
        """Inserta varias líneas de impuesto secuencialmente.

        NOTA de atomicidad: igual que ReceiptItemRepository.insert_many,
        cada INSERT es su propia transacción.
        """
        return [await self.insert(receipt_id, tax) for tax in taxes]

    async def find_by_receipt_id(self, receipt_id: int) -> list[dict[str, Any]]:
        sql = """
            SELECT
                id,
                receipt_id,
                tax_name,
                tax_rate,
                amount
            FROM receipt_taxes
            WHERE receipt_id = :receipt_id
            ORDER BY id;
        """
        return await self._db_manager.execute_sql_query_fetch_all(
            sql, {"receipt_id": receipt_id}
        )

    async def delete_by_receipt_id(self, receipt_id: int) -> None:
        sql = """
            DELETE FROM receipt_taxes
            WHERE receipt_id = :receipt_id;
        """
        await self._db_manager.execute_statement(sql, {"receipt_id": receipt_id})
