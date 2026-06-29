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

    """Calculate live portfolio rankings and return the top 5 users.

    Each user's portfolio value is computed as cash balance plus the
    market value of all holdings (quantity x current price). Live prices
    are looked up once per unique ticker across all holdings to avoid
    redundant calls; a ticker whose price cannot be fetched contributes
    0.0 to that holding's value rather than raising an error. Users are
    then ranked by descending portfolio value.

    Args:
        db: Database session used to query users and holdings.

    Returns:
        list[LeaderboardItem]: The top 5 users ordered by portfolio
        value (highest first), each with ``user_id``, ``username``, and
        ``portfolio_value`` (rounded to 2 decimal places).

    Raises:
        HTTPException: With status code 500 if an unexpected error
            occurs while building the leaderboard.
    """

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