from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app import schemas, models
from app.db import database
from app.db.dependencies import get_db
from app.schemas.leaderboard_history import LeaderboardHistoryItem, LeaderboardItem

router = APIRouter()

@router.get("/leaderboard/history", response_model=list[LeaderboardHistoryItem])
def get_leaderboard_history(
    db: Session = Depends(get_db),
    days: int = 30
):
    """Build a time series of leaderboard rankings from net worth history.

    For each distinct timestamp recorded in net worth history within the
    requested window, ranks users by net worth in descending order,
    assigns each a 1-based rank, and keeps only the top 10 users for
    that timestamp. The resulting snapshots are returned in ascending
    chronological order (oldest first).

    Args:
        db: Database session used to query net worth history and users.
        days: Number of days of history to include, counting back from
            the current time. Defaults to 30.

    Returns:
        list[LeaderboardHistoryItem]: One entry per timestamp found in
        the window, each containing the ``timestamp`` and up to 10
        ranked ``LeaderboardItem`` entries (``user_id``, ``username``,
        ``portfolio_value``, ``rank``).

    Raises:
        HTTPException: With status code 500 if an unexpected error
            occurs while building the leaderboard history.
    """
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get all net worth history within the date range
        history_records = db.query(
            models.NetWorthHistory.user_id,
            models.NetWorthHistory.net_worth,
            models.NetWorthHistory.timestamp
        ).filter(
            models.NetWorthHistory.timestamp >= start_date
        ).order_by(
            models.NetWorthHistory.timestamp
        ).all()

        # Group records by timestamp
        history_by_timestamp = {}
        for record in history_records:
            timestamp = record.timestamp
            if timestamp not in history_by_timestamp:
                history_by_timestamp[timestamp] = []
            history_by_timestamp[timestamp].append({
                "user_id": record.user_id,
                "net_worth": record.net_worth
            })

        # For each timestamp, sort users by net worth to get rankings
        leaderboard_history = []
        for timestamp, records in history_by_timestamp.items():
            # Sort by net worth (descending)
            records.sort(key=lambda x: x["net_worth"], reverse=True)
            
            # Create ranking data
            rankings = []
            for rank, record in enumerate(records, 1):
                # Get username (need to join with User table)
                user = db.query(models.User).filter(
                    models.User.id == record["user_id"]
                ).first()
                
                if user:
                    rankings.append(
                        schemas.LeaderboardItem(
                            user_id=record["user_id"],
                            username=user.username,
                            portfolio_value=round(record["net_worth"], 2),
                            rank=rank
                        )
                    )
            
            # Add to history
            leaderboard_history.append(
                schemas.LeaderboardHistoryItem(
                    timestamp=timestamp,
                    rankings=rankings[:10]  # Top 10 users
                )
            )

        # Sort history by timestamp (oldest first)
        leaderboard_history.sort(key=lambda x: x.timestamp)
        
        return leaderboard_history

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Internal server error while generating leaderboard history"
        ) from e