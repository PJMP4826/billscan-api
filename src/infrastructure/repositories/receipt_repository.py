import json
from typing import Any

from src.domain.entities.receipt import Receipt
from src.infrastructure.database.sql.sql_database_connection_manager import (
    SQLDatabaseConnectionManager,
)
from src.shared.errors.infrastructure_exceptions import PostgresDBException


class ReceiptRepository:
    """Repositorio para la tabla `receipts` (cabecera del agregado).


    NOTA - reconstrucción de entidades:
    Los métodos de lectura (`find_by_id`, `find_by_uuid`) devuelven
    `dict[str, Any]` crudos, NO instancias de `Receipt`. Reconstruir un
    `Receipt` válido requiere también `items`, `taxes`, `payment` y
    `billing` desde sus respectivos repositorios (Receipt.__post_init__
    exige items no vacíos). Esa composición es responsabilidad de la capa
    de orquestación (caso de uso / servicio de aplicación).
    """

    def __init__(self, manager: SQLDatabaseConnectionManager) -> None:
        self._db_manager = manager

    async def insert(
        self,
        receipt: Receipt,
        merchant_id: int | None,
        user_id: str | None,
        payment_method_code: str,
    ) -> int:
        """Inserta la cabecera del recibo y devuelve el `id` (BIGSERIAL).

        `merchant_id`, `user_id` y `payment_method_code` son FKs resueltas
        previamente por la capa de orquestación (este repositorio no
        conoce MerchantRepository/UserRepository/PaymentMethodRepository).
        """
        totals = receipt.totals
        transaction = receipt.transaction
        payment = receipt.payment

        extra_metadata = (
            json.dumps(receipt.extra_metadata)
            if receipt and receipt.extra_metadata is not None
            else None
        )

        sql = """
            INSERT INTO receipts (
                user_id,
                merchant_id,
                payment_method_code,
                transaction_date,
                transaction_time,
                ticket_number,
                pos_id,
                cashier,
                subtotal,
                total_discount,
                total,
                amount_paid,
                "change",
                card_last_four,
                authorization_code,
                context_notes,
                receipt_uuid,
                extra_metadata
            )
            VALUES (
                :user_id,
                :merchant_id,
                :payment_method_code,
                :transaction_date,
                :transaction_time,
                :ticket_number,
                :pos_id,
                :cashier,
                :subtotal,
                :total_discount,
                :total,
                :amount_paid,
                :change,
                :card_last_four,
                :authorization_code,
                :context_notes,
                :receipt_uuid,
                :extra_metadata
            )
            RETURNING id;
        """
        params: dict[str, Any] = {
            "user_id": user_id,
            "merchant_id": merchant_id,
            "payment_method_code": payment_method_code,
            "transaction_date": transaction.transaction_date,
            "transaction_time": transaction.transaction_time,
            "ticket_number": transaction.ticket_number,
            "pos_id": transaction.pos_id,
            "cashier": transaction.cashier,
            "subtotal": totals.subtotal,
            "total_discount": totals.total_discount,
            "total": totals.total,
            "amount_paid": totals.amount_paid,
            "change": totals.change,
            "card_last_four": payment.card_last_four,
            "authorization_code": payment.authorization_code,
            "context_notes": receipt.context_notes,
            "receipt_uuid": receipt.receipt_uuid,
            "extra_metadata": extra_metadata
        }

        receipt_id = await self._db_manager.execute_sql_query_fetch_one(sql, params)

        if not receipt_id:
            raise PostgresDBException(
                "Error al guardar Ticket en BD"
            )
        return int(receipt_id)

    async def find_by_id(self, receipt_id: int) -> dict[str, Any] | None:
        sql = """
            SELECT
                id,
                user_id,
                merchant_id,
                payment_method_code,
                transaction_date,
                transaction_time,
                ticket_number,
                pos_id,
                cashier,
                subtotal,
                total_discount,
                total,
                amount_paid,
                "change",
                card_last_four,
                authorization_code,
                context_notes,
                receipt_uuid,
                created_at,
                updated_at
            FROM receipts
            WHERE id = :id;
        """
        return await self._db_manager.execute_sql_query_fetch_first(
            sql, {"id": receipt_id}
        )

    async def find_by_uuid(self, receipt_uuid: str) -> dict[str, Any] | None:
        sql = """
            SELECT
                id,
                user_id,
                merchant_id,
                payment_method_code,
                transaction_date,
                transaction_time,
                ticket_number,
                pos_id,
                cashier,
                subtotal,
                total_discount,
                total,
                amount_paid,
                "change",
                card_last_four,
                authorization_code,
                context_notes,
                receipt_uuid,
                created_at,
                updated_at
            FROM receipts
            WHERE receipt_uuid = :receipt_uuid;
        """
        return await self._db_manager.execute_sql_query_fetch_first(
            sql, {"receipt_uuid": receipt_uuid}
        )

    async def find_by_user_id(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Lista recibos de un usuario, más recientes primero."""
        sql = """
            SELECT
                id,
                merchant_id,
                payment_method_code,
                transaction_date,
                transaction_time,
                ticket_number,
                total,
                receipt_uuid,
                created_at
            FROM receipts
            WHERE user_id = :user_id
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset;
        """
        return await self._db_manager.execute_sql_query_fetch_all(
            sql, {"user_id": user_id, "limit": limit, "offset": offset}
        )

    async def update_merchant_and_payment(
        self,
        receipt_id: int,
        merchant_id: int | None,
        payment_method_code: str,
    ) -> None:
        """Actualiza las FKs de comercio y método de pago de un recibo
        existente (p.ej. corrección manual post-OCR)."""
        sql = """
            UPDATE receipts
            SET merchant_id = :merchant_id,
                payment_method_code = :payment_method_code,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id;
        """
        await self._db_manager.execute_statement(
            sql,
            {
                "id": receipt_id,
                "merchant_id": merchant_id,
                "payment_method_code": payment_method_code,
            },
        )

    async def delete(self, receipt_id: int) -> None:
        """Elimina un recibo. ON DELETE CASCADE en el esquema propaga a
        receipt_items, receipt_taxes, receipt_payments,
        receipt_billing_details, billing_files, receipt_images y
        billing_attempts."""
        sql = """
            DELETE FROM receipts
            WHERE id = :id;
        """
        await self._db_manager.execute_statement(sql, {"id": receipt_id})
