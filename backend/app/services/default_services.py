from datetime import datetime
from sqlalchemy.orm import Session

from app.models.users import User
from app.models.holding import Holding
from app.models.auto_trade import AutoTrade
from app.models.trade import Trade


BANKRUPTCY_THRESHOLD = 100.0
RECOVERY_BALANCE = 1000.0


async def check_and_handle_bankruptcy(
    user: User,
    net_worth: float,
    db: Session,
) -> bool:
    """Declare bankruptcy if the user's net worth has fallen below the minimum threshold.

    When triggered, liquidates all holdings at the current market price
    (falling back to ``average_buy_price`` if the price API is unavailable),
    records a ``sell`` trade for each liquidated holding, cancels all active
    auto-trade rules, and marks the account as bankrupt with a timestamp.

    This function is idempotent: calling it on an already-bankrupt user is a
    no-op and returns False.

    Args:
        user: The user to evaluate. Modified in place if bankruptcy is triggered.
        net_worth: Pre-calculated net worth (cash balance + current market value
            of all holdings) in USD.
        db: Active database session used for queries and the final commit.

    Returns:
        True if bankruptcy was declared during this call, False if the user's
        net worth is at or above the threshold or the account was already bankrupt.

    Side effects:
        On bankruptcy: deletes all ``Holding`` rows for the user, inserts
        ``Trade`` rows of type ``"sell"`` for each liquidated holding, sets
        all active ``AutoTrade`` rows to ``is_active = False``, sets
        ``user.is_bankrupt = True`` and ``user.bankrupt_at``, and commits
        the database session.
    """
    if user.is_bankrupt or net_worth >= BANKRUPTCY_THRESHOLD:
        return False

    holdings = db.query(Holding).filter(Holding.user_id == user.id).all()

    from app.services.stock_price import get_current_price

    for holding in holdings:
        price = await get_current_price(holding.ticker)
        if price is None:
            price = holding.average_buy_price

        liquidation_value = price * holding.quantity
        user.balance += liquidation_value

        liquidation_trade = Trade(
            user_id=user.id,
            ticker=holding.ticker,
            trade_type="sell",
            quantity=holding.quantity,
            price=price,
            total_value=liquidation_value,
        )
        db.add(liquidation_trade)
        db.delete(holding)

    db.query(AutoTrade).filter(
        AutoTrade.user_id == user.id,
        AutoTrade.is_active == True,
    ).update({"is_active": False})

    user.is_bankrupt = True
    user.bankrupt_at = datetime.utcnow()

    db.commit()
    db.refresh(user)
    return True


def recover_from_bankruptcy(user: User, db: Session) -> User:
    """Reset a bankrupt user with a fresh starting balance.

    Clears the ``is_bankrupt`` flag and resets the cash balance to
    ``RECOVERY_BALANCE`` ($1,000), allowing the user to resume trading.
    The ``bankrupt_at`` timestamp is intentionally preserved as a permanent
    historical record of when the bankruptcy occurred.

    If the user is not currently bankrupt this function is a no-op and
    returns the user unchanged.

    Args:
        user: The bankrupt user to recover. Modified in place.
        db: Active database session used for the commit.

    Returns:
        The updated ``User`` instance (same object that was passed in).
    """
    if not user.is_bankrupt:
        return user

    user.balance = RECOVERY_BALANCE
    user.is_bankrupt = False

    db.commit()
    db.refresh(user)
    return user
