"""Distress / stabilization mode triggers (Master Doc §5).

If ANY trigger fires, all invest_allocation cards are suppressed and the
ranking becomes: stabilize → runway-to-1-month → debt restructuring.
Boundary semantics are exact and unit-tested at ±1 rupee.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.config import DEBT_OVERHANG_MULTIPLE, DEBT_SERVICE_RATIO_MAX, RUNWAY_MIN_MONTHS
from app.rules.calcs import debt_monthly_interest, monthly_surplus, rupees
from app.schemas.nbca import Evidence
from app.schemas.profile import ProfileIn


class DistressReport(BaseModel):
    surplus_nonpositive: bool
    debt_service_excessive: bool
    runway_critical: bool
    debt_overhang: bool
    evidence: list[Evidence]

    @property
    def in_distress(self) -> bool:
        return (
            self.surplus_nonpositive
            or self.debt_service_excessive
            or self.runway_critical
            or self.debt_overhang
        )


def assess_distress(p: ProfileIn) -> DistressReport:
    surplus, ev_surplus = monthly_surplus(p)
    interest, ev_interest = debt_monthly_interest(p)

    surplus_nonpositive = surplus <= 0
    # strict >: interest of exactly 40% of income does NOT trigger
    debt_service_excessive = interest > DEBT_SERVICE_RATIO_MAX * p.monthly_income
    # strict <: savings of exactly 1 month does NOT trigger
    runway_critical = p.cash_savings < RUNWAY_MIN_MONTHS * p.monthly_expenses
    # strict >: debt of exactly 6× surplus does NOT trigger; needs positive surplus to be meaningful
    debt_overhang = surplus > 0 and p.hi_debt_amount > DEBT_OVERHANG_MULTIPLE * surplus

    evidence = [ev_surplus]
    if p.hi_debt_amount > 0:
        evidence.append(ev_interest)
    evidence.append(
        Evidence(
            claim=(
                f"Distress thresholds: surplus ≤ 0; debt interest > "
                f"{DEBT_SERVICE_RATIO_MAX:.0%} of income; savings < {RUNWAY_MIN_MONTHS} month "
                f"of expenses ({rupees(RUNWAY_MIN_MONTHS * p.monthly_expenses)}); debt > "
                f"{DEBT_OVERHANG_MULTIPLE}× monthly surplus"
            ),
            source="rules_engine",
            ref="calc:distress_thresholds",
            value=None,
        )
    )
    return DistressReport(
        surplus_nonpositive=surplus_nonpositive,
        debt_service_excessive=debt_service_excessive,
        runway_critical=runway_critical,
        debt_overhang=debt_overhang,
        evidence=evidence,
    )
