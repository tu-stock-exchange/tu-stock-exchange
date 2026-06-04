import pytest
from unittest.mock import MagicMock

from fastapi import HTTPException
from fastapi.testclient import TestClient
from trading import app  # import your FastAPI app

client = TestClient(app)

# GET /stocks/?ticker=AAPL
def test_get_price(mocker):
    mock_ticker = MagicMock()
    mock_ticker.fast_info = {"last_price": 150.0}
    mocker.patch("yfinance.Ticker", return_value=mock_ticker)
    response = client.get("/stocks?ticker=AAPL")
    assert response.status_code == 200
    assert response.json() == 150.0

# GET /stocks?ticker=FalseTicker
def test_get_current_price_invalid_ticker(mocker):
    mock_ticker = MagicMock()
    mock_ticker.fast_info.__getitem__.side_effect = AttributeError
    mocker.patch("yfinance.Ticker", return_value=mock_ticker)

    response = client.get("/stocks?ticker=FalseTicker")
    assert response.status_code == 404

#GET /stocks/search?q=Apple
def test_search_ticker(mocker):
    mock_search = MagicMock()
    mock_search.quotes = [
        {"symbol": "AAPL", "shortname": "Apple Inc."},
        {"symbol": "AAPL.BA", "shortname": "Apple Inc. BA"}
    ]
    mocker.patch("yfinance.Search", return_value=mock_search)

    response = client.get("/stocks/search?q=Apple")
    print(response)
    assert response.json() == mock_search.quotes
    assert response.json()[0]["symbol"] == "AAPL"

#GET /stocks/Aapl/3d
def test_ticker_history(mocker):
    import pandas as pd
    mock_df = pd.DataFrame([
        {"Date": "2026-05-29", "Open": 311.77, "High": 315.0, "Low": 309.52, "Close": 312.05, "Volume": 70026800,
         "Dividends": 0, "Stock Splits": 0},
        {"Date": "2026-06-01", "Open": 309.63, "High": 310.94, "Low": 305.01, "Close": 306.30, "Volume": 48849900,
         "Dividends": 0, "Stock Splits": 0},
        {"Date": "2026-06-02", "Open": 307.45, "High": 315.45, "Low": 306.69, "Close": 315.20, "Volume": 44416900,
         "Dividends": 0, "Stock Splits": 0},
    ]).set_index("Date")

    mock_ticker = MagicMock()
    mock_ticker.history.return_value = mock_df
    mocker.patch("yfinance.Ticker", return_value=mock_ticker)

    response = client.get("/stocks/AAPL/3")

    assert response.status_code == 200
    assert len(response.json()) == 3
    assert response.json()[0]["Close"] == 312.05

