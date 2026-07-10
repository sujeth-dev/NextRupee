"""Tier 0 — golden-set ranking agreement. Zero LLM calls; blocks merge.

Rankings are deterministic, so the target is 100%: any mismatch between the
engine's category sequence and the expert-authored expectation is a bug in one
of them, never model drift.

Usage: python evals/run_tier0.py   (from repo root or backend/)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "backend"))

from app.rules.engine import rank  # noqa: E402
from app.schemas.profile import ProfileIn  # noqa: E402

GOLDEN = Path(__file__).parent / "golden" / "profiles.json"


def main() -> int:
    cases = json.loads(GOLDEN.read_text())
    failures: list[str] = []
    for case in cases:
        profile = ProfileIn(**case["profile"])
        got = [c.category for c in rank(profile)]
        expected = case["expected_categories"]
        if got != expected:
            failures.append(f"  {case['name']}: expected {expected}, got {got}")
        # reproducibility double-check on every golden profile
        again = [c.category for c in rank(profile)]
        if got != again:
            failures.append(f"  {case['name']}: NON-DETERMINISTIC ({got} vs {again})")

    total = len(cases)
    passed = total - len({f.split(':')[0] for f in failures})
    print(f"Tier 0 golden-set agreement: {passed}/{total}")
    if failures:
        print("FAILURES:")
        print("\n".join(failures))
        return 1
    print("100% agreement — gate passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
