from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.users import User
from app.models.holding import Holding
from app.services.stock_price import get_current_price
from app.schemas.leaderboard_item import LeaderboardItem
from app.db.dependencies import get_db

router = APIRouter()

@router.get("/leaderboard", response_model=list[LeaderboardItem])
async def get_leaderboard(
    db: Session = Depends(get_db),
):

    try:
        users = db.query(
            User.id,
            User.username,
            User.balance
        ).all()

        holdings = db.query(
            Holding.user_id,
            Holding.ticker,
            Holding.quantity
        ).all()

        user_holdings = {}
        for holding in holdings:
            if holding.user_id not in user_holdings:
                user_holdings[holding.user_id] = []
            user_holdings[holding.user_id].append(holding)

        tickers = set(holding.ticker for holding in holdings)
        ticker_prices = {}
        
        for ticker in tickers:
            price = await get_current_price(ticker)
            ticker_prices[ticker] = price if price is not None else 0.0

        # Calculate portfolio values
        user_values = []
        for user in users:
            total_value = user.balance
            
            # Add value of all holdings
            if user.id in user_holdings:
                for holding in user_holdings[user.id]:
                    total_value += holding.quantity * ticker_prices[holding.ticker]
            
            user_values.append({
                "user_id": user.id,
                "username": user.username,
                "portfolio_value": round(total_value, 2)
            })

        user_values.sort(key=lambda x: x["portfolio_value"], reverse=True)

        return [
            LeaderboardItem(
                user_id=item["user_id"],
                username=item["username"],
                portfolio_value=item["portfolio_value"]
            )
            for item in user_values[:5]
        ]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Internal server error while generating leaderboard"
        ) from e