"""
Detects when a follow-up message signals a life-circumstance change
(job loss, new child, etc.) so the agent can re-run eligibility and
report what changed — instead of treating it as a generic question.
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Maps a detected life-change signal to the memory field(s) it should
# update. Kept intentionally small and explicit — this is a trigger
# detector, not a full extractor (extraction_llm.py already handles
# nuanced free text when the user is answering a specific question).
CHANGE_SIGNALS: list[dict[str, Any]] = [
    {"keywords": ["lost my job", "got fired", "laid off", "unemployed now"],
     "field": "employment_status", "value": "unemployed"},
    {"keywords": ["found a job", "got hired", "started working", "employed now"],
     "field": "employment_status", "value": "employed"},
    {"keywords": ["had a baby", "new child", "new baby", "another child"],
     "field": "children", "value": "__increment__"},
]


def detect_change(message: str, memory: dict[str, Any]) -> Optional[dict[str, Any]]:
    """
    Check a free-text message for a known life-change signal.
    Returns a field update dict if one is found, else None.
    """
    if not message:
        return None

    text = message.lower()

    for signal in CHANGE_SIGNALS:
        if any(kw in text for kw in signal["keywords"]):
            field = signal["field"]
            value = signal["value"]

            if value == "__increment__":
                current = memory.get(field, {}).get("value") or 0
                value = current + 1

            logger.info("Detected life change for field=%s -> %s", field, value)
            return {field: value}

    return None