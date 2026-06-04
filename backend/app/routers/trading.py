from urllib import response

import yfinance as yf
import redis
import json
from fastapi import FastAPI, APIRouter, HTTPException
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
app = FastAPI()
r = redis.Redis(host='localhost', port=6379, db=0)
router = APIRouter(prefix="/stocks")
"""
Returns the stock price. 

Args:
    Ticker (str): name of the Company.

Returns:
    float: stock price.
"""
@router.get("")
def get_current_price(ticker: str) -> float:
    # price = yf.Ticker(ticker)
    # price = price.info.get("currentPrice")
    # return price
    try:
        ticker_data = yf.Ticker(ticker)
        price = ticker_data.fast_info["last_price"]
    except AttributeError:
        raise HTTPException(status_code=404, detail=f"Ticker: {ticker} not found")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Unknown problem")
    return round(price, 2)

"""
Searches for a ticker of a given company

Args:
    q (str): name of the Company.

Returns:
    JSON af all companies that user was probably looking for
"""
@router.get("/search")
def search_ticker(q: str):
    try:
        results = yf.Search(q)
        return results.quotes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

"""
Searches for a ticker of a given company

Returns:
    JSON of 20 companies with most actives(I am not sure how can i do this function) 
"""
@router.get("/popular")
def search_popular_tickers():
    try:
        results = yf.screen("most_actives")
        quotes = results["quotes"]
        i = 0
        response = []
        for q in quotes:
            if i == 20:
                break
            short_name = q["shortName"]
            ticker = q["symbol"]
            response.append({
                "name": short_name,
                "ticker": ticker
            })
            i += 1
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def download_tickers(tickers: list, period: str = "1d"):
    data = yf.download(tickers, period=period)
    if data is None or data.empty:
        raise HTTPException(status_code=404, detail="No data found for given tickers")
    return data["Close"]

@router.get("/check")
def check():
    try:
        return download_tickers(["AAPL"], "1d")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

"""
Gets all user Tickers and updates the price  every day 

Returns:
    JSON of 20 companies with most actives(I am not sure how can i do this function) 
"""
def update_price_history():
    # 1. get all tickers from your portfolios in DB
    # tickers = get_all_tickers_from_db()# get users tickets from db
    tickers = ["AAPL", "META"]
    data = yf.download(tickers, period="1d")

    for ticker in tickers:
        print("Running update_price_history...")
        price = data["Close"][ticker].iloc[-1]
        r.setex(ticker, 3600, json.dumps(float(price)))
scheduler.add_job(update_price_history, "interval", hours=1)
scheduler.start()
"""
Returns the stock price, caches it to redis. 

Args:
    Ticker (str): name of the Company.

Returns:
    float: stock price.
"""
@router.get("/{ticker}")
def get_ticker(ticker: str) -> float:
    ticker_price =float(r.get(ticker))
    if ticker_price:
        print("from cache")
        return ticker_price
    try:
        price = get_current_price(ticker)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Ticker: {ticker} not found")

    r.setex(ticker, 3600, json.dumps(price))
    return price

"""
Returns the stock history over some period. 

Args:
    ticker (str): name of the Company.
    period (int): period of the history in months

Returns:
    str: history of the day with: "Date", "Open", "High", "Low", "Close", "Volume", "Dividends", "Stock Splits".
"""
@router.get("/{ticker}/{period}")
def get_ticker_history(ticker: str, period: str):
    try:
        ticker_data = yf.Ticker(ticker)
        ticker_history = ticker_data.history(period)
        if ticker_history.empty:
            raise HTTPException(status_code=404, detail=f"Wrong ticker:{ticker} or period:{period}")
    except AttributeError:
        raise HTTPException(status_code=404, detail=f"Ticker: {ticker} not found")
    return ticker_history.reset_index().to_dict(orient="records")
app.include_router(router)
