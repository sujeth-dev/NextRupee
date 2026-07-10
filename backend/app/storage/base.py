"""Storage interface. Append-only semantics: profiles are versioned, never updated."""

from __future__ import annotations

from typing import Any, Protocol

from app.schemas.profile import Profile, ProfileIn


class Storage(Protocol):
    def save_profile(self, profile: ProfileIn) -> Profile:
        """Insert a new profile version for the session. Never updates."""
        ...

    def latest_profile(self, session_id: str) -> Profile | None: ...

    def log_nbca(
        self,
        profile_id: str,
        rank: int,
        nbca: dict[str, Any],
        model: str,
        prompt_version: str,
        engine_data_asof: str | None,
    ) -> None: ...

    def log_eval_run(self, git_sha: str, tier: str, metrics: dict[str, Any]) -> None: ...

    def ping(self) -> bool:
        """Cheap real read used by /health (keeps free Supabase unpaused, D-004)."""
        ...
