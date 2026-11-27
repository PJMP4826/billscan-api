from src.domain.enums.push_platform import PushPlatform
from src.domain.ports.repositories.push_token_repository_port import (
    PushTokenRepositoryPort,
)
from src.infrastructure.database.sql.sql_database_connection_manager import (
    SQLDatabaseConnectionManager,
)


class PushTokenRepository(PushTokenRepositoryPort):
    """Repositorio para `push_tokens`.

    `upsert` usa `ON CONFLICT (token)` para que un mismo dispositivo cambie de
    usuario sin violar el UNIQUE global. `delete_by_token_and_user_id` nunca
    falla si la fila no existe o pertenece a otro usuario.
    """

    def __init__(self, manager: SQLDatabaseConnectionManager) -> None:
        self._db_manager = manager

    async def upsert(
        self, user_id: str, token: str, platform: PushPlatform
    ) -> None:
        sql = """
            INSERT INTO push_tokens (user_id, token, platform)
            VALUES (:user_id, :token, :platform)
            ON CONFLICT (token) DO UPDATE
            SET user_id = EXCLUDED.user_id,
                platform = EXCLUDED.platform,
                updated_at = CURRENT_TIMESTAMP;
        """
        await self._db_manager.execute_statement(
            sql,
            {
                "user_id": user_id,
                "token": token,
                "platform": platform.value,
            },
        )

    async def delete_by_token_and_user_id(self, token: str, user_id: str) -> None:
        sql = """
            DELETE FROM push_tokens
            WHERE token = :token
              AND user_id = :user_id;
        """
        await self._db_manager.execute_statement(
            sql, {"token": token, "user_id": user_id}
        )

    async def find_tokens_by_user_id(self, user_id: str) -> list[str]:
        sql = """
            SELECT token
            FROM push_tokens
            WHERE user_id = :user_id;
        """
        rows = await self._db_manager.execute_sql_query_fetch_all(
            sql, {"user_id": user_id}
        )
        return [str(row["token"]) for row in rows]
