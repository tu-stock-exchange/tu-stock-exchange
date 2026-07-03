from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Index
from datetime import datetime
from app.db.database import Base

class HoldingHistory(Base):
    __tablename__ = "holding_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ticker = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    average_buy_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (Index('idx_holding_history_timestamp', 'timestamp'),)