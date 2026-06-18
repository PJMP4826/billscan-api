from typing import Any

from src.domain.value_objects.merchant_data import MerchantData
from src.infrastructure.database.sql.sql_database_connection_manager import (
    SQLDatabaseConnectionManager,
)
from src.shared.errors.infrastructure_exceptions import PostgresDBException
from src.domain.ports.repositories.merchant_repository_port import (
    MerchantRepositoryPort,
)


class MerchantRepository(MerchantRepositoryPort):
    """Repositorio para la tabla `merchants`.

    Mapea hacia/desde el value object `MerchantData`. La tabla tiene una
    restricción UNIQUE compuesta (tax_id, branch_id), por lo que se ofrece
    `find_or_create` para evitar duplicados cuando varias sucursales
    comparten RFC.
    """

    def __init__(self, manager: SQLDatabaseConnectionManager) -> None:
        self._db_manager = manager

    @staticmethod
    def _row_to_vo(row: dict[str, Any]) -> MerchantData:
        return MerchantData(
            name=row["name"],
            tax_id=row["tax_id"],
            address=row["address"],
            branch_id=row["branch_id"],
            phone=row["phone"],
        )

    async def insert(self, merchant: MerchantData) -> int:
        """Inserta un comercio y devuelve el `id` (BIGSERIAL) generado."""
        sql = """
            INSERT INTO merchants (name, tax_id, address, branch_id, phone)
            VALUES (:name, :tax_id, :address, :branch_id, :phone)
            RETURNING id;
        """
        merchant_id = await self._db_manager.execute_sql_query_fetch_one(
            sql,
            {
                "name": merchant.name,
                "tax_id": merchant.tax_id,
                "address": merchant.address,
                "branch_id": merchant.branch_id,
                "phone": merchant.phone,
            },
        )

        if merchant_id is None:
            raise PostgresDBException("No se pudo insertar el comercio, el ID es nulo.")
        return int(merchant_id)

    async def find_by_id(self, merchant_id: int) -> MerchantData | None:
        sql = """
            SELECT id, name, tax_id, address, branch_id, phone
            FROM merchants
            WHERE id = :id;
        """
        row = await self._db_manager.execute_sql_query_fetch_first(
            sql, {"id": merchant_id}
        )
        return self._row_to_vo(row) if row else None

    async def find_by_tax_id_and_branch(
        self, tax_id: str | None, branch_id: str | None
    ) -> dict[str, Any] | None:
        """Busca por la llave única compuesta (tax_id, branch_id).

        Devuelve el dict con `id` incluido (útil para FK en `receipts`),
        no solo el VO.
        """
        sql = """
            SELECT id, name, tax_id, address, branch_id, phone
            FROM merchants
            WHERE tax_id = :tax_id AND branch_id = :branch_id;
        """
        return await self._db_manager.execute_sql_query_fetch_first(
            sql, {"tax_id": tax_id, "branch_id": branch_id}
        )

    async def find_or_create(self, merchant: MerchantData) -> int:
        """Busca un comercio por (tax_id, branch_id); si no existe lo inserta.

        Devuelve el `id` (BIGSERIAL) en cualquier caso. Si tax_id y
        branch_id son ambos None, siempre inserta (no hay llave única que
        verificar de forma significativa).
        """
        if merchant.tax_id is not None or merchant.branch_id is not None:
            existing = await self.find_by_tax_id_and_branch(
                merchant.tax_id, merchant.branch_id
            )
            if existing is not None:
                return int(existing["id"])

        return await self.insert(merchant)
