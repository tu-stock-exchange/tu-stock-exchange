import redis.asyncio as redis
from app.core.config import settings

_redis_client = None

async def init_redis():
    """Call this during FastAPI startup."""
    global _redis_client
    if _redis_client is None:
        _redis_client = await redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        # Test connection
        await _redis_client.ping()

async def get_redis():
    """Return the Redis client, initialising it if necessary."""
    global _redis_client
    if _redis_client is None:
        await init_redis()
    return _redis_client

async def close_redis():
    """Call this during FastAPI shutdown."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None