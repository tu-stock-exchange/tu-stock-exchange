from fastapi import APIRouter, HTTPException
from app.services.stock_price import get_current_price

router = APIRouter()

POPULAR_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA",
    "NVDA", "META", "NFLX", "AMD", "INTC",
    "PYPL", "ADBE", "CRM", "UBER", "DIS",
    "SNAP", "BABA", "SPOT", "SQ", "SHOP",
]

TICKER_NAMES = {
    "AAPL": "Apple", "MSFT": "Microsoft", "GOOGL": "Google",
    "AMZN": "Amazon", "TSLA": "Tesla", "NVDA": "NVIDIA",
    "META": "Meta", "NFLX": "Netflix", "AMD": "AMD",
    "INTC": "Intel", "PYPL": "PayPal", "ADBE": "Adobe",
    "CRM": "Salesforce", "UBER": "Uber", "DIS": "Disney",
    "SNAP": "Snap", "BABA": "Alibaba", "SPOT": "Spotify",
    "SQ": "Block", "SHOP": "Shopify",
}


@router.get("/stocks/popular")
def get_popular_stocks():
    stocks = []
    for ticker in POPULAR_TICKERS:
        price = get_current_price(ticker)
        if price is not None:
            stocks.append({
                "ticker": ticker,
                "name": TICKER_NAMES.get(ticker, ticker),
                "price": price,
            })
    return {"stocks": stocks}


@router.get("/stocks/search")
def search_stocks(q: str = ""):
    q = q.upper().strip()
    if not q:
        return {"results": []}
    results = []
    for ticker in POPULAR_TICKERS:
        name = TICKER_NAMES.get(ticker, ticker)
        if q in ticker or q in name.upper():
            price = get_current_price(ticker)
            if price is not None:
                results.append({"ticker": ticker, "name": name, "price": price})
    return {"results": results}


@router.get("/stocks/{ticker}")
def get_stock(ticker: str):
    ticker = ticker.upper()
    price = get_current_price(ticker)
    if price is None:
        raise HTTPException(status_code=404, detail=f"Could not find price for {ticker}")
    name = TICKER_NAMES.get(ticker, ticker)
    return {"ticker": ticker, "name": name, "price": price}
