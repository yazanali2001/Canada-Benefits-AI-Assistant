"""
Evaluates a UserProfile against all known eligibility rules.
"""

import logging
from typing import TypedDict

from backend.eligibility.profile import UserProfile
from backend.eligibility.rules import RULES

logger = logging.getLogger(__name__)


class EligibilityResult(TypedDict):
    program_name: str
    reason: str
    confidence: str  # "high" — always high here, since these come from explicit rules


def evaluate_eligibility(profile: UserProfile) -> list[EligibilityResult]:
    """
    Check a user's profile against every rule and return the programs
    they currently qualify for, each with a plain-language reason.

    Every result here has confidence="high" because it's derived from
    an explicit, deterministic rule — not from LLM inference. This
    distinction is surfaced to the user in the final answer so they
    know what's guaranteed vs. what's a general suggestion.
    """
    results: list[EligibilityResult] = []

    for rule in RULES:
        try:
            if rule.condition(profile):
                results.append(
                    {
                        "program_name": rule.program_name,
                        "reason": rule.reason,
                        "confidence": "high",
                    }
                )
        except Exception:
            logger.exception("Rule '%s' failed to evaluate.", rule.program_name)

    return results


def diff_eligibility(
    before: list[EligibilityResult], after: list[EligibilityResult]
) -> dict[str, list[str]]:
    """
    Compare two eligibility snapshots and return what was gained/lost.
    Used when the user's profile changes mid-conversation (e.g. they
    report losing their job), so we can tell them exactly what changed.
    """
    before_names = {r["program_name"] for r in before}
    after_names = {r["program_name"] for r in after}

    return {
        "gained": sorted(after_names - before_names),
        "lost": sorted(before_names - after_names),
    }