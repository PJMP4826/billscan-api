from decimal import Decimal
from typing import Any

from src.infrastructure.database.sql.sql_database_connection_manager import (
    SQLDatabaseConnectionManager,
)
from src.shared.errors.infrastructure_exceptions import PostgresDBException
from src.domain.ports.repositories.receipt_payment_repository_port import (
    ReceiptPaymentRepositoryPort,
)


class ReceiptPaymentRepository(ReceiptPaymentRepositoryPort):
    """Repositorio para la tabla `receipt_payments` (pagos múltiples / split
    payments, 1:M).

    NOTA - sin VO de dominio aún:
    `Receipt.payment` es un único `PaymentInfo`, no una lista. No existe
    hoy un value object que represente "una lista de pagos" para mapear
    aquí. Este repositorio expone parámetros escalares en lugar de aceptar
    `PaymentInfo`, como placeholder explícito para cuando se modele split
    payments en el dominio.

    Para el caso 95% (un solo método de pago), los datos ya están
    denormalizados en `receipts` (payment_method_code, card_last_four,
    authorization_code) y esta tabla puede no usarse en absoluto.
    """

    def __init__(self, manager: SQLDatabaseConnectionManager) -> None:
        self._db_manager = manager

    async def insert(
        self,
        receipt_id: int,
        payment_method_code: str,
        amount: Decimal,
        card_last_four: str | None = None,
        authorization_code: str | None = None,
    ) -> int:
        """Inserta un registro de pago y devuelve su `id` (BIGSERIAL)."""
        sql = """
            INSERT INTO receipt_payments (
                receipt_id,
                payment_method_code,
                amount,
                card_last_four,
                authorization_code
            )
            VALUES (
                :receipt_id,
                :payment_method_code,
                :amount,
                :card_last_four,
                :authorization_code
            )
            RETURNING id;
        """
        params: dict[str, Any] = {
            "receipt_id": receipt_id,
            "payment_method_code": payment_method_code,
            "amount": amount,
            "card_last_four": card_last_four,
            "authorization_code": authorization_code,
        }
        payment_id = await self._db_manager.execute_sql_query_fetch_one(sql, params)

        if not payment_id:
            raise PostgresDBException("Error al guardar los pagos")
        return int(payment_id)

    async def find_by_receipt_id(self, receipt_id: int) -> list[dict[str, Any]]:
        sql = """
            SELECT
                id,
                receipt_id,
                payment_method_code,
                amount,
                card_last_four,
                authorization_code,
                created_at
            FROM receipt_payments
            WHERE receipt_id = :receipt_id
            ORDER BY id;
        """
        return await self._db_manager.execute_sql_query_fetch_all(
            sql, {"receipt_id": receipt_id}
        )

    async def delete_by_receipt_id(self, receipt_id: int) -> None:
        sql = """
            DELETE FROM receipt_payments
            WHERE receipt_id = :receipt_id;
        """
        await self._db_manager.execute_statement(sql, {"receipt_id": receipt_id})
