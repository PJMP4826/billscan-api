from typing import Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine

from src.config.logger import logger
from src.config.settings import settings
from src.shared.errors.infrastructure_exceptions import (
    InfrastructureException,
    PostgresDBException,
)


class SQLDatabaseConnectionManager:
    def __init__(self) -> None:
        self.settings = settings
        self._engine: AsyncEngine | None = None

    @property
    def engine(self) -> AsyncEngine:
        """Retorna el engine asíncrono de SQLAlchemy (Singleton)."""
        if self._engine is None:
            self._engine = self._create_engine()
        return self._engine

    def _create_engine(self) -> AsyncEngine:
        try:
            connection_url = self.settings.database_url
            logger.info(
                f"Iniciando conexion ASYNC a PostgreSQL: {self.settings.db_name}"
            )

            return create_async_engine(
                connection_url,
                echo=False,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
            )
        except Exception as e:
            logger.error(f"Error al configurar el engine asíncrono: {str(e)}")
            raise InfrastructureException(
                "Error en la configuración del motor de base de datos asíncrono",
                details={"error": str(e)},
            )

    async def execute_sql_query_fetch_all(
        self, sql: str, params: dict[str, Any] = {}
    ) -> list[dict[str, Any]]:
        """Ejecuta consulta asíncrona y devuelve todas las filas."""
        async with self.engine.connect() as conn:
            trans = await conn.begin()
            try:
                result = await conn.execute(text(sql), params)
                await trans.commit()
                return [dict(row) for row in result.mappings().all()]
            except Exception as e:
                await trans.rollback()
                logger.error(f"Error en execute_sql_query_fetch_all (Async): {str(e)}")
                raise PostgresDBException(
                    message="Error al ejecutar consulta async de múltiples filas"
                )

    async def execute_sql_query_fetch_one(
        self, sql: str, params: dict[str, Any] = {}
    ) -> Any | None:
        """Ejecuta consulta y devuelve el primer valor de la primera columna."""
        async with self.engine.connect() as conn:
            trans = await conn.begin()
            try:
                result = await conn.execute(text(sql), params)
                await trans.commit()
                row = result.fetchone()
                return row[0] if row else None
            except Exception as e:
                await trans.rollback()
                logger.error(f"Error en execute_sql_query_fetch_one (Async): {str(e)}")
                raise PostgresDBException(
                    message="Error al ejecutar consulta async de valor único"
                )

    async def execute_sql_query_fetch_first(
        self, sql: str, params: dict[str, Any] = {}
    ) -> dict[str, Any] | None:
        """Ejecuta consulta y devuelve la primera fila completa como diccionario."""
        async with self.engine.connect() as conn:
            trans = await conn.begin()
            try:
                result = await conn.execute(text(sql), params)
                await trans.commit()
                row = result.mappings().first()
                return dict(row) if row else None
            except Exception as e:
                await trans.rollback()
                logger.error(
                    f"Error en execute_sql_query_fetch_first (Async): {str(e)}"
                )
                raise PostgresDBException(
                    message="Error al ejecutar consulta async de fila única"
                )

    async def execute_statement(self, sql: str, params: dict[str, Any] = {}) -> None:
        """Ejecuta statements (INSERT, UPDATE, DELETE) y hace commit."""
        async with self.engine.connect() as conn:
            trans = await conn.begin()
            try:
                await conn.execute(text(sql), params)
                await trans.commit()
            except Exception as e:
                await trans.rollback()
                logger.error(f"Error en execute_statement (Async): {str(e)}")
                raise PostgresDBException(
                    message="Error al ejecutar operación de escritura"
                )

    async def test_connection(self) -> dict[str, Any]:
        """Test de salud asíncrono."""
        try:
            async with self.engine.connect() as conn:
                result = await conn.execute(text("SELECT version();"))
                row = result.fetchone()
                version = str(row[0]) if row else "Desconocida"

                return {
                    "status": "success",
                    "message": f"Conexión ASYNC activa a: {self.settings.db_name}",
                    "version": version,
                }
        except Exception as e:
            logger.error(f"Test de conexión async fallido: {e}")
            return {
                "status": "error",
                "message": f"Error al conectar asíncronamente: {str(e)}",
            }

    async def close(self):
        """Cierra el pool de conexiones de forma asíncrona."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            logger.info("Pool de conexiones asíncronas de PostgreSQL liberado")

database_connection_manager = SQLDatabaseConnectionManager()