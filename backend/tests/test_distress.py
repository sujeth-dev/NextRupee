"""Distress trigger boundary tests — every trigger at ±1 rupee (Phase 2 exit criteria)."""

from __future__ import annotations

from app.rules.distress import assess_distress
from app.schemas.profile import ProfileIn


def profile(**kw) -> ProfileIn:
    base = dict(
        session_id="t",
        monthly_income=100_000,
        monthly_expenses=60_000,
        cash_savings=200_000,
        hi_debt_amount=0,
        hi_debt_apr=0,
    )
    base.update(kw)
    return ProfileIn(**base)


class TestSurplusTrigger:
    def test_surplus_positive_by_one_rupee_no_trigger(self):
        r = assess_distress(profile(monthly_income=60_001))
        assert not r.surplus_nonpositive

    def test_surplus_exactly_zero_triggers(self):
        r = assess_distress(profile(monthly_income=60_000))
        assert r.surplus_nonpositive and r.in_distress

    def test_surplus_negative_by_one_rupee_triggers(self):
        r = assess_distress(profile(monthly_income=59_999))
        assert r.surplus_nonpositive


class TestDebtServiceTrigger:
    # interest > 40% of income triggers. income=100k ⇒ threshold 40k/month.
    # debt at 48% APR ⇒ monthly interest = debt * 0.04
    def test_interest_exactly_40pct_no_trigger(self):
        r = assess_distress(profile(hi_debt_amount=1_000_000, hi_debt_apr=48))  # 40,000
        assert not r.debt_service_excessive

    def test_interest_just_above_40pct_triggers(self):
        r = assess_distress(profile(hi_debt_amount=1_000_100, hi_debt_apr=48))  # 40,004
        assert r.debt_service_excessive and r.in_distress

    def test_no_debt_no_trigger(self):
        assert not assess_distress(profile()).debt_service_excessive


class TestRunwayTrigger:
    def test_savings_exactly_one_month_no_trigger(self):
        r = assess_distress(profile(cash_savings=60_000))
        assert not r.runway_critical

    def test_savings_one_rupee_short_triggers(self):
        r = assess_distress(profile(cash_savings=59_999))
        assert r.runway_critical and r.in_distress


class TestDebtOverhangTrigger:
    # surplus = 40,000 ⇒ threshold 240,000
    def test_debt_exactly_6x_surplus_no_trigger(self):
        r = assess_distress(profile(hi_debt_amount=240_000, hi_debt_apr=12))
        assert not r.debt_overhang

    def test_debt_one_rupee_over_6x_triggers(self):
        r = assess_distress(profile(hi_debt_amount=240_001, hi_debt_apr=12))
        assert r.debt_overhang and r.in_distress

    def test_overhang_requires_positive_surplus(self):
        r = assess_distress(profile(monthly_income=60_000, hi_debt_amount=1, hi_debt_apr=1))
        assert not r.debt_overhang  # surplus trigger owns this case
        assert r.surplus_nonpositive


class TestHealthyProfile:
    def test_no_triggers(self):
        r = assess_distress(profile())
        assert not r.in_distress
        assert r.evidence, "distress assessment must always carry evidence"
