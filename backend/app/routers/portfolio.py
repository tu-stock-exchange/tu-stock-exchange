from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.db.dependencies import get_db
from pydantic import BaseModel
from datetime import datetime
from typing import List
from app.schemas.holding_item import HoldingItem

router = APIRouter()

class PortfolioHistoryItem(BaseModel):
    timestamp: datetime
    net_worth: float
    balance: float
    holdings_value: float
    holdings: List[HoldingItem] = []

    class Config:
        orm_mode = True

@router.get("/users/{user_id}/portfolio/history", response_model=List[PortfolioHistoryItem])
def get_portfolio_history(
    user_id: int,
    db: Session = Depends(get_db)
):

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get net worth history (main timeline)
    net_worth_history = db.query(
        models.NetWorthHistory.timestamp,
        models.NetWorthHistory.net_worth
    ).filter(
        models.NetWorthHistory.user_id == user_id
    ).order_by(
        models.NetWorthHistory.timestamp
    ).all()

    holdings_history = db.query(
        models.HoldingHistory
    ).filter(
        models.HoldingHistory.user_id == user_id
    ).order_by(
        models.HoldingHistory.timestamp
    ).all()

    holdings_by_timestamp = {}
    for item in holdings_history:
        if item.timestamp not in holdings_by_timestamp:
            holdings_by_timestamp[item.timestamp] = []
        holdings_by_timestamp[item.timestamp].append(item)

    history = []
    for timestamp, net_worth in net_worth_history:
        # Calculate balance and holdings value
        balance = net_worth - sum(h.quantity * h.current_price for h in holdings_by_timestamp.get(timestamp, []))
        holdings_value = net_worth - balance

        holdings = []
        for h in holdings_by_timestamp.get(timestamp, []):
            holdings.append(
                schemas.HoldingItem(
                    ticker=h.ticker,
                    quantity=h.quantity,
                    average_buy_price=h.average_buy_price,
                    current_price=h.current_price
                )
            )

        history.append(
            PortfolioHistoryItem(
                timestamp=timestamp,
                net_worth=net_worth,
                balance=balance,
                holdings_value=holdings_value,
                holdings=holdings
            )
        )

    return history