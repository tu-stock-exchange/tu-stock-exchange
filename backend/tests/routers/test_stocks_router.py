from unittest.mock import AsyncMock, patch

import pytest

from app.routers.stocks import POPULAR_TICKERS, TICKER_NAMES


# ---------------------------------------------------------------------------
# GET /api/stocks/popular
# ---------------------------------------------------------------------------

class TestGetPopularStocks:

    def test_returns_200(self, client):
        with patch("app.routers.stocks.get_current_price", new=AsyncMock(return_value=150.0)):
            response = client.get("/api/stocks/popular")
        assert response.status_code == 200

    def test_response_contains_stocks_key(self, client):
        with patch("app.routers.stocks.get_current_price", new=AsyncMock(return_value=150.0)):
            data = client.get("/api/stocks/popular").json()
        assert "stocks" in data

    def test_returns_all_tickers_when_all_prices_available(self, client):
        with patch("app.routers.stocks.get_current_price", new=AsyncMock(return_value=100.0)):
            data = client.get("/api/stocks/popular").json()
        assert len(data["stocks"]) == len(POPULAR_TICKERS)

    def test_each_item_has_ticker_name_price(self, client):
        with patch("app.routers.stocks.get_current_price", new=AsyncMock(return_value=100.0)):
            data = client.get("/api/stocks/popular").json()
        for stock in data["stocks"]:
            assert "ticker" in stock
            assert "name" in stock
            assert "price" in stock

    def test_ticker_with_none_price_excluded(self, client):
        async def price_side_effect(ticker):
            return None if ticker == "AAPL" else 100.0

        with patch("app.routers.stocks.get_current_price", side_effect=price_side_effect):
            data = client.get("/api/stocks/popular").json()

        tickers = [s["ticker"] for s in data["stocks"]]
        assert "AAPL" not in tickers
        assert len(data["stocks"]) == len(POPULAR_TICKERS) - 1

    def test_returns_empty_list_when_all_prices_fail(self, client):
        with patch("app.routers.stocks.get_current_price", new=AsyncMock(return_value=None)):
            data = client.get("/api/stocks/popular").json()
        assert data["stocks"] == []

    def test_name_matches_ticker_names_map(self, client):
        with patch("app.routers.stocks.get_current_price", new=AsyncMock(return_value=100.0)):
            data = client.get("/api/stocks/popular").json()
        for stock in data["stocks"]:
            assert stock["name"] == TICKER_NAMES[stock["ticker"]]

    def test_price_value_is_correct(self, client):
        with patch("app.routers.stocks.get_current_price", new=AsyncMock(return_value=250.50)):
            data = client.get("/api/stocks/popular").json()
        for stock in data["stocks"]:
            assert stock["price"] == 250.50


# ---------------------------------------------------------------------------
# GET /api/stocks/search
# ---------------------------------------------------------------------------

class TestSearchStocks:

    def test_empty_query_returns_empty_results(self, client):
        response = client.get("/api/stocks/search?q=")
        assert response.status_code == 200
        assert response.json() == {"results": []}

    def test_missing_query_param_returns_empty_results(self, client):
        response = client.get("/api/stocks/search")
        assert response.status_code == 200
        assert response.json() == {"results": []}

    def test_search_by_exact_ticker(self, client):
        with patch("app.routers.stocks.get_current_price", new=AsyncMock(return_value=150.0)):
            data = client.get("/api/stocks/search?q=AAPL").json()
        tickers = [r["ticker"] for r in data["results"]]
        assert "AAPL" in tickers

    def test_search_by_ticker_substring(self, client):
        with patch("app.routers.stocks.get_current_price", new=AsyncMock(return_value=150.0)):
            data = client.get("/api/stocks/search?q=AAP").json()
        tickers = [r["ticker"] for r in data["results"]]
        assert "AAPL" in tickers

    def test_search_by_company_name(self, client):
        with patch("app.routers.stocks.get_current_price", new=AsyncMock(return_value=150.0)):
            data = client.get("/api/stocks/search?q=apple").json()
        tickers = [r["ticker"] for r in data["results"]]
        assert "AAPL" in tickers

    def test_search_is_case_insensitive(self, client):
        with patch("app.routers.stocks.get_current_price", new=AsyncMock(return_value=150.0)):
            lower = client.get("/api/stocks/search?q=microsoft").json()
            upper = client.get("/api/stocks/search?q=MICROSOFT").json()
        assert lower["results"] == upper["results"]

    def test_search_excludes_none_prices(self, client):
        with patch("app.routers.stocks.get_current_price", new=AsyncMock(return_value=None)):
            data = client.get("/api/stocks/search?q=AAPL").json()
        assert data["results"] == []

    def test_search_no_match_returns_empty(self, client):
        with patch("app.routers.stocks.get_current_price", new=AsyncMock(return_value=100.0)):
            data = client.get("/api/stocks/search?q=ZZZZ").json()
        assert data["results"] == []

    def test_search_result_has_ticker_name_price(self, client):
        with patch("app.routers.stocks.get_current_price", new=AsyncMock(return_value=150.0)):
            data = client.get("/api/stocks/search?q=AAPL").json()
        result = data["results"][0]
        assert result["ticker"] == "AAPL"
        assert result["name"] == "Apple"
        assert result["price"] == 150.0

    def test_search_can_return_multiple_matches(self, client):
        # "A" matches many tickers (AAPL, AMZN, ADBE, BABA, etc.)
        with patch("app.routers.stocks.get_current_price", new=AsyncMock(return_value=100.0)):
            data = client.get("/api/stocks/search?q=A").json()
        assert len(data["results"]) > 1


# ---------------------------------------------------------------------------
# GET /api/stocks/{ticker}
# ---------------------------------------------------------------------------

class TestGetSingleStock:

    def test_returns_200_for_known_ticker(self, client):
        with patch("app.routers.stocks.get_current_price", new=AsyncMock(return_value=150.0)):
            response = client.get("/api/stocks/AAPL")
        assert response.status_code == 200

    def test_response_has_ticker_name_price(self, client):
        with patch("app.routers.stocks.get_current_price", new=AsyncMock(return_value=150.0)):
            data = client.get("/api/stocks/AAPL").json()
        assert data["ticker"] == "AAPL"
        assert data["name"] == "Apple"
        assert data["price"] == 150.0

    def test_ticker_uppercased_in_response(self, client):
        with patch("app.routers.stocks.get_current_price", new=AsyncMock(return_value=150.0)):
            data = client.get("/api/stocks/aapl").json()
        assert data["ticker"] == "AAPL"

    def test_returns_404_when_price_unavailable(self, client):
        with patch("app.routers.stocks.get_current_price", new=AsyncMock(return_value=None)):
            response = client.get("/api/stocks/AAPL")
        assert response.status_code == 404

    def test_404_detail_contains_ticker(self, client):
        with patch("app.routers.stocks.get_current_price", new=AsyncMock(return_value=None)):
            data = client.get("/api/stocks/FAKE").json()
        assert "FAKE" in data["detail"]

    def test_unknown_ticker_name_falls_back_to_ticker(self, client):
        with patch("app.routers.stocks.get_current_price", new=AsyncMock(return_value=99.0)):
            data = client.get("/api/stocks/XYZW").json()
        assert data["name"] == "XYZW"
        assert data["ticker"] == "XYZW"
