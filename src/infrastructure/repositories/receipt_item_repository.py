import json
from typing import Any

from src.domain.value_objects.line_item import LineItem
from src.infrastructure.database.sql.sql_database_connection_manager import (
    SQLDatabaseConnectionManager,
)
from src.shared.errors.infrastructure_exceptions import PostgresDBException


class ReceiptItemRepository:
    """Repositorio para la tabla `receipt_items` (detalle 1:M de un recibo).

    NOTA - serialización JSONB:
    `item_metadata` se serializa explícitamente con `json.dumps()` antes de
    enviarse como parámetro. Si el driver/engine ya adapta dict -> JSONB de
    forma automática, esto causaría doble-codificación (string JSON dentro
    de un campo JSONB). Verificar contra la configuración real de
    SQLAlchemy/asyncpg y ajustar si es necesario.
    """

    def __init__(self, manager: SQLDatabaseConnectionManager) -> None:
        self._db_manager = manager

    async def insert(self, receipt_id: int, item: LineItem) -> int:
        """Inserta un artículo del recibo y devuelve su `id` (BIGSERIAL)."""
        sql = """
            INSERT INTO receipt_items (
                receipt_id,
                quantity,
                description,
                sku,
                unit_price,
                total_price,
                discount,
                item_metadata
            )
            VALUES (
                :receipt_id,
                :quantity,
                :description,
                :sku,
                :unit_price,
                :total_price,
                :discount,
                :item_metadata
            )
            RETURNING id;
        """
        params: dict[str, Any] = {
            "receipt_id": receipt_id,
            "quantity": item.quantity,
            "description": item.description,
            "sku": item.sku,
            "unit_price": item.unit_price,
            "total_price": item.total_price,
            "discount": item.discount,
            "item_metadata": (
                json.dumps(item.item_metadata)
                if item.item_metadata is not None
                else None
            ),
        }
        item_id = await self._db_manager.execute_sql_query_fetch_one(sql, params)

        if not item_id:
            raise PostgresDBException(
                "Error al guardar los items del Ticket"
            )
        return int(item_id)

    async def insert_many(self, receipt_id: int, items: list[LineItem]) -> list[int]:
        """Inserta varios artículos secuencialmente.

        NOTA: cada llamada a `insert` abre/cierra su propia transacción
        (ver SQLDatabaseConnectionManager). Si falla el item N, los items
        1..N-1 quedan persistidos. Ver advertencia de atomicidad acordada
        para la capa de orquestación.
        """
        return [await self.insert(receipt_id, item) for item in items]

    async def find_by_receipt_id(self, receipt_id: int) -> list[dict[str, Any]]:
        sql = """
            SELECT
                id,
                receipt_id,
                quantity,
                description,
                sku,
                unit_price,
                total_price,
                discount,
                item_metadata
            FROM receipt_items
            WHERE receipt_id = :receipt_id
            ORDER BY id;
        """
        return await self._db_manager.execute_sql_query_fetch_all(
            sql, {"receipt_id": receipt_id}
        )

    async def delete_by_receipt_id(self, receipt_id: int) -> None:
        sql = """
            DELETE FROM receipt_items
            WHERE receipt_id = :receipt_id;
        """
        await self._db_manager.execute_statement(sql, {"receipt_id": receipt_id})
