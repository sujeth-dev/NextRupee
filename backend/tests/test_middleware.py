"""Rate limiter unit + integration tests."""

from __future__ import annotations

from app.middleware import RateLimiter


class TestRateLimiter:
    def test_allows_up_to_limit(self):
        rl = RateLimiter(limit_per_minute=3)
        assert all(rl.allow("ip1", now=float(i)) for i in range(3))
        assert not rl.allow("ip1", now=3.0)

    def test_window_slides(self):
        rl = RateLimiter(limit_per_minute=2)
        assert rl.allow("ip1", now=0.0)
        assert rl.allow("ip1", now=1.0)
        assert not rl.allow("ip1", now=2.0)
        assert rl.allow("ip1", now=61.5)  # first hit expired

    def test_keys_are_independent(self):
        rl = RateLimiter(limit_per_minute=1)
        assert rl.allow("a", now=0.0)
        assert rl.allow("b", now=0.0)
        assert not rl.allow("a", now=0.1)


def test_api_returns_429_over_limit(client, monkeypatch):
    from app import middleware

    monkeypatch.setattr(middleware, "limiter", middleware.RateLimiter(limit_per_minute=2))
    body = {"question": "why is gold expensive right now?"}
    assert client.post("/api/ask", json=body).status_code == 200
    assert client.post("/api/ask", json=body).status_code == 200
    assert client.post("/api/ask", json=body).status_code == 429


def test_health_not_rate_limited(client, monkeypatch):
    from app import middleware

    monkeypatch.setattr(middleware, "limiter", middleware.RateLimiter(limit_per_minute=1))
    for _ in range(5):
        assert client.get("/health").status_code == 200
