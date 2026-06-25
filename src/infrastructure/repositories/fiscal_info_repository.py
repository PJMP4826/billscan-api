from datetime import date
from typing import Any

from src.infrastructure.database.sql.sql_database_connection_manager import (
    SQLDatabaseConnectionManager,
)
from src.shared.errors.infrastructure_exceptions import PostgresDBException
from src.domain.ports.repositories.fiscal_info_repository_port import (
    FiscalInfoRepositoryPort,
)


class FiscalInfoRepository(FiscalInfoRepositoryPort):
    """Repositorio para las tablas `fiscal_info` y `regimenes`.

    Trabaja directamente con diccionarios para lectura y maneja la
    inserción de datos fiscales y su historial de regímenes.
    """

    def __init__(self, manager: SQLDatabaseConnectionManager) -> None:
        self._db_manager = manager

    async def insert_fiscal_info(
        self,
        user_id: str,
        rfc: str,
        razon_social: str,
        email: str,
        cp: str,
        address: str | None,
        use_cfdi_code_default: str
    ) -> int:
        """Inserta la información fiscal base del usuario y devuelve su `id` (BIGSERIAL)."""
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
            RETURNING id;
        """

        row = await self._db_manager.execute_sql_query_fetch_one(
            sql,
            {
                "user_id": user_id,
                "rfc": rfc,
                "razon_social": razon_social,
                "email": email,
                "cp": cp,
                "address": address,
                "use_cfdi_default": use_cfdi_code_default
            },
        )

        if not row:
            raise PostgresDBException("Error al registrar la informacion fiscal en BD")
        return int(row)

    async def add_regimen(
        self,
        fiscal_info_id: int,
        regimen_code: str,
        regimen_description: str,
        fecha_alta: date,
    ) -> int:
        """Agrega un nuevo régimen fiscal al historial del usuario.

        Al mantener un historial, "actualizar" el régimen consiste en insertar
        uno nuevo. Las consultas de lectura tomarán el más reciente.
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
            )
            RETURNING id;
        """

        row = await self._db_manager.execute_sql_query_fetch_one(
            sql,
            {
                "fiscal_info_id": fiscal_info_id,
                "regimen_code": regimen_code,
                "regimen_description": regimen_description,
                "fecha_alta": fecha_alta,
            },
        )

        if not row:
            raise PostgresDBException("Error al guardar regimen fiscal")
        return int(row)

    async def get_latest_by_user_id(self, user_id: str) -> dict[str, Any] | None:
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
        return await self._db_manager.execute_sql_query_fetch_first(
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

    async def update_fiscal_info_details(
        self,
        fiscal_info_id: int,
        rfc: str,
        razon_social: str,
        email: str,
        cp: str,
        address: str | None,
        use_cfdi_code_default: str
    ) -> None:
        """(Opcional) Método para actualizar los datos estáticos de la información fiscal."""
        sql = """
            UPDATE fiscal_info
            SET rfc = :rfc,
                razon_social = :razon_social,
                email = :email,
                cp = :cp,
                address = :address
                use_cfdi_default = :use_cfdi_default
            WHERE id = :id;
        """
        await self._db_manager.execute_statement(
            sql,
            {
                "id": fiscal_info_id,
                "rfc": rfc,
                "razon_social": razon_social,
                "email": email,
                "cp": cp,
                "address": address,
                "use_cfdi_default": use_cfdi_code_default
            },
        )
