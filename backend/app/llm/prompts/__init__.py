"""Versioned prompt loading. The active version is pinned here (see CHANGELOG.md)."""

from __future__ import annotations

from pathlib import Path

PROMPT_VERSION = "v2"
_DIR = Path(__file__).parent


def load_prompt(name: str) -> str:
    return (_DIR / f"{name}_{PROMPT_VERSION}.md").read_text(encoding="utf-8")
