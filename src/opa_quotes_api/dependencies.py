"""Dependency injection for FastAPI."""
from typing import AsyncGenerator

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from opa_quotes_api.config import get_settings
from opa_quotes_api.database import AsyncSessionLocal
from opa_quotes_api.services.cache_service import CacheService
from opa_quotes_api.repository.quote_repository import QuoteRepository
from opa_quotes_api.services.quote_service import QuoteService
from opa_quotes_api.logging_setup import get_logger

logger = get_logger(__name__)
settings = get_settings()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for database session.
    
    Yields:
        AsyncSession for database operations
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_redis() -> AsyncGenerator[redis.Redis, None]:
    """
    Dependency for Redis client.
    
    Yields:
        Redis client instance
    """
    client = redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=False
    )
    try:
        yield client
    finally:
        await client.close()


async def get_cache_service(
    redis_client: redis.Redis = None
) -> CacheService:
    """
    Dependency for cache service.
    
    Args:
        redis_client: Optional Redis client (will create if not provided)
        
    Returns:
        CacheService instance
    """
    if redis_client is None:
        redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=False
        )
    
    return CacheService(redis_client)


async def get_quote_repository(
    db: AsyncSession = None
) -> QuoteRepository:
    """
    Dependency for quote repository.
    
    Args:
        db: Optional database session (will create if not provided)
        
    Returns:
        QuoteRepository instance
    """
    if db is None:
        async with AsyncSessionLocal() as session:
            return QuoteRepository(session)
    
    return QuoteRepository(db)


async def get_quote_service() -> AsyncGenerator[QuoteService, None]:
    """
    Dependency for quote service.
    
    Yields:
        QuoteService instance with cache and repository
    """
    # Create Redis client
    redis_client = redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=False
    )
    
    # Create database session
    async with AsyncSessionLocal() as db_session:
        try:
            # Create dependencies
            cache = CacheService(redis_client)
            repository = QuoteRepository(db_session)
            service = QuoteService(cache, repository)
            
            yield service
            
        finally:
            await redis_client.aclose()
            await db_session.close()
