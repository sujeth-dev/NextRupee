"""Explanation layer: valid fill, retry-on-garbage, guard rejection → fallback."""

from __future__ import annotations

import json

from app.llm.client import LLMClient, LLMUnavailable
from app.llm.explain import cap_confidence, generate_card
from app.rules.engine import rank
from app.schemas.profile import ProfileIn

PROFILE = ProfileIn(
    session_id="t", monthly_income=100_000, monthly_expenses=60_000,
    cash_savings=400_000, hi_debt_amount=120_000, hi_debt_apr=42,
)


def ranked_debt_card():
    return next(c for c in rank(PROFILE) if c.category == "debt")


class ScriptedClient(LLMClient):
    """Returns queued responses; records calls. No network, no sleeping."""

    def __init__(self, responses):
        super().__init__(api_key="test-key", sleeper=lambda s: None)
        self._responses = list(responses)
        self.calls = []

    def complete(self, system, user):
        self.calls.append((system, user))
        if not self._responses:
            raise LLMUnavailable("script exhausted")
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def good_prose(ranked):
    return json.dumps({
        "action": ranked.action,
        "rationale_chain": ["The interest arithmetic dominates every alternative."],
        "confidence_basis": "The comparison is arithmetic on stated numbers.",
        "invalidation_conditions": ["The debt is restructured to a lower rate."],
        "alternatives": ["Split between debt and buffer."],
        "opportunity_cost": ranked.opportunity_cost,
    })


class TestGenerateCard:
    def test_valid_response_produces_card(self):
        ranked = ranked_debt_card()
        card = generate_card(ranked, ScriptedClient([good_prose(ranked)]))
        assert card.degraded is False
        assert card.category == "debt"
        assert card.amount_range == ranked.amount_range  # engine numbers untouched
        assert card.evidence == ranked.evidence

    def test_unconfigured_client_falls_back(self):
        ranked = ranked_debt_card()
        card = generate_card(ranked, LLMClient(api_key=""))
        assert card.degraded is True
        assert card.amount_range == ranked.amount_range

    def test_garbage_then_valid_retries_once(self):
        ranked = ranked_debt_card()
        client = ScriptedClient(["not json at all", good_prose(ranked)])
        card = generate_card(ranked, client)
        assert card.degraded is False
        assert len(client.calls) == 2
        assert "rejected" in client.calls[1][1]  # error feedback passed back

    def test_two_bad_responses_fall_back(self):
        ranked = ranked_debt_card()
        card = generate_card(ranked, ScriptedClient(["nope", "still nope"]))
        assert card.degraded is True

    def test_invented_number_rejected_then_fallback(self):
        ranked = ranked_debt_card()
        bad = json.loads(good_prose(ranked))
        bad["opportunity_cost"] = "You would lose ₹9,87,654 next year."
        client = ScriptedClient([json.dumps(bad), json.dumps(bad)])
        card = generate_card(ranked, client)
        assert card.degraded is True
        assert "safety scanner" in client.calls[1][1]

    def test_instrument_name_rejected(self):
        ranked = ranked_debt_card()
        bad = json.loads(good_prose(ranked))
        bad["alternatives"] = ["Put it all in bitcoin instead."]
        card = generate_card(ranked, ScriptedClient([json.dumps(bad), json.dumps(bad)]))
        assert card.degraded is True

    def test_freshness_cap_applies(self):
        ranked = ranked_debt_card()
        card = generate_card(ranked, LLMClient(api_key=""), freshness_cap="medium")
        assert card.confidence == "medium"

    def test_code_fenced_json_accepted(self):
        ranked = ranked_debt_card()
        card = generate_card(ranked, ScriptedClient([f"```json\n{good_prose(ranked)}\n```"]))
        assert card.degraded is False


class TestCapConfidence:
    def test_ordering(self):
        assert cap_confidence("high", "medium") == "medium"
        assert cap_confidence("low", "high") == "low"
        assert cap_confidence("high", "high") == "high"
