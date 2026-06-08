from app.db import database

def get_db():
    db = database.SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()