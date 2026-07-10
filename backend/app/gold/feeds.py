"""Live gold drivers: fetch, cache, asof-stamp, freshness rules (Master Doc §6).

Every driver value is cached to a JSON file with its `asof` date. Freshness:
  > FRESHNESS_SOFT_DAYS  ⇒ answers flagged "as of {date}", confidence capped "medium"
  > FRESHNESS_HARD_DAYS  ⇒ driver excluded from engine facts entirely

Fetchers degrade gracefully: on any network/parse failure the cached value
(however old) keeps serving under the freshness rules above.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path

import httpx

from app.config import FRESHNESS_HARD_DAYS, FRESHNESS_SOFT_DAYS, settings

log = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent / "cache"

#: Config-constant drivers, manually updated (import duty changes by budget notification).
IMPORT_DUTY_PCT = 6.0
IMPORT_DUTY_ASOF = "2025-02-01"
DOMESTIC_PREMIUM_PCT = 1.5  # typical domestic premium over landed price
DOMESTIC_PREMIUM_ASOF = "2025-02-01"


@dataclass
class DriverValue:
    id: str
    name: str
    value: float
    unit: str
    asof: str  # ISO date
    source: str

    @property
    def asof_date(self) -> date:
        return date.fromisoformat(self.asof)


def _cache_path(driver_id: str) -> Path:
    return CACHE_DIR / f"{driver_id}.json"


def save_driver(d: DriverValue) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _cache_path(d.id).write_text(json.dumps(asdict(d), indent=2))


def load_driver(driver_id: str) -> DriverValue | None:
    p = _cache_path(driver_id)
    if not p.exists():
        return None
    try:
        return DriverValue(**json.loads(p.read_text()))
    except (json.JSONDecodeError, TypeError):
        log.warning("corrupt cache for driver %s", driver_id)
        return None


# --- fetchers (plain httpx; see decision log D-011) ----------------------------------

_YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=5d"
_FRED = (
    "https://api.stlouisfed.org/fred/series/observations"
    "?series_id={series}&api_key={key}&file_type=json&sort_order=desc&limit=1"
)


def _yahoo_last_close(symbol: str) -> tuple[float, str]:
    r = httpx.get(_YAHOO.format(symbol=symbol), timeout=15,
                  headers={"User-Agent": "nextrupee/0.1"})
    r.raise_for_status()
    result = r.json()["chart"]["result"][0]
    closes = [c for c in result["indicators"]["quote"][0]["close"] if c is not None]
    ts = result["timestamp"][-1]
    return float(closes[-1]), datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()


def _fred_latest(series: str) -> tuple[float, str]:
    if not settings.fred_api_key:
        raise RuntimeError("FRED_API_KEY not configured")
    r = httpx.get(_FRED.format(series=series, key=settings.fred_api_key), timeout=15)
    r.raise_for_status()
    obs = r.json()["observations"][0]
    return float(obs["value"]), obs["date"]


#: driver id -> (name, unit, source, fetch callable)
FETCHERS = {
    "gold_usd": ("Gold spot (USD/oz)", "USD", "yahoo:GC=F", lambda: _yahoo_last_close("GC=F")),
    "usd_index": ("US dollar index", "index", "yahoo:DX-Y.NYB",
                  lambda: _yahoo_last_close("DX-Y.NYB")),
    "usd_inr": ("USD/INR", "INR", "yahoo:USDINR=X", lambda: _yahoo_last_close("USDINR=X")),
    "us_real_yield_10y": ("US 10y real yield", "%", "fred:DFII10", lambda: _fred_latest("DFII10")),
    "india_cpi_yoy": ("India CPI (index)", "index", "fred:INDCPIALLMINMEI",
                      lambda: _fred_latest("INDCPIALLMINMEI")),
}


def fetch_all(today: date | None = None) -> dict[str, DriverValue]:
    """Refresh every fetchable driver; failures fall back to cache. Returns current set."""
    for driver_id, (name, unit, source, fetch) in FETCHERS.items():
        try:
            value, asof = fetch()
            save_driver(DriverValue(driver_id, name, value, unit, asof, source))
        except Exception:  # noqa: BLE001 — any feed failure must not break the job
            log.exception("feed failed: %s (serving cache)", driver_id)
    _save_constants()
    return current_drivers(today)


def _save_constants() -> None:
    save_driver(DriverValue("import_duty", "Indian gold import duty", IMPORT_DUTY_PCT, "%",
                            IMPORT_DUTY_ASOF, "config:budget-notification"))
    save_driver(DriverValue("domestic_premium", "Domestic premium over landed price",
                            DOMESTIC_PREMIUM_PCT, "%", DOMESTIC_PREMIUM_ASOF, "config:manual"))


def gold_inr_derived(drivers: dict[str, DriverValue]) -> DriverValue | None:
    """Landed INR gold price per 10g, derived from USD spot × fx × (1 + duty)."""
    usd, fx = drivers.get("gold_usd"), drivers.get("usd_inr")
    if not usd or not fx:
        return None
    duty = drivers.get("import_duty")
    duty_pct = duty.value if duty else IMPORT_DUTY_PCT
    per_10g = usd.value / 31.1035 * 10 * fx.value * (1 + duty_pct / 100)
    asof = min(usd.asof, fx.asof)  # derived value is only as fresh as its stalest input
    return DriverValue("gold_inr", "Gold landed price (INR/10g)", round(per_10g),
                       "INR", asof, "derived:gold_usd×usd_inr×duty")


def current_drivers(today: date | None = None) -> dict[str, DriverValue]:
    """All cached drivers, constants included, plus the derived INR price."""
    _save_constants()
    out: dict[str, DriverValue] = {}
    for driver_id in [*FETCHERS.keys(), "import_duty", "domestic_premium"]:
        d = load_driver(driver_id)
        if d:
            out[d.id] = d
    inr = gold_inr_derived(out)
    if inr:
        out[inr.id] = inr
    return out


# --- freshness -----------------------------------------------------------------------


def staleness_days(d: DriverValue, today: date | None = None) -> int:
    today = today or datetime.now(timezone.utc).date()
    return (today - d.asof_date).days


def freshness_status(d: DriverValue, today: date | None = None) -> str:
    # Config constants (import duty, premium) are structural facts updated by
    # policy events, not daily feeds — they never expire, only their update
    # date is surfaced.
    if d.source.startswith("config:"):
        return "fresh"
    days = staleness_days(d, today)
    if days > FRESHNESS_HARD_DAYS:
        return "expired"
    if days > FRESHNESS_SOFT_DAYS:
        return "stale"
    return "fresh"


def usable_drivers(today: date | None = None) -> dict[str, DriverValue]:
    """Drivers admissible as engine facts (expired ones excluded, Master Doc §6)."""
    return {
        k: v for k, v in current_drivers(today).items()
        if freshness_status(v, today) != "expired"
    }


def confidence_cap(today: date | None = None) -> str:
    """'high' when all usable drivers are fresh; 'medium' when any is stale."""
    usable = usable_drivers(today)
    if not usable:
        return "medium"
    if any(freshness_status(v, today) == "stale" for v in usable.values()):
        return "medium"
    return "high"


def freshness_report(today: date | None = None) -> dict[str, dict]:
    return {
        k: {"asof": v.asof, "days_old": staleness_days(v, today),
            "status": freshness_status(v, today)}
        for k, v in current_drivers(today).items()
    }
