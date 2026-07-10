"""Deterministic ranking engine (Master Doc §5).

Owns ranking and ALL math. Emits fully-populated RankedActions whose fields
double as the deterministic fallback card (Master Doc §4). The LLM only ever
rewrites prose around these numbers — never the numbers themselves.

Reproducibility contract: same profile + same gold adjustment in ⇒ identical
ranking out. No randomness, no clock reads, no I/O.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.config import (
    ALLOCATION_SPLITS,
    EMERGENCY_FUND_STAGE1_MONTHS,
    EMERGENCY_FUND_STAGE2_MONTHS,
    EXPECTED_RETURNS,
    GOLD_REGIME_ADJUSTMENT_MAX,
    HIGH_INTEREST_APR_MIN,
)
from app.rules import calcs
from app.rules.calcs import rupees
from app.rules.distress import DistressReport, assess_distress
from app.schemas.nbca import NBCA, Category, Confidence, Evidence
from app.schemas.profile import ProfileIn


class RankedAction(BaseModel):
    """Engine output: one fully-computed recommendation, rank-ordered."""

    rank: int
    category: Category
    action: str
    amount_range: tuple[int, int]
    priority_score: float
    rationale_chain: list[str]
    evidence: list[Evidence]
    confidence: Confidence
    confidence_basis: str
    invalidation_conditions: list[str]
    alternatives: list[str]
    opportunity_cost: str

    def to_fallback_nbca(self) -> NBCA:
        """Deterministic card used when the LLM output is rejected twice."""
        return NBCA(
            action=self.action,
            category=self.category,
            amount_range=self.amount_range,
            rationale_chain=self.rationale_chain,
            evidence=self.evidence,
            confidence=self.confidence,
            confidence_basis=self.confidence_basis,
            invalidation_conditions=self.invalidation_conditions,
            alternatives=self.alternatives,
            opportunity_cost=self.opportunity_cost,
            degraded=True,
        )


def _clamp_range(lo: int, hi: int) -> tuple[int, int]:
    lo, hi = max(0, lo), max(0, hi)
    return (min(lo, hi), hi)


# --- distress-mode cards -------------------------------------------------------------


def _distress_cards(p: ProfileIn, report: DistressReport) -> list[RankedAction]:
    cards: list[RankedAction] = []
    surplus, _ = calcs.monthly_surplus(p)

    if report.surplus_nonpositive or report.debt_service_excessive:
        deficit = max(0, -surplus)
        interest, ev_interest = calcs.debt_monthly_interest(p)
        target = deficit if deficit > 0 else interest
        cards.append(
            RankedAction(
                rank=0,
                category="stabilize",
                action="Stabilize cash flow before anything else: reduce outgo or raise income "
                f"by about {rupees(max(target, 1))} a month",
                amount_range=_clamp_range(target, target),
                priority_score=100.0,
                rationale_chain=[
                    "Money out currently outpaces (or is consumed by) obligations",
                    "No allocation strategy works while the monthly base is negative",
                    "Restoring positive surplus unlocks every later step",
                ],
                evidence=report.evidence + ([ev_interest] if p.hi_debt_amount > 0 else []),
                confidence="high",
                confidence_basis="Direct arithmetic on your stated income and expenses",
                invalidation_conditions=[
                    "Monthly surplus turns positive and debt interest falls below "
                    "40% of income"
                ],
                alternatives=["Negotiate fixed obligations before cutting variable spend"],
                opportunity_cost="Every stabilization month delays wealth-building, but skipping "
                "it makes losses compound instead",
            )
        )

    if report.runway_critical:
        gap, ev_gap = calcs.emergency_fund_gap(p, 1)
        cards.append(
            RankedAction(
                rank=0,
                category="emergency_fund",
                action=f"Build a one-month cash buffer: set aside {rupees(gap)} before any "
                "investing",
                amount_range=_clamp_range(min(gap, max(surplus, 0)) or gap, gap),
                priority_score=90.0,
                rationale_chain=[
                    "Savings currently cover less than one month of expenses",
                    "A single missed pay-cycle would force new borrowing",
                    "One month of buffer is the minimum shock absorber",
                ],
                evidence=[ev_gap, *report.evidence],
                confidence="high",
                confidence_basis="Direct arithmetic on your stated savings and expenses",
                invalidation_conditions=[
                    f"Cash savings reach {rupees(p.monthly_expenses)} (one month of expenses)"
                ],
                alternatives=["Park the buffer in a sweep-in deposit for liquidity"],
                opportunity_cost="Buffer cash earns little, but borrowing at credit-card rates "
                "when shocked costs far more",
            )
        )

    if p.hi_debt_amount > 0:
        annual, ev_annual = calcs.debt_annual_interest(p)
        cards.append(
            RankedAction(
                rank=0,
                category="debt",
                action="Restructure the high-interest debt: negotiate a lower rate, consolidate, "
                "or convert to a term loan",
                amount_range=_clamp_range(0, p.hi_debt_amount),
                priority_score=80.0,
                rationale_chain=[
                    f"At {p.hi_debt_apr:g}% APR this debt costs {rupees(annual)} a year",
                    "In distress mode, prepayment capacity is limited, so the rate itself "
                    "is the lever",
                    "Cutting the rate shrinks the hole while cash flow recovers",
                ],
                evidence=[ev_annual, *report.evidence],
                confidence="high",
                confidence_basis="Interest arithmetic on your stated balance and APR",
                invalidation_conditions=["Debt APR falls below 10%", "Balance is cleared"],
                alternatives=["Balance transfer to a lower-APR line", "EMI conversion"],
                opportunity_cost="Time spent negotiating vs. interest accruing daily at "
                f"{p.hi_debt_apr:g}% APR",
            )
        )

    return cards


# --- normal-mode cards ---------------------------------------------------------------


def _normal_cards(p: ProfileIn, gold_adjustment_pts: int) -> list[RankedAction]:
    cards: list[RankedAction] = []
    surplus, ev_surplus = calcs.monthly_surplus(p)
    runway, ev_runway = calcs.months_runway(p)

    # 1. Emergency fund to 3 months — priority ∝ (3 − months_runway)
    if runway < EMERGENCY_FUND_STAGE1_MONTHS:
        gap, ev_gap = calcs.emergency_fund_gap(p, EMERGENCY_FUND_STAGE1_MONTHS)
        score = 50.0 + 10.0 * (EMERGENCY_FUND_STAGE1_MONTHS - min(runway, 3))
        cards.append(
            RankedAction(
                rank=0,
                category="emergency_fund",
                action=f"Grow your emergency fund to three months of expenses — "
                f"{rupees(gap)} to go",
                amount_range=_clamp_range(min(gap, max(surplus, 0)) or gap, gap),
                priority_score=round(score, 2),
                rationale_chain=[
                    f"Runway is {runway:.1f} months; three months is the resilience floor",
                    "Every rupee of buffer prevents forced borrowing or forced selling",
                    "This must exist before market risk is taken",
                ],
                evidence=[ev_runway, ev_gap, ev_surplus],
                confidence="high",
                confidence_basis="Direct arithmetic on your stated savings and expenses",
                invalidation_conditions=[
                    f"Savings reach {rupees(EMERGENCY_FUND_STAGE1_MONTHS * p.monthly_expenses)} "
                    "(three months of expenses)"
                ],
                alternatives=["Split monthly surplus between buffer and debt if both apply"],
                opportunity_cost="Buffer cash trails inflation, but its option value during a "
                "shock exceeds the drag",
            )
        )

    # 2. Insurance gap
    if p.dependents and not p.term_insurance:
        cover, ev_cover = calcs.term_cover_target(p)
        cards.append(
            RankedAction(
                rank=0,
                category="insurance",
                action=f"Put term life cover of about {rupees(cover)} in place for your "
                "dependents",
                amount_range=_clamp_range(cover, cover),
                priority_score=45.0,
                rationale_chain=[
                    "People depend on your income and no term cover exists",
                    "An uninsured earner is the single largest unpriced risk in the plan",
                    "Cover of ~15× annual income replaces the income stream",
                ],
                evidence=[ev_cover],
                confidence="high",
                confidence_basis="Standard cover heuristic applied to your stated income",
                invalidation_conditions=[
                    "Adequate term cover is purchased",
                    "No one depends on your income",
                ],
                alternatives=["Employer group cover as a stopgap (verify portability)"],
                opportunity_cost="Premium outlay vs. dependents carrying the full income risk",
            )
        )

    # 3. High-interest debt prepay — guaranteed-return framing
    if p.hi_debt_amount > 0 and p.hi_debt_apr >= HIGH_INTEREST_APR_MIN:
        annual, ev_annual = calcs.debt_annual_interest(p)
        deploy, ev_deploy = calcs.deployable_cash(p)
        best_alt = max(EXPECTED_RETURNS.values())
        edge = p.hi_debt_apr - best_alt
        cards.append(
            RankedAction(
                rank=0,
                category="debt",
                action=f"Prepay the {p.hi_debt_apr:g}% APR debt — every rupee here earns a "
                f"guaranteed {p.hi_debt_apr:g}%",
                amount_range=_clamp_range(min(deploy, p.hi_debt_amount), p.hi_debt_amount),
                # sub-score varies with the APR edge but stays inside the tier band
                # (< 45): fixed hierarchy means tiers must never cross.
                priority_score=round(40.0 + min(max(edge, 0.0), 45.0) / 10.0, 2),
                rationale_chain=[
                    f"Prepayment returns {p.hi_debt_apr:g}% guaranteed, tax-free",
                    f"The best long-run asset-class expectation is ~{best_alt:g}% — and it is "
                    "not guaranteed",
                    f"Carrying this balance costs {rupees(annual)} a year",
                ],
                evidence=[
                    ev_annual,
                    ev_deploy,
                    Evidence(
                        claim="Expected long-run returns used for comparison: "
                        + ", ".join(f"{k} {v:g}%" for k, v in EXPECTED_RETURNS.items()),
                        source="rules_engine",
                        ref="calc:expected_returns_table",
                        value=None,
                    ),
                ],
                confidence="high",
                confidence_basis="APR vs. expected-return comparison is arithmetic, not forecast",
                invalidation_conditions=[
                    "Debt APR drops below 10%",
                    "Balance is cleared",
                ],
                alternatives=["Restructure to a lower rate if prepayment capacity is thin"],
                opportunity_cost=f"Rupees sent to debt skip the market — but {p.hi_debt_apr:g}% "
                "guaranteed beats every expected alternative",
            )
        )

    # 4. Emergency fund 3 → 6 months
    if EMERGENCY_FUND_STAGE1_MONTHS <= runway < EMERGENCY_FUND_STAGE2_MONTHS:
        gap, ev_gap = calcs.emergency_fund_gap(p, EMERGENCY_FUND_STAGE2_MONTHS)
        cards.append(
            RankedAction(
                rank=0,
                category="emergency_fund",
                action=f"Extend your emergency fund from three to six months — "
                f"{rupees(gap)} to go",
                amount_range=_clamp_range(min(gap, max(surplus, 0)) or gap, gap),
                priority_score=30.0,
                rationale_chain=[
                    f"Runway is {runway:.1f} months; six months covers a job-loss cycle",
                    "Deeper buffer permits higher-risk allocation later",
                ],
                evidence=[ev_runway, ev_gap],
                confidence="high",
                confidence_basis="Direct arithmetic on your stated savings and expenses",
                invalidation_conditions=[
                    f"Savings reach {rupees(EMERGENCY_FUND_STAGE2_MONTHS * p.monthly_expenses)} "
                    "(six months of expenses)"
                ],
                alternatives=["Ladder the second tranche into short-duration deposits"],
                opportunity_cost="Slightly lower expected return than investing the same rupees",
            )
        )

    # 5. Invest surplus by risk-tolerance split, gold share regime-adjusted (bounded)
    if surplus > 0:
        adj = max(-GOLD_REGIME_ADJUSTMENT_MAX, min(GOLD_REGIME_ADJUSTMENT_MAX, gold_adjustment_pts))
        equity, fixed_income, gold = ALLOCATION_SPLITS[p.risk_tolerance]
        gold += adj
        equity -= adj
        ev_split = Evidence(
            claim=f"Allocation for {p.risk_tolerance} risk tolerance: {equity}% equity, "
            f"{fixed_income}% fixed income, {gold}% gold"
            + (f" (gold shifted {adj:+d} pts by the gold regime signal)" if adj else ""),
            source="rules_engine",
            ref="calc:allocation_split",
            value=f"{equity}/{fixed_income}/{gold}",
        )
        cards.append(
            RankedAction(
                rank=0,
                category="invest_allocation",
                action=f"Invest your monthly surplus of {rupees(surplus)} as {equity}% equity, "
                f"{fixed_income}% fixed income, {gold}% gold (asset classes, not instruments)",
                amount_range=_clamp_range(surplus, surplus),
                priority_score=20.0,
                rationale_chain=[
                    "Foundations (buffer, cover, expensive debt) are handled",
                    f"A {p.risk_tolerance}-risk split balances growth against drawdown you can "
                    "tolerate",
                    "Asset-class level keeps the decision structural, not speculative",
                ],
                evidence=[ev_surplus, ev_split],
                confidence="medium",
                confidence_basis="Split follows your stated risk tolerance; market outcomes "
                "are not guaranteed",
                invalidation_conditions=[
                    "Risk tolerance changes",
                    "Any distress trigger fires (surplus, runway, debt service)",
                ],
                alternatives=["Step allocation in over 3–6 months rather than at once"],
                opportunity_cost="Holding the surplus as cash instead cedes expected real "
                "returns to inflation",
            )
        )

    return cards


# --- public API ----------------------------------------------------------------------


def rank(p: ProfileIn, gold_adjustment_pts: int = 0) -> list[RankedAction]:
    """Rank next best courses of action. Deterministic; see module docstring."""
    report = assess_distress(p)
    if report.in_distress:
        cards = _distress_cards(p, report)
    else:
        cards = _normal_cards(p, gold_adjustment_pts)
    cards.sort(key=lambda c: -c.priority_score)
    for i, card in enumerate(cards):
        card.rank = i + 1
    return cards
