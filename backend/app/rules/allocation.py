"""Deterministic asset-allocation split (Phase 3a).

"Where the money goes" — the percentage split of investable surplus across
household asset classes. Built on the SAME principled buckets the ranking engine
already uses for its invest_allocation card (ALLOCATION_SPLITS by risk tolerance,
gold share regime-adjusted), so the panel and the card never disagree. Each of the
three engine buckets is presented as a slice mapped to the instrument classes a
household actually uses, with an icon key the frontend renders.

Gated: an allocation is offered only when the base is secure — never in distress,
never without a positive monthly surplus. When the buffer or high-interest debt is
still being handled the split is still shown (it is where surplus goes *once*
foundations are met) but flagged foundations_pending so the UI can say so.

Pure and deterministic: same profile + same gold adjustment ⇒ identical split.
No randomness, no clock, no I/O — unit-tested with fixed fixtures.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.config import (
    ALLOCATION_SPLITS,
    EMERGENCY_FUND_STAGE1_MONTHS,
    EXPECTED_RETURNS,
    GOLD_REGIME_ADJUSTMENT_MAX,
    HIGH_INTEREST_APR_MIN,
)
from app.rules import calcs
from app.rules.distress import assess_distress
from app.schemas.profile import ProfileIn

RISK_LABEL = {"low": "Steady", "medium": "Balanced", "high": "Growth"}


class AllocationSlice(BaseModel):
    kind: str          # InstrumentIcon key on the frontend
    label: str         # plain-language class name
    pct: int           # whole-percent share of investable surplus
    monthly_amount: int  # rupees/month into this slice
    note: str          # one-line "what goes here"
    expected_return_pct: float


class Allocation(BaseModel):
    available: bool
    reason: str | None = None          # why unavailable (distress / no surplus)
    monthly_investable: int = 0
    risk_tolerance: str = "medium"
    risk_label: str = ""
    gold_adjustment_pts: int = 0
    foundations_pending: bool = False  # buffer/debt still being filled
    foundations_note: str | None = None
    slices: list[AllocationSlice] = []


def resolve_split(risk_tolerance: str, gold_adjustment_pts: int) -> tuple[int, int, int]:
    """(equity, fixed_income, gold) whole-percent split — identical formula to the
    ranking engine's invest_allocation card, so the two can never drift."""
    adj = max(-GOLD_REGIME_ADJUSTMENT_MAX, min(GOLD_REGIME_ADJUSTMENT_MAX, gold_adjustment_pts))
    equity, fixed_income, gold = ALLOCATION_SPLITS[risk_tolerance]
    return equity - adj, fixed_income, gold + adj


def _amounts(surplus: int, pcts: tuple[int, int, int]) -> tuple[int, int, int]:
    """Split rupees by pcts, giving any rounding remainder to the largest slice so
    the parts always sum back to the whole."""
    raw = [round(surplus * p / 100) for p in pcts]
    remainder = surplus - sum(raw)
    if remainder and surplus > 0:
        raw[pcts.index(max(pcts))] += remainder
    return raw[0], raw[1], raw[2]


def compute_allocation(p: ProfileIn, gold_adjustment_pts: int = 0) -> Allocation:
    surplus, _ = calcs.monthly_surplus(p)

    if assess_distress(p).in_distress:
        return Allocation(
            available=False,
            reason="Your base needs securing before investing — clear the distress signals first.",
        )
    if surplus <= 0:
        return Allocation(
            available=False,
            reason="No monthly surplus to invest yet — free up cash flow first.",
        )

    equity_pct, fixed_pct, gold_pct = resolve_split(p.risk_tolerance, gold_adjustment_pts)
    eq_amt, fx_amt, gd_amt = _amounts(surplus, (equity_pct, fixed_pct, gold_pct))
    adj = gold_pct - ALLOCATION_SPLITS[p.risk_tolerance][2]

    runway, _ = calcs.months_runway(p)
    foundations_pending = (
        runway < EMERGENCY_FUND_STAGE1_MONTHS
        or (p.hi_debt_amount > 0 and p.hi_debt_apr >= HIGH_INTEREST_APR_MIN)
    )

    slices = [
        AllocationSlice(
            kind="index",
            label="Equity — via index funds",
            pct=equity_pct,
            monthly_amount=eq_amt,
            note="Low-cost Nifty/Sensex index funds — the growth engine, for money you won't "
            "touch for 7+ years.",
            expected_return_pct=EXPECTED_RETURNS["equity"],
        ),
        AllocationSlice(
            kind="bonds",
            label="Fixed income — FD, bonds, PPF/EPF",
            pct=fixed_pct,
            monthly_amount=fx_amt,
            note="Deposits, debt funds and small-savings — the steady, capital-safe ballast.",
            expected_return_pct=EXPECTED_RETURNS["fixed_income"],
        ),
        AllocationSlice(
            kind="gold",
            label="Gold",
            pct=gold_pct,
            monthly_amount=gd_amt,
            note="A small hedge that holds up when markets and the rupee wobble — not a growth bet."
            + (f" Shifted {adj:+d} pt by today's gold-regime signal." if adj else ""),
            expected_return_pct=EXPECTED_RETURNS["gold"],
        ),
    ]

    return Allocation(
        available=True,
        monthly_investable=surplus,
        risk_tolerance=p.risk_tolerance,
        risk_label=RISK_LABEL.get(p.risk_tolerance, p.risk_tolerance.title()),
        gold_adjustment_pts=adj,
        foundations_pending=foundations_pending,
        foundations_note=(
            "Fill your emergency buffer and clear high-interest debt first — this is the split "
            "for what's left to invest each month."
            if foundations_pending
            else None
        ),
        slices=slices,
    )
