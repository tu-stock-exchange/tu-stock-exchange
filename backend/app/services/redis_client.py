from redis import Redis
from app.core.config import settings

redis_client = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5
)

def check_connection():
    """Verify Redis connection is working"""
    try:
        redis_client.ping()
        return True
    except Exception as e:
        print(f"Redis connection failed: {str(e)}")
        return False

if not check_connection():
    print("Warning: Redis not available. Caching will be disabled.")