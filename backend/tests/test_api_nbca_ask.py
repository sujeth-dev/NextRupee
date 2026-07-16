"""End-to-end API tests for /api/nbca and /api/ask (offline: deterministic paths)."""

from __future__ import annotations

PROFILE = {
    "session_id": "hero",
    "monthly_income": 100000,
    "monthly_expenses": 60000,
    "cash_savings": 400000,
    "hi_debt_amount": 120000,
    "hi_debt_apr": 42,
    "dependents": False,
    "term_insurance": True,
    "risk_tolerance": "medium",
    "goals": ["diwali_gold"],
}


class TestNBCAEndpoint:
    def test_inline_profile_returns_ranked_cards(self, client):
        r = client.post("/api/nbca", json={"profile": PROFILE})
        assert r.status_code == 200
        body = r.json()
        assert body["cards"], "cards expected"
        assert body["cards"][0]["category"] == "debt"  # hero scenario
        assert body["in_distress"] is False
        # offline mode: every card is the deterministic fallback and says so
        assert body["degraded_count"] == len(body["cards"])
        assert body["model"] == "deterministic-fallback"

    def test_session_id_path(self, client):
        client.post("/api/profile", json=PROFILE)
        r = client.post("/api/nbca", json={"session_id": "hero"})
        assert r.status_code == 200

    def test_unknown_session_404(self, client):
        assert client.post("/api/nbca", json={"session_id": "ghost"}).status_code == 404

    def test_neither_input_422(self, client):
        assert client.post("/api/nbca", json={}).status_code == 422

    def test_distress_profile_flagged_no_invest(self, client):
        distressed = {**PROFILE, "session_id": "d1", "monthly_income": 50000}
        r = client.post("/api/nbca", json={"profile": distressed})
        body = r.json()
        assert body["in_distress"] is True
        assert all(c["category"] != "invest_allocation" for c in body["cards"])

    def test_cards_carry_evidence_refs(self, client):
        r = client.post("/api/nbca", json={"profile": PROFILE})
        for card in r.json()["cards"]:
            assert card["evidence"]
            for ev in card["evidence"]:
                assert ev["ref"]


class TestAskEndpoint:
    def test_instrument_question_refused(self, client):
        r = client.post("/api/ask", json={"question": "which stock should I buy?"})
        assert r.status_code == 200
        body = r.json()
        assert body["refused"] is True
        assert body["headline"] == "NextRupee doesn't pick stocks, funds, or coins."
        assert "doesn't recommend specific stocks" in body["detail"]
        # legacy field stays populated: headline + detail
        assert body["answer"].startswith(body["headline"])
        assert body["detail"] in body["answer"]

    def test_gold_question_grounded_fallback(self, client):
        r = client.post("/api/ask", json={"question": "why is gold expensive right now?"})
        body = r.json()
        assert body["refused"] is False
        assert body["degraded"] is True  # offline mode
        assert body["citations"], "chunk citations expected"
        assert "#" in body["citations"][0]
        # split response: plain one-liner + cited detail, answer = concatenation
        assert body["headline"]
        assert "[" not in body["headline"], "headline must carry no citations"
        assert "[" in body["detail"], "detail must carry citations"
        assert body["answer"] == f'{body["headline"]}\n\n{body["detail"]}'

    def test_short_question_422(self, client):
        assert client.post("/api/ask", json={"question": "hi"}).status_code == 422
