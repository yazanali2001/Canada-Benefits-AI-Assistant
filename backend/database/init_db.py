"""
One-off script to create all database tables.
Run with: python -m backend.database.init_db
"""

import logging
from backend.database.db import Base, engine
from backend.database import models  # noqa: F401  (must be imported before create_all)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db() -> None:
    """Create all tables defined in models.py if they don't already exist."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully.")
    except Exception:
        logger.exception("Failed to initialize database.")
        raise


if __name__ == "__main__":
    init_db()