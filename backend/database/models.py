"""
SQLAlchemy ORM models for the Canada Benefits AI app.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON

from backend.database.db import Base


class User(Base):
    """Registered user account."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class UserMemory(Base):
    """Stores the latest known profile/answers for a given user_id."""

    __tablename__ = "user_memory"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)
    memory_data = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class Conversation(Base):
    """Stores every chat turn for history/auditing purposes."""

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    user_message = Column(Text, nullable=False)
    assistant_response = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)