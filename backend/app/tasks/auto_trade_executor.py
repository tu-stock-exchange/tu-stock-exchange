from app.db import database
from app.models.auto_trade import AutoTrade
from app.models.users import User
from app.models.holding import Holding
from app.models.trade import Trade
from app.services.stock_price import get_current_price

def check_auto_trades():
    """Check all active auto trades and execute any whose target price condition is met.

    Runs every hour via the APScheduler background scheduler. For each active
    auto trade, fetches the current market price and executes a buy or sell if
    the condition is met (buy: price <= target, sell: price >= target). Skips
    trades with unavailable prices, bankrupt users, or insufficient funds.
    Sets is_active = False after a successful execution.
    """
    db = database.SyncSessionLocal()

    try: 
        active_trades = db.query(AutoTrade).filter(AutoTrade.is_active == True).all()

        for auto_trade in active_trades:

            current_price = get_current_price(auto_trade.ticker)
            if current_price is None:
                continue

            should_execute = False

            if auto_trade.trade_type == "buy" and current_price <= auto_trade.target_price:
                should_execute = True
            elif auto_trade.trade_type == "sell" and current_price >= auto_trade.target_price:
                should_execute = True 

            if should_execute:
                user = db.query(User).filter(User.id == auto_trade.user_id).first()

                if not user or user.is_bankrupt:
                    auto_trade.is_active = False
                    continue

                total_value = current_price * auto_trade.quantity

                if auto_trade.trade_type == "buy":
                    if user.balance < total_value:
                        continue

                    user.balance -= total_value

                    holding = db.query(Holding).filter(
                        Holding.user_id == user.id,
                        Holding.ticker == auto_trade.ticker
                    ).first()
                    if holding:
                        holding.quantity += auto_trade.quantity
                    else:
                        new_holding = Holding(
                            user_id=user.id,
                            ticker=auto_trade.ticker,
                            quantity=auto_trade.quantity,
                            average_buy_price=current_price
                        )
                        db.add(new_holding)

                elif auto_trade.trade_type == "sell":
                    holding = db.query(Holding).filter(Holding.user_id == user.id, Holding.ticker == auto_trade.ticker).first()

                    if not holding or holding.quantity < auto_trade.quantity:
                        continue

                    holding.quantity -= auto_trade.quantity
                    if holding.quantity == 0:
                        db.delete(holding)
                    user.balance += total_value

                new_trade = Trade(
                    user_id=user.id,
                    ticker=auto_trade.ticker,
                    quantity=auto_trade.quantity,
                    price=current_price,
                    trade_type=auto_trade.trade_type,
                    total_value=total_value,
                )
                db.add(new_trade)
                auto_trade.is_active = False
                db.commit()   
    finally:
        db.close()
