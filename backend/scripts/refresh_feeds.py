"""Nightly data-feed refresh job (GitHub Actions cron / Render cron).

Usage: python scripts/refresh_feeds.py
Exit code 0 even on partial failure — freshness rules handle staleness;
the job only fails if NO driver could be served at all.
"""

from __future__ import annotations

import json
import sys

from app.gold.feeds import fetch_all, freshness_report


def main() -> int:
    drivers = fetch_all()
    report = freshness_report()
    print(json.dumps(report, indent=2))
    if not drivers:
        print("FATAL: no drivers available (fetch failed and cache empty)", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
