"""LLM client: OpenAI-compatible chat completions with retry, model fallback,
and a daily request cap (decision log D-002).

Free OpenRouter routes rate-limit around 20 req/min and ~200 req/day per model,
so every call runs through: primary model (2 attempts, exponential backoff) →
fallback model (2 attempts) → LLMUnavailable. Callers treat LLMUnavailable as
"produce the deterministic fallback" — the product never 500s because a model
was busy.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from datetime import date

import httpx

from app.config import settings

log = logging.getLogger(__name__)

_ATTEMPTS_PER_MODEL = 2
_BACKOFF_BASE_S = 1.0
_TIMEOUT = 40.0


class LLMUnavailable(Exception):
    """All models failed or the daily budget is spent."""


class BudgetExceeded(LLMUnavailable):
    """Per-day request cap reached (graceful 'demo budget reached' path)."""


class _DailyCounter:
    def __init__(self, cap: int) -> None:
        self.cap = cap
        self._day: date | None = None
        self._count = 0

    def tick(self) -> None:
        today = date.today()
        if self._day != today:
            self._day, self._count = today, 0
        if self._count >= self.cap:
            raise BudgetExceeded(f"daily LLM request cap ({self.cap}) reached")
        self._count += 1

    @property
    def used_today(self) -> int:
        return self._count if self._day == date.today() else 0


class LLMClient:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        models: list[str] | None = None,
        temperature: float | None = None,
        daily_cap: int | None = None,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self.base_url = (base_url or settings.llm_base_url).rstrip("/")
        self.api_key = api_key if api_key is not None else settings.llm_api_key
        self.models = models or [settings.llm_model, settings.llm_fallback_model]
        self.temperature = temperature if temperature is not None else settings.llm_temperature
        self.counter = _DailyCounter(daily_cap or settings.llm_daily_request_cap)
        self._sleep = sleeper

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def complete(self, system: str, user: str) -> str:
        """Return the assistant message text, or raise LLMUnavailable."""
        if not self.configured:
            raise LLMUnavailable("no LLM API key configured")
        last_error: Exception | None = None
        for model in self.models:
            for attempt in range(_ATTEMPTS_PER_MODEL):
                try:
                    self.counter.tick()
                    return self._call(model, system, user)
                except BudgetExceeded:
                    raise
                except (httpx.HTTPError, KeyError, ValueError) as exc:
                    last_error = exc
                    log.warning("llm attempt failed model=%s attempt=%d: %s",
                                model, attempt + 1, exc)
                    self._sleep(_BACKOFF_BASE_S * (2 ** attempt))
        raise LLMUnavailable(f"all models failed: {last_error}")

    def _call(self, model: str, system: str, user: str) -> str:
        r = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": model,
                "temperature": self.temperature,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
            timeout=_TIMEOUT,
        )
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
        if not isinstance(content, str) or not content.strip():
            raise ValueError("empty completion")
        return content


_default_client: LLMClient | None = None


def get_client() -> LLMClient:
    global _default_client
    if _default_client is None:
        _default_client = LLMClient()
    return _default_client
