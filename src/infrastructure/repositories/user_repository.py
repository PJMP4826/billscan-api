from typing import Any

from src.domain.entities.authenticated_user import AuthenticatedUser
from src.domain.ports.repositories.user_repository_port import (
    UserRepositoryPort,
)
from src.infrastructure.database.sql.sql_database_connection_manager import (
    SQLDatabaseConnectionManager,
)


class UserRepository(UserRepositoryPort):
    """Repositorio para la tabla `users`.

    La tabla es un espejo local de los usuarios creados en el proveedor de
    Auth, por lo que las escrituras reciben la entidad `AuthenticatedUser` y
    las lecturas devuelven `dict[str, Any]` (incluyen `created_at`, que no
    forma parte de la entidad).
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
        await self._db_manager.execute_statement(sql, {"id": user_id, "email": email})

    async def insert_if_new(self, user: AuthenticatedUser) -> bool:
        """Inserta el usuario solo si no existe.

        Idempotente ante peticiones concurrentes: `ON CONFLICT DO NOTHING`
        cubre tanto la PK (`id`) como el UNIQUE de `email`. Devuelve `True`
        si la fila se creó en esta llamada.

        Nota: el manager no expone `rowcount`, así que se usa `RETURNING id`
        y se lee el primer valor de la primera fila.
        """
        sql = """
            INSERT INTO users (id, email)
            VALUES (:id, :email)
            ON CONFLICT DO NOTHING
            RETURNING id;
        """
        created_id = await self._db_manager.execute_sql_query_fetch_one(
            sql, {"id": user.user_id.value, "email": user.email}
        )
        return created_id is not None

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
