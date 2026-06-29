from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.models.auto_trade import AutoTrade
from app.models.users import User
from app.db.dependencies import get_db
from app.core.auth_dependencies import get_current_user

router = APIRouter()

class AutoTradeRequest(BaseModel):
    ticker : str
    trade_type : str
    target_price : float
    quantity : int 

@router.post("/auto-trades")
def create_auto_trade(request: AutoTradeRequest, current_user : User = Depends(get_current_user), db : Session = Depends(get_db)):
    """Create a new auto trade rule that will execute when the target price is reached."""
    new_auto_trade = AutoTrade(
        user_id = current_user.id, 
        ticker = request.ticker, 
        trade_type = request.trade_type, 
        target_price = request.target_price, 
        quantity = request.quantity
    )

    db.add(new_auto_trade)
    db.commit()

    return { "message" : "Auto trade created", 
            "id" : new_auto_trade.id}

@router.get("/auto-trades")
def get_auto_trades(current_user : User = Depends(get_current_user), db : Session = Depends(get_db)):
    """Return all active auto trade rules for the current user."""
    auto_trades = db.query(AutoTrade).filter(
        AutoTrade.user_id == current_user.id,
        AutoTrade.is_active == True
    ).all()
    return {"auto_trades" : auto_trades}

@router.delete("/auto-trades/{auto_trade_id}")
def delete_auto_trade(auto_trade_id : int, current_user : User = Depends(get_current_user), db : Session = Depends(get_db)):
    """Deactivate an auto trade rule by setting is_active to False (soft delete)."""
    auto_trade = db.query(AutoTrade).filter(AutoTrade.id == auto_trade_id, AutoTrade.user_id == current_user.id).first()
    
    if not auto_trade:
        raise HTTPException(status_code = 404, detail = "Auto trade not found")
    
    auto_trade.is_active = False
    db.commit()
    return {"message" : "Auto trade deactivated"}