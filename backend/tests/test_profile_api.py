"""Profile intake API tests (Phase 1 exit criteria: POST → stored, versioned)."""

from __future__ import annotations

PROFILE = {
    "session_id": "sess-abc",
    "monthly_income": 80000,
    "monthly_expenses": 50000,
    "cash_savings": 100000,
    "hi_debt_amount": 120000,
    "hi_debt_apr": 42,
    "dependents": True,
    "term_insurance": False,
    "risk_tolerance": "medium",
    "goals": ["diwali_gold"],
}


def test_post_profile_stores_and_returns_row(client):
    r = client.post("/api/profile", json=PROFILE)
    assert r.status_code == 201
    body = r.json()
    assert body["version"] == 1
    assert body["monthly_income"] == 80000
    assert "id" in body and "created_at" in body


def test_resubmission_appends_new_version(client):
    client.post("/api/profile", json=PROFILE)
    r2 = client.post("/api/profile", json={**PROFILE, "cash_savings": 150000})
    assert r2.json()["version"] == 2
    latest = client.get(f"/api/profile/{PROFILE['session_id']}").json()
    assert latest["version"] == 2
    assert latest["cash_savings"] == 150000


def test_unknown_session_404(client):
    assert client.get("/api/profile/nope").status_code == 404


def test_invalid_payload_422(client):
    assert client.post("/api/profile", json={"session_id": "x"}).status_code == 422


def test_health_reports_db(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["db"] == "ok"
