from src.domain.enums.sat_payment_methods import (
    SatPaymentMethodCode,
    SatPaymentMethodDescription,
)
from src.infrastructure.database.sql.sql_database_connection_manager import (
    SQLDatabaseConnectionManager,
)


class PaymentMethodRepository:
    """Repositorio para la tabla de catálogo `payment_methods`.

    `code` (VARCHAR(10)) es la PRIMARY KEY y corresponde al catálogo
    oficial de formas de pago del SAT. Se asume que `SatPaymentMethodCode`
    y `SatPaymentMethodDescription` son enums de tipo `str` cuyo `.value`
    coincide con `code` y `description` respectivamente.
    """

    def __init__(self, manager: SQLDatabaseConnectionManager) -> None:
        self._db_manager = manager

    async def insert(
        self,
        code: SatPaymentMethodCode,
        description: SatPaymentMethodDescription,
    ) -> None:
        """Inserta un método de pago en el catálogo.

        Pensado para poblar la tabla una sola vez (seed) con el catálogo
        completo del SAT, no para uso transaccional por recibo.
        """
        sql = """
            INSERT INTO payment_methods (code, description)
            VALUES (:code, :description);
        """
        await self._db_manager.execute_statement(
            sql, {"code": code.value, "description": description.value}
        )

    async def find_by_code(self, code: SatPaymentMethodCode) -> dict[str, str] | None:
        sql = """
            SELECT code, description
            FROM payment_methods
            WHERE code = :code;
        """
        return await self._db_manager.execute_sql_query_fetch_first(
            sql, {"code": code.value}
        )

    async def list_all(self) -> list[dict[str, str]]:
        sql = """
            SELECT code, description
            FROM payment_methods
            ORDER BY code;
        """
        return await self._db_manager.execute_sql_query_fetch_all(sql)

    async def exists(self, code: SatPaymentMethodCode) -> bool:
        sql = """
            SELECT 1
            FROM payment_methods
            WHERE code = :code;
        """
        row = await self._db_manager.execute_sql_query_fetch_one(
            sql, {"code": code.value}
        )
        return row is not None
