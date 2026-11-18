import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.config import DATABASE_URL, DB_SSLMODE

logger = logging.getLogger('app')

engine_kwargs: dict = {
    'echo': False,
    'pool_pre_ping': True,
}

if DATABASE_URL.startswith('postgresql+asyncpg://'):
    engine_kwargs['connect_args'] = {
        'ssl': 'require' if DB_SSLMODE in {'require', 'verify-full', 'verify-ca'} else 'prefer'
    }

engine = create_async_engine(DATABASE_URL, **engine_kwargs)

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
        if DATABASE_URL.startswith('postgresql'):
            version = (await conn.execute(text('SELECT version()'))).scalar_one()
            logger.info('PostgreSQL connection active: %s', version.split(',')[0])
