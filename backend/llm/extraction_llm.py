"""
Dynamic, LLM-based extraction for free-text "Other" answers.
"""

import json
import logging
from typing import Any, Optional

from backend.llm.groq_client import generate_response

logger = logging.getLogger(__name__)

FIELD_SPECS: dict[str, str] = {
    "employment_status": (
        "a short lowercase snake_case label such as 'employed', "
        "'unemployed', 'self_employed', 'retired', or another label "
        "that best fits their described situation"
    ),
    "marital_status": (
        "a short lowercase snake_case label such as 'single', 'married', "
        "'common_law', 'divorced_separated', 'widowed', or another fitting label"
    ),
    "province": "the name of the Canadian province or territory they mentioned, as a proper noun string",
    "residency_status": (
        "a short lowercase snake_case label such as 'citizen', 'permanent_resident', "
        "'temporary_resident', 'refugee_protected_person', or another fitting label"
    ),
    "children": "an integer — how many children/dependents they have",
    "income": "an integer — their approximate yearly income in CAD, no currency symbols",
    "disability": "a boolean — true if they indicate having a disability, else false",
    "senior": "a boolean — true if they indicate being 65 or older, else false",
    "veteran_status": "a boolean — true if they indicate being a veteran, else false",
    "indigenous_status": "a boolean — true if they indicate being Indigenous (First Nations, Métis, or Inuit), else false",
    "housing_problem": "a boolean — true if they indicate a housing difficulty, else false",
    "student": "a boolean — true if they indicate being a student, else false",
}


def extract_other_answer(field: str, free_text: str) -> Optional[Any]:
    """
    Use the LLM to turn a free-text "Other" answer into a structured
    value for the given profile field.
    """
    spec = FIELD_SPECS.get(field)
    if spec is None:
        logger.warning("No extraction spec defined for field=%s", field)
        return None

    prompt = f"""Extract one value from the user's answer below.

Field: {field}
Expected value: {spec}

User's answer: "{free_text}"

Respond with ONLY a JSON object, no other text, in this exact shape:
{{"value": <the extracted value>}}"""

    raw = generate_response(prompt, temperature=0.0)

    try:
        cleaned = (
            raw.strip()
            .removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )
        parsed = json.loads(cleaned)
        return parsed.get("value")
    except (json.JSONDecodeError, AttributeError):
        logger.warning("Could not parse LLM extraction output for field=%s: %r", field, raw)
        return None