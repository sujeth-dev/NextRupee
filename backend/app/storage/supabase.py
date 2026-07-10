"""Thin Supabase (PostgREST) storage client. No SDK dependency — plain httpx."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.schemas.profile import Profile, ProfileIn

log = logging.getLogger(__name__)
_TIMEOUT = 10.0


class SupabaseStorage:
    def __init__(self, url: str, service_key: str) -> None:
        self._rest = url.rstrip("/") + "/rest/v1"
        self._headers = {
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def _post(self, table: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        try:
            r = httpx.post(
                f"{self._rest}/{table}", json=payload, headers=self._headers, timeout=_TIMEOUT
            )
            r.raise_for_status()
            rows = r.json()
            return rows[0] if isinstance(rows, list) and rows else None
        except httpx.HTTPError:
            log.exception("supabase insert failed: table=%s", table)
            return None

    def save_profile(self, profile: ProfileIn) -> Profile:
        latest = self.latest_profile(profile.session_id)
        version = (latest.version + 1) if latest else 1
        row = Profile(**profile.model_dump(), version=version)
        payload = row.model_dump(mode="json")
        self._post("profiles", payload)
        return row

    def latest_profile(self, session_id: str) -> Profile | None:
        try:
            r = httpx.get(
                f"{self._rest}/profiles",
                params={
                    "session_id": f"eq.{session_id}",
                    "order": "version.desc",
                    "limit": "1",
                },
                headers=self._headers,
                timeout=_TIMEOUT,
            )
            r.raise_for_status()
            rows = r.json()
            return Profile(**rows[0]) if rows else None
        except httpx.HTTPError:
            log.exception("supabase read failed: profiles")
            return None

    def log_nbca(
        self,
        profile_id: str,
        rank: int,
        nbca: dict[str, Any],
        model: str,
        prompt_version: str,
        engine_data_asof: str | None,
    ) -> None:
        self._post(
            "nbca_log",
            {
                "profile_id": profile_id,
                "rank": rank,
                "nbca": nbca,
                "model": model,
                "prompt_version": prompt_version,
                "engine_data_asof": engine_data_asof,
            },
        )

    def log_eval_run(self, git_sha: str, tier: str, metrics: dict[str, Any]) -> None:
        self._post("eval_runs", {"git_sha": git_sha, "tier": tier, "metrics": metrics})

    def ping(self) -> bool:
        try:
            r = httpx.get(
                f"{self._rest}/profiles",
                params={"select": "id", "limit": "1"},
                headers=self._headers,
                timeout=_TIMEOUT,
            )
            return r.status_code == 200
        except httpx.HTTPError:
            return False
