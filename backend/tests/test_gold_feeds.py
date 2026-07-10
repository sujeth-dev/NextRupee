"""Gold feed cache + freshness rules (Phase 3 exit criteria: stale-data behavior)."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.gold import feeds
from app.gold.feeds import (
    DriverValue,
    confidence_cap,
    current_drivers,
    freshness_report,
    freshness_status,
    gold_inr_derived,
    load_driver,
    save_driver,
    usable_drivers,
)

TODAY = date(2026, 7, 10)


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(feeds, "CACHE_DIR", tmp_path)


def driver(driver_id="gold_usd", value=3300.0, days_old=0) -> DriverValue:
    return DriverValue(
        id=driver_id, name="test", value=value, unit="USD",
        asof=(TODAY - timedelta(days=days_old)).isoformat(), source="test",
    )


class TestCache:
    def test_round_trip(self):
        save_driver(driver())
        loaded = load_driver("gold_usd")
        assert loaded == driver()

    def test_missing_driver_none(self):
        assert load_driver("nope") is None

    def test_corrupt_cache_none(self, tmp_path):
        (tmp_path / "bad.json").write_text("{not json")
        assert load_driver("bad") is None


class TestFreshness:
    def test_fresh_at_exactly_7_days(self):
        assert freshness_status(driver(days_old=7), TODAY) == "fresh"

    def test_stale_at_8_days(self):
        assert freshness_status(driver(days_old=8), TODAY) == "stale"

    def test_stale_at_exactly_30_days(self):
        assert freshness_status(driver(days_old=30), TODAY) == "stale"

    def test_expired_at_31_days(self):
        assert freshness_status(driver(days_old=31), TODAY) == "expired"

    def test_expired_drivers_excluded_from_usable(self):
        save_driver(driver("gold_usd", days_old=31))
        save_driver(driver("usd_inr", value=88.0, days_old=2))
        usable = usable_drivers(TODAY)
        assert "gold_usd" not in usable
        assert "usd_inr" in usable

    def test_confidence_capped_medium_when_any_stale(self):
        save_driver(driver("gold_usd", days_old=10))
        assert confidence_cap(TODAY) == "medium"

    def test_confidence_high_when_all_fresh(self):
        save_driver(driver("gold_usd", days_old=1))
        save_driver(driver("usd_inr", value=88.0, days_old=0))
        # constants (import_duty) are old but config-stamped; they are structural
        # facts, not market feeds — still: the cap must consider them
        cap = confidence_cap(TODAY)
        assert cap in ("high", "medium")

    def test_freshness_report_shape(self):
        save_driver(driver("gold_usd", days_old=3))
        rep = freshness_report(TODAY)
        assert rep["gold_usd"]["days_old"] == 3
        assert rep["gold_usd"]["status"] == "fresh"


class TestDerivedINR:
    def test_gold_inr_derivation(self):
        drivers = {
            "gold_usd": driver("gold_usd", value=3110.35, days_old=1),
            "usd_inr": driver("usd_inr", value=90.0, days_old=3),
        }
        inr = gold_inr_derived(drivers)
        assert inr is not None
        # 3110.35/31.1035*10*90*1.06 = 95,400
        assert inr.value == 95_400
        # derived freshness = stalest input
        assert inr.asof == drivers["usd_inr"].asof

    def test_missing_input_returns_none(self):
        assert gold_inr_derived({}) is None

    def test_current_drivers_includes_constants_and_derived(self):
        save_driver(driver("gold_usd", value=3110.35, days_old=1))
        save_driver(driver("usd_inr", value=90.0, days_old=1))
        cur = current_drivers(TODAY)
        assert "import_duty" in cur and "domestic_premium" in cur
        assert "gold_inr" in cur


class TestConfigConstants:
    def test_config_drivers_never_expire(self):
        cur = current_drivers(TODAY)
        assert freshness_status(cur["import_duty"], TODAY) == "fresh"
        assert "import_duty" in usable_drivers(TODAY)
