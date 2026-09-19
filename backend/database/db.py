"""
Database connection setup (SQLAlchemy engine + session factory).
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

logger = logging.getLogger(__name__)

DATABASE_URL = "sqlite:///benefits_ai.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # required for SQLite + FastAPI
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Session:
    """
    FastAPI dependency that yields a DB session and guarantees
    it's closed afterwards, even if an exception occurs.

    Usage in an endpoint:
        def endpoint(db: Session = Depends(get_db)): ...
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        logger.exception("Database session error, rolling back.")
        db.rollback()
        raise
    finally:
        db.close()