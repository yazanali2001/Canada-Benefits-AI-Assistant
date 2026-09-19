"""
Persistence layer for per-user conversation memory.
Handles reading/writing the UserMemory row — no extraction logic here.
"""

import logging
from typing import Any

from backend.database.db import SessionLocal
from backend.database.models import UserMemory

logger = logging.getLogger(__name__)

# Every field the eligibility engine (backend/eligibility/rules.py) needs.
DEFAULT_MEMORY: dict[str, Any] = {
    "employment_status": {"value": None, "asked": False},
    "marital_status": {"value": None, "asked": False},
    "province": {"value": None, "asked": False},
    "residency_status": {"value": None, "asked": False},
    "student": {"value": None, "asked": False},
    "children": {"value": None, "asked": False},
    "income": {"value": None, "asked": False},
    "disability": {"value": None, "asked": False},
    "senior": {"value": None, "asked": False},
    "veteran_status": {"value": None, "asked": False},
    "indigenous_status": {"value": None, "asked": False},
    "housing_problem": {"value": None, "asked": False},
    "current_question": None,
    "eligibility_summary_given": False,
    "last_known_eligibility": [],
}


def get_memory(user_id: str) -> dict[str, Any]:
    """
    Return the stored memory for a user, creating a fresh default
    record on first contact. Missing keys from older records are
    backfilled so the app never crashes on a stale schema.
    """
    db = SessionLocal()
    try:
        record = db.query(UserMemory).filter(UserMemory.user_id == user_id).first()

        if record is None:
            record = UserMemory(user_id=user_id, memory_data=DEFAULT_MEMORY.copy())
            db.add(record)
            db.commit()
            db.refresh(record)
            logger.info("Created new memory for user_id=%s", user_id)

        memory = record.memory_data
        for key, default_value in DEFAULT_MEMORY.items():
            if key not in memory:
                memory[key] = default_value

        return memory
    except Exception:
        logger.exception("Failed to load memory for user_id=%s", user_id)
        db.rollback()
        return DEFAULT_MEMORY.copy()
    finally:
        db.close()


def save_memory(user_id: str, memory: dict[str, Any]) -> None:
    """Persist an updated memory dict back to the database."""
    db = SessionLocal()
    try:
        record = db.query(UserMemory).filter(UserMemory.user_id == user_id).first()
        if record is None:
            record = UserMemory(user_id=user_id, memory_data=memory)
            db.add(record)
        else:
            record.memory_data = memory
        db.commit()
    except Exception:
        logger.exception("Failed to save memory for user_id=%s", user_id)
        db.rollback()
    finally:
        db.close()


def update_memory(user_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    """Apply extracted field updates on top of the existing memory and persist."""
    memory = get_memory(user_id)

    for key, value in updates.items():
        if key in memory and isinstance(memory[key], dict):
            memory[key]["value"] = value
            memory[key]["asked"] = True

    save_memory(user_id, memory)
    return memory