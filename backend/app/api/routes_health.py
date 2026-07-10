"""Health endpoint: process liveness + DB reachability + data freshness.

Performs a real Supabase read (D-004) so the external uptime ping keeps the
free project from auto-pausing.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.storage import Storage, get_storage

router = APIRouter(tags=["ops"])


@router.get("/health")
def health(storage: Storage = Depends(get_storage)) -> dict:
    try:  # gold engine ships in Phase 3; health must not depend on it
        from app.gold.feeds import freshness_report

        freshness = freshness_report()
    except ImportError:
        freshness = {}

    return {
        "status": "ok",
        "db": "ok" if storage.ping() else "unreachable",
        "data_freshness": freshness,
    }
