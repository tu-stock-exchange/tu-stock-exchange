from app.services.redis_client import get_redis
from app.core.config import settings
import httpx

CACHE_TTL = 3600  # 1 hour
FINNHUB_URL = "https://finnhub.io/api/v1/quote"

async def get_current_price(ticker: str) -> float | None:
    """Fetch the current price for a ticker from Redis cache, falling back to the Finnhub API."""
    ticker = ticker.upper()
    cache_key = f"price:{ticker}"

    redis = await get_redis()
    try:
        cached = await redis.get(cache_key)
        if cached:
            return float(cached)
    except Exception:
        pass

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(
                FINNHUB_URL,
                params={"symbol": ticker, "token": settings.FINNHUB_API_KEY},
            )
        data = response.json()
        price = data.get("c")
        if not price or float(price) <= 0:
            return None
        price = float(price)
        try:
            await redis.setex(cache_key, CACHE_TTL, str(price))
        except Exception:
            pass
        return price
    except NameError as e:
        print(f"NameError inside try: {e}")
        return None
    except Exception as e:
        print(f"General error: {e}")
        return None