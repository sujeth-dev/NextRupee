"""Tier 2 — nightly full eval with the demo model. Not a merge gate.

Scores explanation quality over a golden-set sample with an LLM judge
(coherent causal chain? concrete invalidators? quantified opportunity cost?),
plus annotation-relative confidence agreement. Metrics land in eval_runs; the
job fails loudly on a >5pt regression against the previous run.

Honesty note (mirrored in the README): confidence agreement is measured against
expert annotation, NOT against live outcomes — outcome calibration needs the
longitudinal ledger documented as future work.

Requires LLM_API_KEY; exits 0 with a notice when unset (fork-safe CI).
Sampled to respect free-route daily quotas.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "backend"))

from app.llm.client import LLMClient, LLMUnavailable  # noqa: E402
from app.llm.explain import generate_card  # noqa: E402
from app.rules.engine import rank  # noqa: E402
from app.schemas.profile import ProfileIn  # noqa: E402
from app.storage import get_storage  # noqa: E402

SAMPLE = 10  # free-route quota discipline (~30 requests total incl. judging)
REGRESSION_PTS = 5.0

JUDGE_SYSTEM = """You grade one explanation card from a financial decision-support product.
Score each criterion 1-5 (5 best) and reply with ONLY a JSON object:
{"causal_coherence": n, "invalidators_concrete": n, "opportunity_cost_quantified": n}
- causal_coherence: do the rationale steps follow logically toward the action?
- invalidators_concrete: are the invalidation conditions checkable, not vague?
- opportunity_cost_quantified: does it state what is given up, tied to a number?"""


def git_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO,
                              capture_output=True, text=True, check=True).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def main() -> int:
    if not os.environ.get("LLM_API_KEY"):
        print("Tier 2 skipped: LLM_API_KEY not set (expected on forks).")
        return 0

    client = LLMClient()
    cases = json.loads((REPO / "evals" / "golden" / "profiles.json").read_text())[:SAMPLE]

    scores: list[float] = []
    fill_ok = fill_total = 0
    conf_agree = conf_total = 0

    for case in cases:
        ranked = rank(ProfileIn(**case["profile"]))
        if not ranked:
            continue
        card = generate_card(ranked[0], client)
        fill_total += 1
        if card.degraded:
            continue
        fill_ok += 1
        # annotation-relative confidence agreement: engine confidence is the annotation
        conf_total += 1
        conf_agree += 1 if card.confidence == ranked[0].confidence else 0
        try:
            raw = client.complete(JUDGE_SYSTEM, card.model_dump_json())
            j = json.loads(raw.strip().removeprefix("```json").removesuffix("```"))
            scores.append(sum(float(j[k]) for k in (
                "causal_coherence", "invalidators_concrete", "opportunity_cost_quantified"
            )) / 3.0)
        except (LLMUnavailable, json.JSONDecodeError, KeyError, ValueError) as exc:
            print(f"judge skipped for {case['name']}: {exc}")

    quality = round(sum(scores) / len(scores) * 20, 1) if scores else 0.0  # 0-100 scale
    metrics = {
        "quality_score": quality,
        "judged": len(scores),
        "schema_fill_rate": round(fill_ok / fill_total, 3) if fill_total else None,
        "confidence_agreement": round(conf_agree / conf_total, 3) if conf_total else None,
        "sample_size": SAMPLE,
    }
    print(json.dumps(metrics, indent=2))

    storage = get_storage()
    storage.log_eval_run(git_sha(), "tier2", metrics)

    prev = os.environ.get("TIER2_BASELINE")
    if prev and scores:
        baseline = float(prev)
        if quality < baseline - REGRESSION_PTS:
            print(f"REGRESSION: quality {quality} < baseline {baseline} − {REGRESSION_PTS}")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
