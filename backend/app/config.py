"""Application settings and rule constants.

Rule constants are deliberately plain module-level values (not env-driven):
they are part of the product spec (Master Doc §5) and each is unit-tested.
Runtime settings come from the environment.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict

# --- Rule constants (Master Doc §5) -------------------------------------------------

#: Distress: monthly debt interest > this fraction of income
DEBT_SERVICE_RATIO_MAX = 0.40
#: Distress: cash savings below this many months of expenses
RUNWAY_MIN_MONTHS = 1
#: Distress: high-interest debt above this multiple of monthly surplus
DEBT_OVERHANG_MULTIPLE = 6
#: Emergency fund targets (months of expenses)
EMERGENCY_FUND_STAGE1_MONTHS = 3
EMERGENCY_FUND_STAGE2_MONTHS = 6
#: Debt counts as "high interest" at or above this APR (percent)
HIGH_INTEREST_APR_MIN = 10.0
#: Term-cover heuristic: multiple of annual income
TERM_COVER_INCOME_MULTIPLE = 15
#: Asset-class split by risk tolerance: (equity, fixed_income, gold) in percent
ALLOCATION_SPLITS: dict[str, tuple[int, int, int]] = {
    "low": (35, 50, 15),
    "medium": (55, 30, 15),
    "high": (70, 20, 10),
}
#: Gold regime signal may shift the gold share by at most this many points
GOLD_REGIME_ADJUSTMENT_MAX = 5
#: Indicative long-run expected annual returns by asset class (percent) —
#: used only for the guaranteed-return framing of debt prepayment (§5.3).
EXPECTED_RETURNS = {"equity": 12.0, "fixed_income": 7.0, "gold": 8.0}

#: Data freshness (Master Doc §6)
FRESHNESS_SOFT_DAYS = 7   # older ⇒ flag + confidence cap "medium"
FRESHNESS_HARD_DAYS = 30  # older ⇒ exclude engine facts entirely


class Settings(BaseSettings):
    """Runtime configuration, environment-driven. See .env.example."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"  # local | staging | prod

    # Supabase (optional — storage degrades to NullStorage when unset)
    supabase_url: str = ""
    supabase_service_key: str = ""

    # LLM via OpenRouter (OpenAI-compatible). Free routes have tight rate
    # limits (~20 req/min, ~200 req/day per model) — hence the fallback chain.
    llm_base_url: str = "https://openrouter.ai/api/v1"
    llm_api_key: str = ""
    llm_model: str = "z-ai/glm-4.5-air:free"
    llm_fallback_model: str = "meta-llama/llama-3.3-70b-instruct:free"
    llm_temperature: float = 0.2
    llm_daily_request_cap: int = 180  # below the ~200/day free ceiling

    # External data
    fred_api_key: str = ""

    # Hardening
    rate_limit_per_minute: int = 10

    # Paths
    chroma_path: str = ".chroma"


settings = Settings()
