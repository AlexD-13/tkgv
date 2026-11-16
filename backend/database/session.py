import logging

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.config import DATABASE_URL

logger = logging.getLogger("app")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"timeout": 30},
)

# SQLite per-connection PRAGMAs (foreign keys + busy timeout).
@event.listens_for(engine.sync_engine, "connect")
def _set_sqlite_pragmas(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("PRAGMA busy_timeout = 30000;")
    cursor.close()


AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def init_pragmas_check() -> None:
    async with engine.connect() as conn:
        fk = (await conn.execute(text("PRAGMA foreign_keys;"))).scalar()
        bt = (await conn.execute(text("PRAGMA busy_timeout;"))).scalar()
        logger.info("SQLite PRAGMA foreign_keys=%s busy_timeout=%s", fk, bt)
