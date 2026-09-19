"""
Defines the shape of a user's profile as used by the eligibility engine.
"""

from typing import Optional
from pydantic import BaseModel


class UserProfile(BaseModel):
    """
    Structured, validated representation of what we know about a user.
    All fields are Optional because we build this up incrementally
    as the conversation progresses — not everything is known at once.
    """

    employment_status: Optional[str] = None
    marital_status: Optional[str] = None
    province: Optional[str] = None
    residency_status: Optional[str] = None
    student: Optional[bool] = None
    children: Optional[int] = None
    income: Optional[int] = None  # annual income in CAD
    disability: Optional[bool] = None
    senior: Optional[bool] = None
    veteran_status: Optional[bool] = None
    indigenous_status: Optional[bool] = None
    housing_problem: Optional[bool] = None

    @classmethod
    def from_memory_dict(cls, memory_data: dict) -> "UserProfile":
        """
        Build a UserProfile from the raw {"field": {"value": x}} shape
        stored in the database, ignoring unknown/legacy keys safely.
        """
        flat = {
            key: value.get("value") if isinstance(value, dict) else value
            for key, value in memory_data.items()
            if key not in ("current_question", "eligibility_summary_given", "last_known_eligibility")
        }
        return cls(**{k: v for k, v in flat.items() if k in cls.model_fields})