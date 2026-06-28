from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.models.trade import Trade
from app.models.users import User
from app.db.dependencies import get_db
from app.models.holding import Holding
from app.core.auth_dependencies import get_current_user
from app.services.stock_price import get_current_price
from app.services.default_services import check_and_handle_bankruptcy


router = APIRouter()

# data the frontend send
class TradeRequest(BaseModel):
    ticker: str
    quantity: int

@router.post("/trades/buy")
async def buy_stock(trade: TradeRequest, current_user : User = Depends(get_current_user),db : Session = Depends(get_db)):
    """Purchase shares of a stock at the current live price, updating balance and holdings."""
    user = current_user

    if user.is_bankrupt:
        raise HTTPException(status_code = 403, detail = "Account is bankrupt")

    price = await get_current_price(trade.ticker)
    if price is None:
        raise HTTPException(status_code=503, detail=f"Could not fetch price for {trade.ticker}")
    total_cost = price * trade.quantity

    if user.balance < total_cost:
        raise HTTPException(
            status_code = 400,
            detail = f"Insufficient funds. Need ${total_cost}, have ${user.balance}"
        )
    
    
    user.balance -= total_cost

    new_trade = Trade(
    user_id=user.id,
    ticker=trade.ticker,
    trade_type="buy",
    quantity=trade.quantity,
    price=price,
    total_value=total_cost,
    )
    db.add(new_trade)

    holding = db.query(Holding).filter(
        Holding.user_id == user.id, 
        Holding.ticker == trade.ticker).first()
    
    if holding:
        new_avg = (
            (holding.quantity * holding.average_buy_price) + (trade.quantity * price)
        ) / (holding.quantity + trade.quantity)
        holding.quantity += trade.quantity
        holding.average_buy_price = new_avg
    else:
        new_holding = Holding(
            user_id = user.id, 
            ticker = trade.ticker,
            quantity = trade.quantity, 
            average_buy_price = price
        )
        db.add(new_holding)



    db.commit()

    holdings = db.query(Holding).filter(Holding.user_id == user.id).all()
    total_stock_value = sum(
        h.quantity * (await get_current_price(h.ticker) or h.average_buy_price)
        for h in holdings
    )
    await check_and_handle_bankruptcy(user, user.balance + total_stock_value, db)

    return {
        "message": "Buy order successful",
        "ticker": trade.ticker,
        "quantity":trade.quantity, 
        "price_per_stock": price, 
        "total_cost" : total_cost,
        "new_balance": user.balance,
    }   

@router.post("/trades/sell")
async def sell_stock(trade: TradeRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Sell shares of a held stock at the current live price, updating balance and holdings."""
    user = current_user

    if user.is_bankrupt:
        raise HTTPException(status_code=403, detail="Account is bankrupt")

    holding = db.query(Holding).filter(
        Holding.user_id == user.id,
        Holding.ticker == trade.ticker
    ).first()

    if not holding or holding.quantity < trade.quantity:
        raise HTTPException(
            status_code = 400,
            detail = f"Not enough stocks. You have {holding.quantity if holding else 0}"
        )

    price = await get_current_price(trade.ticker)
    if price is None:
        raise HTTPException(status_code=503, detail=f"Could not fetch price for {trade.ticker}")
    total_value = price * trade.quantity

    new_trade = Trade(
        user_id=user.id,
        ticker=trade.ticker,
        trade_type="sell",
        quantity=trade.quantity,
        price=price,
        total_value=total_value,
    )
    db.add(new_trade)

    user.balance += total_value


    holding.quantity -= trade.quantity
    if holding.quantity == 0:
        db.delete(holding)

    db.commit()

    holdings = db.query(Holding).filter(Holding.user_id == user.id).all()
    total_stock_value = sum(
        h.quantity * (await get_current_price(h.ticker) or h.average_buy_price)
        for h in holdings
    )
    await check_and_handle_bankruptcy(user, user.balance + total_stock_value, db)

    return {
        "message": "Sell order successful",
        "ticker": trade.ticker,
        "quantity": trade.quantity,
        "price_per_stock": price,
        "total_value": total_value,
        "new_balance": user.balance,
    }

@router.get("/portfolio")
async def get_portfolio(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Return all current holdings with cost basis, live value, and profit/loss for each position."""
    user = current_user
    holdings = db.query(Holding).filter(Holding.user_id == user.id).all()

    holdings_data = []
    total_current_value = 0.0
    total_cost_basis = 0.0

    for holding in holdings:
        current_price = await get_current_price(holding.ticker)
        current_value = holding.quantity * current_price
        cost_basis = holding.quantity * holding.average_buy_price
        pnl = current_value - cost_basis
        pnl_percent = (pnl/cost_basis)*100 if cost_basis > 0 else 0.0

        total_current_value += current_value
        total_cost_basis += cost_basis

        holdings_data.append({
            "ticker":holding.ticker, 
            "quantity":holding.quantity,
            "average_buy_price":holding.average_buy_price, 
            "current_price": current_price, 
            "current_value": round(current_value, 2), 
            "cost_basis": round(cost_basis, 2), 
            "pnl": round(pnl, 2), 
            "pnl_percent": round(pnl_percent, 2), 
        })
    return{
        "holdings":holdings_data, 
        "total_current_value":round(total_current_value, 2), 
        "total_cost_basis": round(total_cost_basis, 2), 
        "total_pnl":round(total_current_value - total_cost_basis, 2), 
        "cash_balance": round(user.balance, 2), 
    }

@router.get("/trades/history")
async def get_history(current_user: User = Depends(get_current_user), page: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    """Return a paginated list of the user's past buy and sell trades."""
    offset = (page-1)*limit
    trades = db.query(Trade).filter(Trade.user_id == current_user.id).offset(offset).limit(limit).all()
    return {"trades" : trades, 
            "page" : page, 
            "limit":limit}


@router.get('/portfolio/networth')
async def get_networth(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Return the user's total net worth as the sum of cash balance and current market value of all holdings."""
    user = current_user
    holdings = db.query(Holding).filter(Holding.user_id == user.id).all()

    total_stock_value = 0.0
    for holding in holdings:
        current_price = await get_current_price(holding.ticker)
        total_stock_value += holding.quantity * current_price

    networth = user.balance + total_stock_value

    return {
        "networth" : round(networth, 2), 
        "cash_balance" : round(user.balance, 2), 
        "total_stock_value":round(total_stock_value, 2)
    }
