from contextlib import asynccontextmanager
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from app.core.config import settings

_pool = None 
@asynccontextmanager
async def get_postgres_checkpointer():
    """
    Yields an AsyncPostgresSaver tied to the Supabase connection pool.
    Automatically sets up the necessary LangGraph checkpoint tables on first run.
    """

    global _pool
    if _pool is None:
        _pool = AsyncConnectionPool(
        conninfo=settings.DATABASE_URL,
        max_size=10,
        kwargs={"autocommit": True, "prepare_threshold": 0},
        open=False
        )
        await _pool.open()

    checkpointer = AsyncPostgresSaver(_pool)
    # This automatically creates the `checkpoints` and `checkpoint_writes` tables in Supabase
    await checkpointer.setup()
    try:
        yield checkpointer
    finally:
        # Context manager ensures we clean up references cleanly
        pass