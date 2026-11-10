import asyncio
from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine
from app.config import get_settings
from app.db import Base
import app.models  # noqa: F401

target_metadata = Base.metadata


def _run(conn):
    context.configure(connection=conn, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def main():
    engine = create_async_engine(get_settings().database_url)
    async with engine.connect() as c:
        await c.run_sync(_run)
    await engine.dispose()


asyncio.run(main())
