"""Deterministic allocation split (Phase 3a): fixed inputs → exact outputs,
gating on distress / surplus, and consistency with the ranking engine's split."""

from __future__ import annotations

import pytest

from app.config import ALLOCATION_SPLITS
from app.rules.allocation import compute_allocation, resolve_split
from app.schemas.profile import ProfileIn


def _profile(**kw) -> ProfileIn:
    base = dict(
        session_id="t",
        monthly_income=100_000,
        monthly_expenses=60_000,
        cash_savings=400_000,  # ~6.7 months runway → foundations met
        risk_tolerance="medium",
    )
    base.update(kw)
    return ProfileIn(**base)


class TestResolveSplit:
    @pytest.mark.parametrize("risk", ["low", "medium", "high"])
    def test_matches_config_when_no_adjustment(self, risk):
        eq, fx, gd = resolve_split(risk, 0)
        assert (eq, fx, gd) == ALLOCATION_SPLITS[risk]

    def test_gold_adjustment_shifts_equity_and_gold(self):
        eq, fx, gd = resolve_split("medium", 3)
        base_eq, base_fx, base_gd = ALLOCATION_SPLITS["medium"]
        assert gd == base_gd + 3 and eq == base_eq - 3 and fx == base_fx

    def test_adjustment_is_clamped(self):
        eq, fx, gd = resolve_split("high", 99)  # clamp to +5
        base_eq, _, base_gd = ALLOCATION_SPLITS["high"]
        assert gd == base_gd + 5 and eq == base_eq - 5


class TestComputeAllocation:
    def test_medium_split_amounts_sum_to_surplus(self):
        a = compute_allocation(_profile(), gold_adjustment_pts=0)
        assert a.available
        assert a.monthly_investable == 40_000
        assert [s.pct for s in a.slices] == [55, 30, 15]
        assert [s.kind for s in a.slices] == ["index", "bonds", "gold"]
        assert sum(s.monthly_amount for s in a.slices) == 40_000  # remainder reconciled
        assert [s.monthly_amount for s in a.slices] == [22_000, 12_000, 6_000]

    def test_percentages_total_100(self):
        for risk in ("low", "medium", "high"):
            a = compute_allocation(_profile(risk_tolerance=risk))
            assert sum(s.pct for s in a.slices) == 100

    def test_gold_regime_adjustment_reflected(self):
        a = compute_allocation(_profile(), gold_adjustment_pts=5)
        assert a.gold_adjustment_pts == 5
        assert a.slices[2].pct == 20 and a.slices[0].pct == 50  # gold up, equity down

    def test_unavailable_in_distress(self):
        # negative surplus → distress
        a = compute_allocation(_profile(monthly_income=40_000, monthly_expenses=60_000))
        assert not a.available and a.reason and not a.slices

    def test_unavailable_without_surplus(self):
        a = compute_allocation(_profile(monthly_income=60_000, monthly_expenses=60_000))
        assert not a.available and not a.slices

    def test_foundations_pending_flag_when_buffer_thin(self):
        # 2 months runway: past the 1-month distress floor but under the 3-month
        # target → not distress, split shown but flagged foundations_pending
        a = compute_allocation(_profile(cash_savings=120_000))
        assert a.available and a.foundations_pending and a.foundations_note

    def test_foundations_met_when_buffer_and_no_debt(self):
        a = compute_allocation(_profile())
        assert a.available and not a.foundations_pending
