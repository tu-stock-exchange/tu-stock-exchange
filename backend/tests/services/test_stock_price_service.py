import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.stock_price import CACHE_TTL, FINNHUB_URL, get_current_price


def run(coro):
    return asyncio.run(coro)


def make_redis(cached_value=None, get_exc=None, setex_exc=None):
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=cached_value, side_effect=get_exc)
    redis.setex = AsyncMock(side_effect=setex_exc)
    return redis


def make_httpx_mock(price_value=None, raise_exc=None):
    """Return a mock httpx module whose AsyncClient context manager yields a client."""
    response = MagicMock()
    response.json.return_value = {"c": price_value} if price_value is not None else {}

    client = AsyncMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    if raise_exc:
        client.get = AsyncMock(side_effect=raise_exc)
    else:
        client.get = AsyncMock(return_value=response)

    mock_httpx = MagicMock()
    mock_httpx.AsyncClient.return_value = client
    return mock_httpx


# ---------------------------------------------------------------------------
# Cache hit
# ---------------------------------------------------------------------------

class TestCacheHit:

    def test_returns_float_from_cache(self):
        redis = make_redis(cached_value="150.0")
        with patch("app.services.stock_price.get_redis", new=AsyncMock(return_value=redis)):
            result = run(get_current_price("AAPL"))
        assert result == 150.0

    def test_cache_value_converted_to_float(self):
        redis = make_redis(cached_value="99.99")
        with patch("app.services.stock_price.get_redis", new=AsyncMock(return_value=redis)):
            result = run(get_current_price("TSLA"))
        assert isinstance(result, float)
        assert result == 99.99

    def test_ticker_uppercased_before_cache_lookup(self):
        redis = make_redis(cached_value="200.0")
        with patch("app.services.stock_price.get_redis", new=AsyncMock(return_value=redis)):
            run(get_current_price("aapl"))
        redis.get.assert_awaited_once_with("price:AAPL")

    def test_api_not_called_on_cache_hit(self):
        redis = make_redis(cached_value="100.0")
        mock_httpx = make_httpx_mock(price_value=999.0)
        with patch("app.services.stock_price.get_redis", new=AsyncMock(return_value=redis)), \
             patch("app.services.stock_price.httpx", mock_httpx, create=True):
            run(get_current_price("AAPL"))
        mock_httpx.AsyncClient.assert_not_called()

    def test_cache_key_format(self):
        redis = make_redis(cached_value="50.0")
        with patch("app.services.stock_price.get_redis", new=AsyncMock(return_value=redis)):
            run(get_current_price("MSFT"))
        redis.get.assert_awaited_once_with("price:MSFT")


# ---------------------------------------------------------------------------
# Cache miss → API call
# ---------------------------------------------------------------------------

