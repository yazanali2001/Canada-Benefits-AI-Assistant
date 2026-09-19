"""
Defines the survey questions, their fixed multiple-choice options,
and how each fixed option maps to a stored profile value.

"Other" is always available as an escape hatch — free text typed
for "Other" is resolved dynamically by backend/llm/extraction_llm.py
(an actual LLM call), not by any hardcoded pattern here.
"""

from typing import Any, Optional

QUESTIONS: list[dict[str, Any]] = [
    {
        "field": "employment_status",
        "question": "What is your current employment status?",
        "options": ["Employed", "Unemployed", "Self-employed", "Retired", "Other"],
        "value_map": {
            "Employed": "employed",
            "Unemployed": "unemployed",
            "Self-employed": "self_employed",
            "Retired": "retired",
        },
    },
    {
        "field": "marital_status",
        "question": "What is your current marital status?",
        "options": ["Single", "Married", "Common-law", "Divorced/Separated", "Widowed", "Other"],
        "value_map": {
            "Single": "single",
            "Married": "married",
            "Common-law": "common_law",
            "Divorced/Separated": "divorced_separated",
            "Widowed": "widowed",
        },
    },
    {
        "field": "province",
        "question": "Which province or territory do you currently live in?",
        "options": [
            "Ontario", "Quebec", "British Columbia", "Alberta", "Manitoba",
            "Saskatchewan", "Nova Scotia", "New Brunswick",
            "Newfoundland and Labrador", "Prince Edward Island",
            "Northwest Territories", "Yukon", "Nunavut", "Other",
        ],
        "value_map": {
            p: p for p in [
                "Ontario", "Quebec", "British Columbia", "Alberta", "Manitoba",
                "Saskatchewan", "Nova Scotia", "New Brunswick",
                "Newfoundland and Labrador", "Prince Edward Island",
                "Northwest Territories", "Yukon", "Nunavut",
            ]
        },
    },
    {
        "field": "residency_status",
        "question": "What is your residency status in Canada?",
        "options": [
            "Canadian citizen", "Permanent resident",
            "Temporary resident / Work permit", "Refugee or protected person", "Other",
        ],
        "value_map": {
            "Canadian citizen": "citizen",
            "Permanent resident": "permanent_resident",
            "Temporary resident / Work permit": "temporary_resident",
            "Refugee or protected person": "refugee_protected_person",
        },
    },
    {
        "field": "student",
        "question": "Are you currently a student?",
        "options": ["Yes", "No"],
        "value_map": {"Yes": True, "No": False},
    },
    {
        "field": "children",
        "question": "How many children or dependents do you have?",
        "options": ["0", "1", "2", "3 or more", "Other"],
        "value_map": {"0": 0, "1": 1, "2": 2, "3 or more": 3},
    },
    {
        "field": "income",
        "question": "What is your approximate yearly income (CAD)?",
        "options": [
            "Under $20,000", "$20,000–$40,000", "$40,000–$70,000", "Over $70,000", "Other",
        ],
        "value_map": {
            "Under $20,000": 15000,
            "$20,000–$40,000": 30000,
            "$40,000–$70,000": 55000,
            "Over $70,000": 80000,
        },
    },
    {
        "field": "disability",
        "question": "Do you have a disability?",
        "options": ["Yes", "No"],
        "value_map": {"Yes": True, "No": False},
    },
    {
        "field": "senior",
        "question": "Are you 65 years of age or older?",
        "options": ["Yes", "No"],
        "value_map": {"Yes": True, "No": False},
    },
    {
        "field": "veteran_status",
        "question": "Are you a veteran of the Canadian Armed Forces?",
        "options": ["Yes", "No"],
        "value_map": {"Yes": True, "No": False},
    },
    {
        "field": "indigenous_status",
        "question": "Do you identify as First Nations, Métis, or Inuit?",
        "options": ["Yes", "No"],
        "value_map": {"Yes": True, "No": False},
    },
    {
        "field": "housing_problem",
        "question": "Are you currently facing any housing difficulties?",
        "options": ["Yes", "No"],
        "value_map": {"Yes": True, "No": False},
    },
]


def get_question_by_field(field: str) -> Optional[dict[str, Any]]:
    """Look up a question's full definition (text + options + map) by field name."""
    return next((q for q in QUESTIONS if q["field"] == field), None)


def get_next_question(memory: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Return the next unanswered question's full definition, or None if complete."""
    for question in QUESTIONS:
        if memory.get(question["field"], {}).get("value") is None:
            return question
    return None