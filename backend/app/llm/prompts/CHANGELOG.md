# Prompt changelog

Prompts are versioned files; the active version is pinned in `app/llm/prompts/__init__.py`.
Any prompt change bumps the version and lands with a Tier 1/2 eval run.

- v1 (2026-07-10): initial card-explanation, why-QA, and refusal prompts.
- v2 (2026-07-16): why-QA now emits a `{headline, detail}` JSON object — a one-line
  plain-language answer plus the cited 120-180 word explanation. Card-explanation
  `action` tightened to a short plain imperative (reasoning stays in rationale_chain).
  Refusal prompt unchanged (copied verbatim).