class TestApiCall:

    def test_returns_price_from_api(self):
        redis = make_redis(cached_value=None)
        mock_httpx = make_httpx_mock(price_value=250.0)
        with patch("app.services.stock_price.get_redis", new=AsyncMock(return_value=redis)), \
             patch("app.services.stock_price.httpx", mock_httpx, create=True):
            result = run(get_current_price("AAPL"))
        assert result == 250.0

    def test_api_called_with_correct_url_and_ticker(self):
        redis = make_redis(cached_value=None)
        mock_httpx = make_httpx_mock(price_value=100.0)
        with patch("app.services.stock_price.get_redis", new=AsyncMock(return_value=redis)), \
             patch("app.services.stock_price.httpx", mock_httpx, create=True), \
             patch("app.services.stock_price.settings") as mock_settings:
            mock_settings.FINNHUB_API_KEY = "test-key"
            run(get_current_price("GOOG"))
        client = mock_httpx.AsyncClient.return_value
        client.get.assert_awaited_once_with(
            FINNHUB_URL,
            params={"symbol": "GOOG", "token": "test-key"},
        )

    def test_price_cached_after_api_call(self):
        redis = make_redis(cached_value=None)
        mock_httpx = make_httpx_mock(price_value=300.0)
        with patch("app.services.stock_price.get_redis", new=AsyncMock(return_value=redis)), \
             patch("app.services.stock_price.httpx", mock_httpx, create=True):
            run(get_current_price("AMZN"))
        redis.setex.assert_awaited_once_with("price:AMZN", CACHE_TTL, "300.0")

    def test_price_not_cached_when_api_returns_zero(self):
        redis = make_redis(cached_value=None)
        mock_httpx = make_httpx_mock(price_value=0)
        with patch("app.services.stock_price.get_redis", new=AsyncMock(return_value=redis)), \
             patch("app.services.stock_price.httpx", mock_httpx, create=True):
            run(get_current_price("AAPL"))
        redis.setex.assert_not_awaited()

    def test_returns_none_when_api_price_is_zero(self):
        redis = make_redis(cached_value=None)
        mock_httpx = make_httpx_mock(price_value=0)
        with patch("app.services.stock_price.get_redis", new=AsyncMock(return_value=redis)), \
             patch("app.services.stock_price.httpx", mock_httpx, create=True):
            result = run(get_current_price("AAPL"))
        assert result is None

    def test_returns_none_when_api_price_is_negative(self):
        redis = make_redis(cached_value=None)
        mock_httpx = make_httpx_mock(price_value=-5.0)
        with patch("app.services.stock_price.get_redis", new=AsyncMock(return_value=redis)), \
             patch("app.services.stock_price.httpx", mock_httpx, create=True):
            result = run(get_current_price("AAPL"))
        assert result is None

    def test_returns_none_when_c_field_missing(self):
        redis = make_redis(cached_value=None)
        mock_httpx = make_httpx_mock()  # json returns {}
        with patch("app.services.stock_price.get_redis", new=AsyncMock(return_value=redis)), \
             patch("app.services.stock_price.httpx", mock_httpx, create=True):
            result = run(get_current_price("AAPL"))
        assert result is None

    def test_returns_none_when_api_raises(self):
        redis = make_redis(cached_value=None)
        mock_httpx = make_httpx_mock(raise_exc=Exception("network error"))
        with patch("app.services.stock_price.get_redis", new=AsyncMock(return_value=redis)), \
             patch("app.services.stock_price.httpx", mock_httpx, create=True):
            result = run(get_current_price("AAPL"))
        assert result is None

    def test_returns_price_even_when_setex_fails(self):
        redis = make_redis(cached_value=None, setex_exc=Exception("redis write error"))
        mock_httpx = make_httpx_mock(price_value=175.0)
        with patch("app.services.stock_price.get_redis", new=AsyncMock(return_value=redis)), \
             patch("app.services.stock_price.httpx", mock_httpx, create=True):
            result = run(get_current_price("AAPL"))
        assert result == 175.0


# ---------------------------------------------------------------------------
# Redis failure fallback
# ---------------------------------------------------------------------------

class TestRedisFallback:

    def test_falls_through_to_api_when_redis_get_raises(self):
        redis = make_redis(get_exc=Exception("redis unavailable"))
        mock_httpx = make_httpx_mock(price_value=120.0)
        with patch("app.services.stock_price.get_redis", new=AsyncMock(return_value=redis)), \
             patch("app.services.stock_price.httpx", mock_httpx, create=True):
            result = run(get_current_price("AAPL"))
        assert result == 120.0

    def test_returns_none_when_both_redis_and_api_fail(self):
        redis = make_redis(get_exc=Exception("redis down"))
        mock_httpx = make_httpx_mock(raise_exc=Exception("api down"))
        with patch("app.services.stock_price.get_redis", new=AsyncMock(return_value=redis)), \
             patch("app.services.stock_price.httpx", mock_httpx, create=True):
            result = run(get_current_price("AAPL"))
        assert result is None
