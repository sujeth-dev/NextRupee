"""In-memory storage for local dev and CI. Same append-only semantics."""

from __future__ import annotations

import logging
from typing import Any

from app.schemas.profile import Profile, ProfileIn

log = logging.getLogger(__name__)


class NullStorage:
    def __init__(self) -> None:
        self._profiles: dict[str, list[Profile]] = {}

    def save_profile(self, profile: ProfileIn) -> Profile:
        versions = self._profiles.setdefault(profile.session_id, [])
        row = Profile(**profile.model_dump(), version=len(versions) + 1)
        versions.append(row)
        return row

    def latest_profile(self, session_id: str) -> Profile | None:
        versions = self._profiles.get(session_id)
        return versions[-1] if versions else None

    def log_nbca(
        self,
        profile_id: str,
        rank: int,
        nbca: dict[str, Any],
        model: str,
        prompt_version: str,
        engine_data_asof: str | None,
    ) -> None:
        log.info("nbca_log (offline): profile=%s rank=%s model=%s", profile_id, rank, model)

    def log_eval_run(self, git_sha: str, tier: str, metrics: dict[str, Any]) -> None:
        log.info("eval_run (offline): sha=%s tier=%s", git_sha, tier)

    def ping(self) -> bool:
        return True
