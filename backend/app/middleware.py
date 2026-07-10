"""Production hardening middleware (Master Doc §10) — portfolio-sized, deliberately minimal.

- Sliding-window rate limit per client IP on /api/* (default 10 req/min).
- In-memory: one Render free instance means one process; a real deployment
  would move this to Redis, noted in README known-limitations.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse

from app.config import settings

_WINDOW_S = 60.0


class RateLimiter:
    def __init__(self, limit_per_minute: int | None = None) -> None:
        self.limit = limit_per_minute or settings.rate_limit_per_minute
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str, now: float | None = None) -> bool:
        now = now if now is not None else time.monotonic()
        q = self._hits[key]
        while q and now - q[0] > _WINDOW_S:
            q.popleft()
        if len(q) >= self.limit:
            return False
        q.append(now)
        return True


limiter = RateLimiter()


async def rate_limit_middleware(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        client_ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (
            request.client.host if request.client else "unknown"
        )
        if not limiter.allow(client_ip):
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit reached — 10 requests a minute keeps the demo "
                                   "free for everyone. Try again shortly."},
            )
    return await call_next(request)
