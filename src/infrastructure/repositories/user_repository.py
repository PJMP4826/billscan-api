from typing import Any

from src.infrastructure.database.sql.sql_database_connection_manager import (
    SQLDatabaseConnectionManager,
)


class UserRepository:
    """Repositorio para la tabla `users`.

    No existe una entidad de dominio `User` (la tabla solo refleja usuarios
    creados por el proveedor de Auth), por lo que este repositorio trabaja
    directamente con `dict[str, Any]` en lugar de mapear a/desde un VO.
    """

    def __init__(self, manager: SQLDatabaseConnectionManager) -> None:
        self._db_manager = manager

    async def insert(self, user_id: str, email: str) -> None:
        """Inserta un usuario nuevo. Lanza si el id o el email ya existen
        (PRIMARY KEY / UNIQUE constraint del esquema)."""
        sql = """
            INSERT INTO users (id, email)
            VALUES (:id, :email);
        """
        await self._db_manager.execute_statement(
            sql, {"id": user_id, "email": email}
        )

    async def find_by_id(self, user_id: str) -> dict[str, Any] | None:
        sql = """
            SELECT id, email, created_at
            FROM users
            WHERE id = :id;
        """
        return await self._db_manager.execute_sql_query_fetch_first(
            sql, {"id": user_id}
        )

    async def find_by_email(self, email: str) -> dict[str, Any] | None:
        sql = """
            SELECT id, email, created_at
            FROM users
            WHERE email = :email;
        """
        return await self._db_manager.execute_sql_query_fetch_first(
            sql, {"email": email}
        )

    async def exists(self, user_id: str) -> bool:
        sql = """
            SELECT 1
            FROM users
            WHERE id = :id;
        """
        row = await self._db_manager.execute_sql_query_fetch_one(sql, {"id": user_id})
        return row is not None
