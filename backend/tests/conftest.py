import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

from main import app
from app.db.database import Base
from app.db.dependencies import get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture()
def client():
    Base.metadata.create_all(bind=engine)

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()

@pytest.fixture()
def db():
    """Provide a database session for tests that need direct database access"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture()
def setup_leaderboard_test_data(db):
    """Set up test data specifically for leaderboard tests"""
    users = [
        {
            "id": 1,
            "username": "user1",
            "email": "user1@example.com",
            "password_hash": "hash1",
            "balance": 10000.0,
            "is_bankrupt": False,
            "registered_at": datetime.utcnow()
        },
        {
            "id": 2,
            "username": "user2",
            "email": "user2@example.com",
            "password_hash": "hash2",
            "balance": 5000.0,
            "is_bankrupt": False,
            "registered_at": datetime.utcnow()
        },
        {
            "id": 3,
            "username": "user3",
            "email": "user3@example.com",
            "password_hash": "hash3",
            "balance": 2000.0,
            "is_bankrupt": False,
            "registered_at": datetime.utcnow()
        },
        {
            "id": 4,
            "username": "user4",
            "email": "user4@example.com",
            "password_hash": "hash4",
            "balance": 4000.0,
            "is_bankrupt": False,
            "registered_at": datetime.utcnow()
        },
        {
            "id": 5,
            "username": "user5",
            "email": "user5@example.com",
            "password_hash": "hash5",
            "balance": 3000.0,
            "is_bankrupt": False,
            "registered_at": datetime.utcnow()
        },
        {
            "id": 6,
            "username": "bankrupt_user",
            "email": "bankrupt@example.com",
            "password_hash": "hash6",
            "balance": 0.0,
            "is_bankrupt": True,
            "registered_at": datetime.utcnow()
        },
    ]
    
    for user in users:
        db.execute(
            """
            INSERT INTO users (id, username, email, password_hash, balance, is_bankrupt, registered_at)
            VALUES (:id, :username, :email, :password_hash, :balance, :is_bankrupt, :registered_at)
            """,
            user
        )
    
    holdings = [
        {"user_id": 1, "ticker": "AAPL", "quantity": 10, "average_buy_price": 150.0, "updated_at": datetime.utcnow()},
        {"user_id": 2, "ticker": "TSLA", "quantity": 5, "average_buy_price": 250.0, "updated_at": datetime.utcnow()},
        {"user_id": 3, "ticker": "MSFT", "quantity": 8, "average_buy_price": 300.0, "updated_at": datetime.utcnow()},
        {"user_id": 1, "ticker": "GOOG", "quantity": 2, "average_buy_price": 1200.0, "updated_at": datetime.utcnow()},
    ]
    
    for holding in holdings:
        db.execute(
            """
            INSERT INTO holdings (user_id, ticker, quantity, average_buy_price, updated_at)
            VALUES (:user_id, :ticker, :quantity, :average_buy_price, :updated_at)
            """,
            holding
        )
    
    stock_prices = [
        {"ticker": "AAPL", "price": 155.0, "timestamp": datetime.utcnow()},
        {"ticker": "TSLA", "price": 260.0, "timestamp": datetime.utcnow()},
        {"ticker": "MSFT", "price": 310.0, "timestamp": datetime.utcnow()},
        {"ticker": "GOOG", "price": 1250.0, "timestamp": datetime.utcnow()},
    ]
    
    for price in stock_prices:
        db.execute(
            """
            INSERT INTO stock_price_history (ticker, price, timestamp)
            VALUES (:ticker, :price, :timestamp)
            """,
            price
        )
    
    db.commit()
    
    return db

@pytest.fixture()
def setup_leaderboard_history_test_data(db):
    """Set up test data specifically for leaderboard history tests"""
    users = [
        {
            "id": 1,
            "username": "user1",
            "email": "user1@example.com",
            "password_hash": "hash1",
            "balance": 10000.0,
            "is_bankrupt": False,
            "registered_at": datetime.utcnow()
        },
        {
            "id": 2,
            "username": "user2",
            "email": "user2@example.com",
            "password_hash": "hash2",
            "balance": 5000.0,
            "is_bankrupt": False,
            "registered_at": datetime.utcnow()
        },
        {
            "id": 3,
            "username": "user3",
            "email": "user3@example.com",
            "password_hash": "hash3",
            "balance": 2000.0,
            "is_bankrupt": False,
            "registered_at": datetime.utcnow()
        },
        {
            "id": 4,
            "username": "bankrupt_user",
            "email": "bankrupt@example.com",
            "password_hash": "hash4",
            "balance": 0.0,
            "is_bankrupt": True,
            "registered_at": datetime.utcnow()
        },
    ]
    
    for user in users:
        db.execute(
            """
            INSERT INTO users (id, username, email, password_hash, balance, is_bankrupt, registered_at)
            VALUES (:id, :username, :email, :password_hash, :balance, :is_bankrupt, :registered_at)
            """,
            user
        )
    
    holdings = [
        {"user_id": 1, "ticker": "AAPL", "quantity": 10, "average_buy_price": 150.0, "updated_at": datetime.utcnow()},
        {"user_id": 2, "ticker": "TSLA", "quantity": 5, "average_buy_price": 250.0, "updated_at": datetime.utcnow()},
        {"user_id": 3, "ticker": "MSFT", "quantity": 8, "average_buy_price": 300.0, "updated_at": datetime.utcnow()},
        {"user_id": 1, "ticker": "GOOG", "quantity": 2, "average_buy_price": 1200.0, "updated_at": datetime.utcnow()},
    ]
    
    for holding in holdings:
        db.execute(
            """
            INSERT INTO holdings (user_id, ticker, quantity, average_buy_price, updated_at)
            VALUES (:user_id, :ticker, :quantity, :average_buy_price, :updated_at)
            """,
            holding
        )
    
    stock_prices = [
        {"ticker": "AAPL", "price": 155.0, "timestamp": datetime.utcnow()},
        {"ticker": "TSLA", "price": 260.0, "timestamp": datetime.utcnow()},
        {"ticker": "MSFT", "price": 310.0, "timestamp": datetime.utcnow()},
        {"ticker": "GOOG", "price": 1250.0, "timestamp": datetime.utcnow()},
    ]
    
    for price in stock_prices:
        db.execute(
            """
            INSERT INTO stock_price_history (ticker, price, timestamp)
            VALUES (:ticker, :price, :timestamp)
            """,
            price
        )
    
    # Create net worth history for multiple days
    now = datetime.utcnow()
    day3 = now - timedelta(days=3)
    day2 = now - timedelta(days=2)
    day1 = now - timedelta(days=1)
    
    net_worth_history = [
        {"user_id": 1, "net_worth": 10000.0, "timestamp": day3},
        {"user_id": 2, "net_worth": 5000.0, "timestamp": day3},
        {"user_id": 3, "net_worth": 2000.0, "timestamp": day3},
        
        {"user_id": 1, "net_worth": 12000.0, "timestamp": day2},
        {"user_id": 2, "net_worth": 4000.0, "timestamp": day2},
        {"user_id": 3, "net_worth": 3000.0, "timestamp": day2},
        
        {"user_id": 1, "net_worth": 11000.0, "timestamp": day1},
        {"user_id": 2, "net_worth": 6000.0, "timestamp": day1},
        {"user_id": 3, "net_worth": 2500.0, "timestamp": day1},
    ]
    
    for record in net_worth_history:
        db.execute(
            """
            INSERT INTO net_worth_history (user_id, net_worth, timestamp)
            VALUES (:user_id, :net_worth, :timestamp)
            """,
            record
        )
    
    db.commit()
    
    return db