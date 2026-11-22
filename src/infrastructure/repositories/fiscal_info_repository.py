from typing import Any

from sqlalchemy import text

from src.infrastructure.database.sql.sql_database_connection_manager import (
    SQLDatabaseConnectionManager,
)
from src.domain.errors.fiscal_info_error import FiscalInfoNotFoundError
from src.shared.errors.infrastructure_exceptions import PostgresDBException
from src.domain.ports.repositories.fiscal_info_repository_port import (
    FiscalInfoRepositoryPort,
    RegimenRecord,
)


class FiscalInfoRepository(FiscalInfoRepositoryPort):
    """Repositorio para las tablas `fiscal_info` y `regimenes`.

    Trabaja directamente con diccionarios para lectura y maneja el upsert de
    los datos fiscales (un registro por usuario) junto con el reemplazo de sus
    regímenes.
    """

    def __init__(self, manager: SQLDatabaseConnectionManager) -> None:
        self._db_manager = manager

    async def upsert_fiscal_info(
        self,
        user_id: str,
        rfc: str,
        razon_social: str,
        email: str,
        cp: str,
        address: str | None,
        use_cfdi_code_default: str,
    ) -> tuple[int, bool]:
        """Crea o actualiza la información fiscal base del usuario.

        Al existir ``UNIQUE(user_id)``, un POST repetido actualiza la misma
        fila en lugar de agregar otra. Devuelve ``(id, created)``.
        """
        sql = """
            INSERT INTO fiscal_info (
                user_id, 
                rfc, 
                razon_social, 
                email, 
                cp, 
                address,
                use_cfdi_default
            )
            VALUES (
                :user_id, 
                :rfc, 
                :razon_social, 
                :email, 
                :cp, 
                :address,
                :use_cfdi_default
            )
            ON CONFLICT (user_id) DO UPDATE SET
                rfc = EXCLUDED.rfc,
                razon_social = EXCLUDED.razon_social,
                email = EXCLUDED.email,
                cp = EXCLUDED.cp,
                address = EXCLUDED.address,
                use_cfdi_default = EXCLUDED.use_cfdi_default
            RETURNING id, (xmax = 0) AS created;
        """

        row = await self._db_manager.execute_sql_query_fetch_first(
            sql,
            {
                "user_id": user_id,
                "rfc": rfc,
                "razon_social": razon_social,
                "email": email,
                "cp": cp,
                "address": address,
                "use_cfdi_default": use_cfdi_code_default,
            },
        )

        if not row:
            raise PostgresDBException("Error al registrar la informacion fiscal en BD")
        return int(row["id"]), bool(row["created"])

    async def replace_regimens(
        self,
        fiscal_info_id: int,
        regimens: list[RegimenRecord],
    ) -> None:
        """Reemplaza atómicamente los regímenes del usuario.

        Cada elemento es ``(regimen_code, regimen_description, fecha_alta)``.
        """
        sql = """
            INSERT INTO regimenes (
                fiscal_info, 
                regimen_code, 
                regimen_description, 
                fecha_alta
            )
            VALUES (
                :fiscal_info_id, 
                :regimen_code, 
                :regimen_description, 
                :fecha_alta
            );
        """

        rows = [
            {
                "fiscal_info_id": fiscal_info_id,
                "regimen_code": regimen_code,
                "regimen_description": regimen_description,
                "fecha_alta": fecha_alta,
            }
            for regimen_code, regimen_description, fecha_alta in regimens
        ]

        async with self._db_manager.transaction() as conn:
            await conn.execute(
                text("DELETE FROM regimenes WHERE fiscal_info = :fiscal_info_id;"),
                {"fiscal_info_id": fiscal_info_id},
            )
            if rows:
                await conn.execute(text(sql), rows)

    async def get_latest_by_user_id(self, user_id: str) -> dict[str, Any]:
        """Obtiene la información fiscal del usuario junto con su ÚLTIMO régimen.

        Utiliza LEFT JOIN por si la info fiscal aún no tiene un régimen asociado,
        y ordena por `fecha_alta DESC` para traer solo el vigente.
        """
        sql = """
            SELECT 
                fi.id AS fiscal_info_id,
                fi.user_id,
                fi.rfc,
                fi.razon_social,
                fi.email AS fiscal_email,
                fi.cp,
                fi.address,
                fi.use_cfdi_default,
                r.id AS regimen_id,
                r.regimen_code,
                r.regimen_description,
                r.fecha_alta
            FROM fiscal_info fi
            LEFT JOIN regimenes r ON r.fiscal_info = fi.id
            WHERE fi.user_id = :user_id
            ORDER BY r.fecha_alta DESC NULLS LAST
            LIMIT 1;
        """
        result = await self._db_manager.execute_sql_query_fetch_first(
            sql, {"user_id": user_id}
        )

        if not result:
            raise FiscalInfoNotFoundError()

        return result

    async def get_rfc_by_user_id(self, user_id: str) -> str:
        """Obtiene el RFC cifrado de la información fiscal del usuario."""
        sql = """
            SELECT rfc
            FROM fiscal_info
            WHERE user_id = :user_id
            LIMIT 1;
        """
        result = await self._db_manager.execute_sql_query_fetch_one(
            sql, {"user_id": user_id}
        )

        if not result:
            raise FiscalInfoNotFoundError()

        return str(result)

    async def get_regimens_by_user_id(self, user_id: str) -> list[dict[str, Any]]:
        """Obtiene TODOS los regímenes del usuario para que elija con cuál facturar.

        Se deduplica por ``regimen_code`` quedándose con el ``fecha_alta`` más
        reciente de cada código.
        """
        sql = """
            WITH distinct_regimens AS (
                SELECT DISTINCT ON (r.regimen_code)
                    r.regimen_code AS code,
                    r.regimen_description AS description,
                    r.fecha_alta
                FROM regimenes r
                JOIN fiscal_info fi ON fi.id = r.fiscal_info
                WHERE fi.user_id = :user_id
                ORDER BY r.regimen_code, r.fecha_alta DESC
            )
            SELECT code, description, fecha_alta
            FROM distinct_regimens
            ORDER BY fecha_alta DESC NULLS LAST, code;
        """
        return await self._db_manager.execute_sql_query_fetch_all(
            sql, {"user_id": user_id}
        )

    async def has_fiscal_info(self, user_id: str) -> bool:
        """Verifica de forma optimizada si un usuario ya tiene información fiscal."""
        sql = """
            SELECT 1 
            FROM fiscal_info 
            WHERE user_id = :user_id 
            LIMIT 1;
        """
        row = await self._db_manager.execute_sql_query_fetch_one(
            sql, {"user_id": user_id}
        )
        return row is not None
