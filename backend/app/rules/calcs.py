"""Pure financial calculations. Every function returns (value, Evidence).

This module owns ALL arithmetic in the product (Master Doc non-negotiable #1).
Each calc has a stable id (`calc:<name>`) referenced by NBCA evidence.
"""

from __future__ import annotations

from app.schemas.nbca import Evidence
from app.schemas.profile import ProfileIn


def _ev(name: str, claim: str, value: str) -> Evidence:
    return Evidence(claim=claim, source="rules_engine", ref=f"calc:{name}", value=value)


def rupees(n: int) -> str:
    """Indian-style grouping: 12,34,567."""
    s = str(abs(int(n)))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts) + "," + tail
    return ("-" if n < 0 else "") + "₹" + s


def monthly_surplus(p: ProfileIn) -> tuple[int, Evidence]:
    v = p.monthly_income - p.monthly_expenses
    return v, _ev(
        "monthly_surplus",
        f"Monthly surplus = income {rupees(p.monthly_income)} − expenses "
        f"{rupees(p.monthly_expenses)}",
        rupees(v),
    )


def months_runway(p: ProfileIn) -> tuple[float, Evidence]:
    v = p.cash_savings / p.monthly_expenses if p.monthly_expenses > 0 else float("inf")
    shown = "∞" if v == float("inf") else f"{v:.1f} months"
    return v, _ev(
        "months_runway",
        f"Cash runway = savings {rupees(p.cash_savings)} ÷ monthly expenses "
        f"{rupees(p.monthly_expenses)}",
        shown,
    )


def debt_monthly_interest(p: ProfileIn) -> tuple[int, Evidence]:
    v = round(p.hi_debt_amount * (p.hi_debt_apr / 100) / 12)
    return v, _ev(
        "debt_monthly_interest",
        f"Monthly interest on {rupees(p.hi_debt_amount)} at {p.hi_debt_apr:g}% APR",
        rupees(v),
    )


def debt_annual_interest(p: ProfileIn) -> tuple[int, Evidence]:
    v = round(p.hi_debt_amount * p.hi_debt_apr / 100)
    return v, _ev(
        "debt_annual_interest",
        f"Interest paid over one year on {rupees(p.hi_debt_amount)} at {p.hi_debt_apr:g}% APR",
        rupees(v),
    )


def emergency_fund_gap(p: ProfileIn, target_months: int) -> tuple[int, Evidence]:
    v = max(0, target_months * p.monthly_expenses - p.cash_savings)
    return v, _ev(
        f"ef_gap_{target_months}m",
        f"Gap to a {target_months}-month emergency fund "
        f"({target_months} × {rupees(p.monthly_expenses)} − {rupees(p.cash_savings)})",
        rupees(v),
    )


def term_cover_target(p: ProfileIn) -> tuple[int, Evidence]:
    from app.config import TERM_COVER_INCOME_MULTIPLE

    v = TERM_COVER_INCOME_MULTIPLE * 12 * p.monthly_income
    return v, _ev(
        "term_cover_target",
        f"Term cover heuristic = {TERM_COVER_INCOME_MULTIPLE} × annual income "
        f"({rupees(12 * p.monthly_income)})",
        rupees(v),
    )


def deployable_cash(p: ProfileIn) -> tuple[int, Evidence]:
    """Cash above the 3-month emergency floor, available to deploy this month."""
    from app.config import EMERGENCY_FUND_STAGE1_MONTHS

    floor = EMERGENCY_FUND_STAGE1_MONTHS * p.monthly_expenses
    v = max(0, p.cash_savings - floor) + max(0, p.monthly_income - p.monthly_expenses)
    return v, _ev(
        "deployable_cash",
        f"Deployable = savings above {EMERGENCY_FUND_STAGE1_MONTHS}-month floor "
        f"({rupees(max(0, p.cash_savings - floor))}) + this month's surplus",
        rupees(v),
    )
