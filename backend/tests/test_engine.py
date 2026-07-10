"""Rules engine ranking tests: hierarchy order, amounts, evidence, properties."""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from app.rules.engine import rank
from app.schemas.profile import ProfileIn


def profile(**kw) -> ProfileIn:
    base = dict(
        session_id="t",
        monthly_income=100_000,
        monthly_expenses=60_000,
        cash_savings=400_000,  # ~6.7 months runway
        hi_debt_amount=0,
        hi_debt_apr=0,
        dependents=False,
        term_insurance=True,
        risk_tolerance="medium",
    )
    base.update(kw)
    return ProfileIn(**base)


class TestNormalHierarchy:
    def test_healthy_profile_gets_invest_card_only(self):
        cards = rank(profile())
        assert [c.category for c in cards] == ["invest_allocation"]

    def test_hero_scenario_debt_beats_invest(self):
        """October, ₹60K spare, credit card at 42% APR: debt prepay must rank first."""
        cards = rank(
            profile(cash_savings=400_000, hi_debt_amount=120_000, hi_debt_apr=42)
        )
        assert cards[0].category == "debt"
        assert "42" in cards[0].action
        assert any("guaranteed" in step.lower() for step in cards[0].rationale_chain)

    def test_full_stack_ordering(self):
        """EF(<3m) > insurance > debt > invest for a profile needing all four."""
        cards = rank(
            profile(
                cash_savings=100_000,  # 1.67 months
                hi_debt_amount=100_000,
                hi_debt_apr=18,
                dependents=True,
                term_insurance=False,
            )
        )
        cats = [c.category for c in cards]
        assert cats == ["emergency_fund", "insurance", "debt", "invest_allocation"]

    def test_ef_priority_scales_with_gap(self):
        low_runway = rank(profile(cash_savings=30_000))[0]
        higher_runway = rank(profile(cash_savings=150_000))[0]
        assert low_runway.priority_score > higher_runway.priority_score

    def test_ef_stage2_between_3_and_6_months(self):
        cards = rank(profile(cash_savings=240_000))  # 4 months
        cats = [c.category for c in cards]
        assert "emergency_fund" in cats
        ef = next(c for c in cards if c.category == "emergency_fund")
        assert "six months" in ef.action
        assert ef.amount_range[1] == 6 * 60_000 - 240_000

    def test_low_apr_debt_not_prepaid(self):
        cards = rank(profile(hi_debt_amount=100_000, hi_debt_apr=8))
        assert all(c.category != "debt" for c in cards)

    def test_apr_exactly_10_is_prepaid(self):
        cards = rank(profile(hi_debt_amount=100_000, hi_debt_apr=10))
        assert any(c.category == "debt" for c in cards)

    def test_allocation_split_by_risk(self):
        for risk, expected in [("low", "35/50/15"), ("medium", "55/30/15"), ("high", "70/20/10")]:
            cards = rank(profile(risk_tolerance=risk))
            invest = next(c for c in cards if c.category == "invest_allocation")
            split_ev = next(e for e in invest.evidence if e.ref == "calc:allocation_split")
            assert split_ev.value == expected

    def test_gold_adjustment_shifts_split_bounded(self):
        invest = next(
            c for c in rank(profile(), gold_adjustment_pts=5) if c.category == "invest_allocation"
        )
        ev = next(e for e in invest.evidence if e.ref == "calc:allocation_split")
        assert ev.value == "50/30/20"
        # beyond the bound is clamped
        invest2 = next(
            c for c in rank(profile(), gold_adjustment_pts=99) if c.category == "invest_allocation"
        )
        ev2 = next(e for e in invest2.evidence if e.ref == "calc:allocation_split")
        assert ev2.value == "50/30/20"

    def test_ranks_are_sequential(self):
        cards = rank(
            profile(cash_savings=100_000, hi_debt_amount=100_000, hi_debt_apr=18,
                    dependents=True, term_insurance=False)
        )
        assert [c.rank for c in cards] == list(range(1, len(cards) + 1))


class TestDistressMode:
    def test_negative_surplus_suppresses_invest_and_leads_with_stabilize(self):
        cards = rank(profile(monthly_income=50_000, hi_debt_amount=50_000, hi_debt_apr=36))
        assert cards[0].category == "stabilize"
        assert all(c.category != "invest_allocation" for c in cards)

    def test_distress_order_stabilize_runway_debt(self):
        cards = rank(
            profile(
                monthly_income=50_000,  # deficit
                cash_savings=10_000,    # < 1 month
                hi_debt_amount=80_000,
                hi_debt_apr=40,
            )
        )
        assert [c.category for c in cards] == ["stabilize", "emergency_fund", "debt"]

    def test_distress_debt_card_is_restructure_not_prepay(self):
        cards = rank(profile(monthly_income=50_000, hi_debt_amount=80_000, hi_debt_apr=40))
        debt = next(c for c in cards if c.category == "debt")
        assert "restructure" in debt.action.lower() or "Restructure" in debt.action


class TestEvidenceContract:
    def test_every_card_has_traceable_evidence(self):
        cards = rank(
            profile(cash_savings=100_000, hi_debt_amount=100_000, hi_debt_apr=18,
                    dependents=True, term_insurance=False)
        )
        for card in cards:
            assert card.evidence, card.category
            for ev in card.evidence:
                assert ev.source == "rules_engine"
                assert ev.ref.startswith("calc:")

    def test_fallback_card_is_valid_nbca_and_degraded(self):
        card = rank(profile())[0].to_fallback_nbca()
        assert card.degraded is True
        assert card.evidence and card.invalidation_conditions and card.alternatives


# --- property tests (Phase 2 exit criteria) -------------------------------------------

profiles = st.builds(
    ProfileIn,
    session_id=st.just("prop"),
    monthly_income=st.integers(0, 2_000_000),
    monthly_expenses=st.integers(0, 2_000_000),
    cash_savings=st.integers(0, 50_000_000),
    hi_debt_amount=st.integers(0, 50_000_000),
    hi_debt_apr=st.floats(0, 60, allow_nan=False),
    dependents=st.booleans(),
    term_insurance=st.booleans(),
    risk_tolerance=st.sampled_from(["low", "medium", "high"]),
)


@settings(max_examples=200, deadline=None)
@given(profiles, st.integers(-10, 10))
def test_property_reproducible(p: ProfileIn, adj: int):
    """Same profile in ⇒ same ranking out."""
    a = [c.model_dump() for c in rank(p, adj)]
    b = [c.model_dump() for c in rank(p, adj)]
    assert a == b


@settings(max_examples=300, deadline=None)
@given(profiles)
def test_property_no_invest_under_distress(p: ProfileIn):
    """No invest_allocation card may ever appear when any distress trigger fires."""
    from app.rules.distress import assess_distress

    if assess_distress(p).in_distress:
        assert all(c.category != "invest_allocation" for c in rank(p))


@settings(max_examples=200, deadline=None)
@given(profiles, st.integers(-10, 10))
def test_property_amount_ranges_valid(p: ProfileIn, adj: int):
    for c in rank(p, adj):
        lo, hi = c.amount_range
        assert 0 <= lo <= hi
