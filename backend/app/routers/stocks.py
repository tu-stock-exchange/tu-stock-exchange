import asyncio
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

# 1. Fetch all 20 stocks concurrently for maximum speed
@router.get("/stocks/popular")
async def get_popular_stocks():
    # asyncio.gather runs all get_current_price calls at the exact same time
    prices = await asyncio.gather(*[get_current_price(ticker) for ticker in POPULAR_TICKERS])
    
    stocks = []
    # zip() pairs each ticker with its corresponding fetched price
    for ticker, price in zip(POPULAR_TICKERS, prices):
        if price is not None:
            stocks.append({
                "ticker": ticker,
                "name": TICKER_NAMES.get(ticker, ticker),
                "price": price,
            })
    return {"stocks": stocks}


# 2. Search endpoint optimized for concurrency
@router.get("/stocks/search")
async def search_stocks(q: str = ""):
    q = q.upper().strip()
    if not q:
        return {"results": []}
    
    # Find which tickers match the search query
    matching_tickers = [
        ticker for ticker in POPULAR_TICKERS 
        if q in ticker or q in TICKER_NAMES.get(ticker, ticker).upper()
    ]
    
    # Fetch only the matching prices concurrently
    prices = await asyncio.gather(*[get_current_price(ticker) for ticker in matching_tickers])
    
    results = []
    for ticker, price in zip(matching_tickers, prices):
        if price is not None:
            results.append({
                "ticker": ticker, 
                "name": TICKER_NAMES.get(ticker, ticker), 
                "price": price
            })
    return {"results": results}


# 3. Single stock endpoint
@router.get("/stocks/{ticker}")
async def get_stock(ticker: str):
    ticker = ticker.upper()
    # Added 'await' here!
    price = await get_current_price(ticker)
    if price is None:
        raise HTTPException(status_code=404, detail=f"Could not find price for {ticker}")
    name = TICKER_NAMES.get(ticker, ticker)
    return {"ticker": ticker, "name": name, "price": price}