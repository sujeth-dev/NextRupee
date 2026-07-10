"""Gold regime signal: the ONE place the gold engine touches ranking (Master Doc §5.5).

Deterministic reading of cached macro drivers into a bounded gold-share
adjustment of −5 / 0 / +5 points. Expired drivers are never consulted.
"""

from __future__ import annotations

from datetime import date

from app.config import GOLD_REGIME_ADJUSTMENT_MAX
from app.gold.feeds import DriverValue, usable_drivers

#: thresholds, part of the spec and unit-tested
REAL_YIELD_LOW = 1.0    # % — below this, gold's opportunity cost is low  → supportive
REAL_YIELD_HIGH = 2.0   # % — above this, opportunity cost bites          → hostile
USD_INDEX_HIGH = 105.0  # strong dollar → hostile


def regime_score(drivers: dict[str, DriverValue]) -> int:
    """Sum of supportive(+1)/hostile(−1) readings across usable macro drivers."""
    score = 0
    ry = drivers.get("us_real_yield_10y")
    if ry is not None:
        if ry.value < REAL_YIELD_LOW:
            score += 1
        elif ry.value > REAL_YIELD_HIGH:
            score -= 1
    dxy = drivers.get("usd_index")
    if dxy is not None and dxy.value > USD_INDEX_HIGH:
        score -= 1
    return score


def regime_adjustment(today: date | None = None) -> int:
    """Bounded allocation adjustment: sign(regime_score) × GOLD_REGIME_ADJUSTMENT_MAX."""
    score = regime_score(usable_drivers(today))
    if score > 0:
        return GOLD_REGIME_ADJUSTMENT_MAX
    if score < 0:
        return -GOLD_REGIME_ADJUSTMENT_MAX
    return 0
