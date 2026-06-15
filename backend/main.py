from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from app.tasks.snapshot import create_daily_snapshot
from app.tasks.auto_trade_executor import check_auto_trades
from app.core.config import settings
from app.utils.logger import logger
from app.routers import auth, users, leaderboard
from app.routers.trading import router as trading_router
from app.routers.auto_trades import router as auto_trades_router
from app.routers.stocks import router as stocks_router
from app.services.redis_client import redis_client
from app.routers.leaderboard_history import router as leaderboard_history_router

app = FastAPI(title="TU Stock Exchange API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080", "http://0.0.0.0:8080", "http://127.0.0.1:8080",
        "http://localhost:5173", "http://127.0.0.1:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

scheduler = BackgroundScheduler()

@app.on_event("startup")
def startup_event():
    try:
        if not redis_client.ping():
            logger.error("Failed to connect to Redis on startup")
        else:
            logger.info("Connected to Redis successfully")
    except Exception as e:
        logger.error(f"Redis not available: {e}")

scheduler.add_job(
    create_daily_snapshot,
    'cron',
    hour=0,
    minute=0,
    id='daily_snapshot_job',
    replace_existing=True
)

scheduler.add_job(
    check_auto_trades,
    'interval',
    hours=1,
    id='auto_trades_job',
    replace_existing=True
)

scheduler.start()
logger.info("Scheduled daily net worth snapshot job (runs at 00:00 UTC)")

@app.on_event("shutdown")
def shutdown_event():
    try:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
    except Exception:
        pass

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(leaderboard.router, prefix="/api")
app.include_router(trading_router, prefix="/api")
app.include_router(auto_trades_router, prefix="/api")
app.include_router(stocks_router, prefix="/api")
app.include_router(leaderboard_history_router, prefix="/api")

@app.get("/")
def root():
    return {"message": "TU Stock Exchange API is running"}