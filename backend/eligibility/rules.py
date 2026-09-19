"""
Declarative eligibility rules for Canadian public benefits.

To add a new benefit: add one EligibilityRule entry below.
No other code needs to change.
"""

from dataclasses import dataclass
from typing import Callable
from backend.eligibility.profile import UserProfile


@dataclass(frozen=True)
class EligibilityRule:
    program_name: str
    reason: str
    condition: Callable[[UserProfile], bool]


RULES: list[EligibilityRule] = [
    EligibilityRule(
        program_name="Employment Insurance (EI)",
        reason="You reported being unemployed.",
        condition=lambda p: p.employment_status == "unemployed",
    ),
    EligibilityRule(
        program_name="Canada Child Benefit (CCB)",
        reason="You reported having one or more children.",
        condition=lambda p: bool(p.children and p.children > 0),
    ),
    EligibilityRule(
        program_name="Education / Student Benefits",
        reason="You reported being a student.",
        condition=lambda p: p.student is True,
    ),
    EligibilityRule(
        program_name="Housing Benefits",
        reason="Your reported income is below the low-income housing threshold.",
        condition=lambda p: bool(p.income and p.income < 40_000),
    ),
    EligibilityRule(
        program_name="Disability Tax Credit",
        reason="You reported having a disability.",
        condition=lambda p: p.disability is True,
    ),
    EligibilityRule(
        program_name="Old Age Security (OAS)",
        reason="You reported being a senior (65+).",
        condition=lambda p: p.senior is True,
    ),
    EligibilityRule(
        program_name="GST/HST Credit",
        reason="Your reported income is within the low-to-modest income range.",
        condition=lambda p: bool(p.income and p.income < 50_000),
    ),
    EligibilityRule(
        program_name="Veterans Affairs Canada Benefits",
        reason="You reported being a veteran of the Canadian Armed Forces.",
        condition=lambda p: p.veteran_status is True,
    ),
    EligibilityRule(
        program_name="Indigenous Services Canada Programs",
        reason="You identified as First Nations, Métis, or Inuit.",
        condition=lambda p: p.indigenous_status is True,
    ),
]