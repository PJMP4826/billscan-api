import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.engine.base import Connection

from alembic import context

# ---------------------------------------------------------------------------
# Load app Settings — Alembic runs from the project root so the import works
# as long as PYTHONPATH includes the project root (see Makefile targets below)
# ---------------------------------------------------------------------------
from src.config.settings import settings

# ---------------------------------------------------------------------------
# Alembic Config object — gives access to values in alembic.ini
# ---------------------------------------------------------------------------
config = context.config

# Set up logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------------------------
# Build URLs
# Alembic's own runner needs a SYNC url.
# We derive it from settings.database_url by swapping the driver.
# settings.database_url  → "postgresql+asyncpg://..."
# sync_url               → "postgresql+psycopg2://..."   (for offline mode)
# async_url              → "postgresql+asyncpg://..."    (for online mode)
# ---------------------------------------------------------------------------
async_url: str = settings.database_url  # already has +asyncpg
sync_url: str = async_url.replace("postgresql+asyncpg", "postgresql+psycopg2", 1)

# No target_metadata — we use pure SQL migrations, not autogenerate
target_metadata = None


# ---------------------------------------------------------------------------
# OFFLINE mode — emits SQL to stdout instead of running against the DB
# Useful for generating migration scripts to review before applying.
# Run: alembic upgrade head --sql
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    context.configure(
        url=sync_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# ONLINE mode — connects to the DB and runs migrations directly
# ---------------------------------------------------------------------------
def do_run_migrations(connection: Connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine = create_async_engine(
        async_url,
        poolclass=pool.NullPool,  # no pooling for migration runs
    )

    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await engine.dispose()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
