from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from motor.motor_asyncio import AsyncIOMotorClient
from aioredis import Redis
import redis.asyncio as redis
import structlog

from app.core.config import settings


logger = structlog.get_logger(__name__)

# PostgreSQL Async Engine with Connection Pooling
postgres_engine = create_async_engine(
    settings.postgres_url,
    pool_size=settings.postgres_pool_size,
    max_overflow=settings.postgres_max_overflow,
    echo=settings.debug,
    future=True,
)

# PostgreSQL Session Factory
PostgresSessionLocal = async_sessionmaker(
    bind=postgres_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# MongoDB Async Client
mongo_client: AsyncIOMotorClient = None

# Redis Async Client
redis_client: Redis = None


async def get_postgres_session() -> AsyncSession:
    """Get async PostgreSQL session from connection pool."""
    async with PostgresSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise


async def get_mongodb():
    """Get MongoDB database instance."""
    global mongo_client
    if mongo_client is None:
        mongo_client = AsyncIOMotorClient(settings.mongodb_url)

    return mongo_client[settings.mongodb_db_name]


async def get_redis():
    """Get Redis client for caching."""
    global redis_client
    if redis_client is None:
        redis_client = Redis.from_url(settings.redis_url)

    return redis_client


async def init_databases():
    """Initialize all database connections."""
    global redis_client

    try:
        # Test PostgreSQL connection
        async with postgres_engine.begin() as conn:
            await conn.execute("SELECT 1")
        logger.info("PostgreSQL connected successfully")

        # Test MongoDB connection
        db = await get_mongodb()
        await db.command("ping")
        logger.info("MongoDB connected successfully")

        # Test Redis connection
        redis_client = await get_redis()
        await redis_client.ping()
        logger.info("Redis connected successfully")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


async def close_databases():
    """Close all database connections."""
    global mongo_client, redis_client

    if mongo_client:
        mongo_client.close()
        logger.info("MongoDB connection closed")

    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")

    await postgres_engine.dispose()
    logger.info("PostgreSQL connections closed")


# Database dependency for FastAPI
async def get_postgres_db():
    """Dependency to get PostgreSQL session."""
    async for session in get_postgres_session():
        yield session


async def get_mongo_db():
    """Dependency to get MongoDB database."""
    db = await get_mongodb()
    yield db


async def get_redis_cache():
    """Dependency to get Redis cache."""
    redis = await get_redis()
    yield redis
