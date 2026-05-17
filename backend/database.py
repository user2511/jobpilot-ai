# backend/database.py
# SQLite connection and session management.
# Swap DATABASE_URL to postgres:// later — zero code changes needed.

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from backend.config import settings
import os

# Create data directory if it doesn't exist
os.makedirs("data", exist_ok=True)

# SQLite needs check_same_thread=False for FastAPI's threading model
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=False  # set True to log all SQL queries during dev
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    FastAPI dependency — yields a DB session per request.
    Always closes the session after the request completes.
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
