"""Tier 1 — cheap checks on every PR (~cents online, free offline).

Offline (--offline, used in CI without secrets):
  - guardrail suite: 25 adversarial prompts against the deterministic input
    guard → expected refuse/answer decisions must match 100%
  - grounding check: for every golden profile, every Evidence.value in the
    fallback cards must appear verbatim in engine output (string diff, no judge)

Online (with LLM_API_KEY set): additionally measures schema-fill success rate
over 15 sampled profiles (target ≥95% without fallback).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "backend"))

from app.guardrails.input_guard import screen_input  # noqa: E402
from app.guardrails.output_guard import allowed_numbers, diff_numbers  # noqa: E402
from app.rules.engine import rank  # noqa: E402
from app.schemas.profile import ProfileIn  # noqa: E402

EVALS = Path(__file__).parent


def guardrail_suite() -> tuple[int, int, list[str]]:
    cases = json.loads((EVALS / "adversarial.json").read_text())
    failures = []
    for case in cases:
        refused = not screen_input(case["prompt"]).allowed
        want_refuse = case["expect"] == "refuse"
        if refused != want_refuse:
            failures.append(f"  {case['prompt']!r}: expected {case['expect']}")
    return len(cases) - len(failures), len(cases), failures


def grounding_check() -> tuple[int, int, list[str]]:
    cases = json.loads((EVALS / "golden" / "profiles.json").read_text())
    checked = 0
    failures = []
    for case in cases:
        for ranked in rank(ProfileIn(**case["profile"])):
            card = ranked.to_fallback_nbca()
            text = " ".join([card.action, card.opportunity_cost,
                             *card.rationale_chain, *card.invalidation_conditions])
            bad = diff_numbers(text, allowed_numbers(card.evidence, [ranked.action,
                               str(ranked.amount_range), *ranked.rationale_chain,
                               ranked.opportunity_cost, *ranked.invalidation_conditions]))
            checked += 1
            if bad:
                failures.append(f"  {case['name']}/{card.category}: unexplained numbers {bad}")
    return checked - len(failures), checked, failures


def schema_fill_rate() -> tuple[int, int]:
    from app.llm.client import get_client  # noqa: PLC0415
    from app.llm.explain import generate_card  # noqa: PLC0415

    client = get_client()
    cases = json.loads((EVALS / "golden" / "profiles.json").read_text())[:15]
    ok = total = 0
    for case in cases:
        ranked = rank(ProfileIn(**case["profile"]))
        if not ranked:
            continue
        card = generate_card(ranked[0], client)
        total += 1
        ok += 0 if card.degraded else 1
    return ok, total


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true",
                        help="skip LLM-dependent checks (CI default)")
    args = parser.parse_args()

    exit_code = 0

    ok, total, failures = guardrail_suite()
    print(f"Tier 1 guardrail suite: {ok}/{total}")
    if failures:
        print("\n".join(failures))
        exit_code = 1

    ok, total, failures = grounding_check()
    print(f"Tier 1 grounding check: {ok}/{total} cards fully evidence-grounded")
    if failures:
        print("\n".join(failures[:10]))
        exit_code = 1

    if not args.offline:
        ok, total = schema_fill_rate()
        rate = ok / total if total else 0
        print(f"Tier 1 schema-fill rate: {ok}/{total} ({rate:.0%}, target ≥95%)")
        if rate < 0.95:
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
