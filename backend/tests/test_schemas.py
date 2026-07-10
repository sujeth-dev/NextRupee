"""NBCA and profile schema contract tests (Phase 1 exit criteria)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas import NBCA, Evidence, ProfileIn


def make_nbca(**overrides) -> NBCA:
    base = {
        "action": "Move ₹60,000 toward clearing your highest-interest debt",
        "category": "debt",
        "amount_range": (50_000, 60_000),
        "rationale_chain": ["42% APR compounds faster than any asset class returns"],
        "evidence": [
            Evidence(
                claim="Credit card APR",
                source="rules_engine",
                ref="calc:debt_apr",
                value="42%",
            )
        ],
        "confidence": "high",
        "confidence_basis": "Guaranteed-return framing: prepayment beats all expected returns",
        "invalidation_conditions": ["Debt is restructured below 10% APR"],
        "alternatives": ["Split between debt and emergency fund"],
        "opportunity_cost": "Skipping gold purchase at seasonal premium",
    }
    base.update(overrides)
    return NBCA(**base)


class TestNBCA:
    def test_round_trip(self):
        card = make_nbca()
        assert NBCA.model_validate_json(card.model_dump_json()) == card

    def test_degraded_defaults_false(self):
        assert make_nbca().degraded is False

    @pytest.mark.parametrize("bad_range", [(10, 5), (-1, 5)])
    def test_amount_range_ordering(self, bad_range):
        with pytest.raises(ValidationError):
            make_nbca(amount_range=bad_range)

    @pytest.mark.parametrize(
        "field", ["rationale_chain", "evidence", "invalidation_conditions", "alternatives"]
    )
    def test_required_lists_nonempty(self, field):
        with pytest.raises(ValidationError):
            make_nbca(**{field: []})

    def test_category_is_closed_set(self):
        with pytest.raises(ValidationError):
            make_nbca(category="stocks")

    def test_evidence_source_closed_set(self):
        with pytest.raises(ValidationError):
            Evidence(claim="x", source="llm", ref="r")


class TestProfileIn:
    def test_float_money_normalised_to_int(self):
        p = ProfileIn(
            session_id="s1",
            monthly_income=80_000.6,
            monthly_expenses=50_000.4,
            cash_savings=100_000,
        )
        assert p.monthly_income == 80_001
        assert p.monthly_expenses == 50_000
        assert isinstance(p.cash_savings, int)

    def test_surplus_and_runway(self):
        p = ProfileIn(
            session_id="s1", monthly_income=80_000, monthly_expenses=50_000, cash_savings=100_000
        )
        assert p.monthly_surplus == 30_000
        assert p.months_runway == 2.0

    def test_zero_expenses_runway_is_inf(self):
        p = ProfileIn(session_id="s1", monthly_income=1, monthly_expenses=0, cash_savings=1)
        assert p.months_runway == float("inf")

    def test_negative_money_rejected(self):
        with pytest.raises(ValidationError):
            ProfileIn(
                session_id="s1", monthly_income=-1, monthly_expenses=0, cash_savings=0
            )

    def test_apr_bounds(self):
        with pytest.raises(ValidationError):
            ProfileIn(
                session_id="s1",
                monthly_income=1,
                monthly_expenses=1,
                cash_savings=1,
                hi_debt_apr=101,
            )
