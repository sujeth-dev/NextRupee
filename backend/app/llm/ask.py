"""Why-Q&A: grounded, cited answers about gold — or a graceful refusal/fallback.

Pipeline: input guard → graph-then-vector retrieval + live drivers → LLM answer
with [chunk-id]/[driver:id] citations → output guard (instruments + citation
presence + number diff vs. sources). Guard failure or model unavailability
degrades to a deterministic answer assembled from the top retrieved chunk and
current driver values.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import date

from app.gold.feeds import confidence_cap, freshness_report, usable_drivers
from app.gold.rag import causal_context, retrieve
from app.guardrails.input_guard import REFUSAL_TEXT, screen_input
from app.guardrails.output_guard import diff_numbers, scan_instruments
from app.llm.client import LLMClient, LLMUnavailable
from app.llm.prompts import load_prompt

log = logging.getLogger(__name__)

_CITATION = re.compile(r"\[(?:driver:)?[a-z0-9\-#_]+\]", re.IGNORECASE)
_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")


def _sources(question: str, today: date | None = None) -> dict:
    retrieved = retrieve(question, k=4)
    drivers = usable_drivers(today)
    return {
        "drivers": {
            k: {"value": v.value, "unit": v.unit, "asof": v.asof} for k, v in drivers.items()
        },
        "causal_edges": causal_context(question),
        "excerpts": [
            {"chunk_id": r.chunk.id, "title": r.chunk.title, "text": r.chunk.text}
            for r in retrieved
        ],
        "freshness": freshness_report(today),
    }


def _allowed_numbers(sources: dict) -> set[str]:
    texts = [e["text"] for e in sources["excerpts"]]
    texts += [f'{d["value"]} {d["asof"]}' for d in sources["drivers"].values()]
    allowed = {str(n) for n in range(0, 16)} | {"20", "24", "30", "40", "50", "100"}
    for t in texts:
        for num in _NUMBER.findall(t):
            allowed.add(num.replace(",", ""))
    return allowed


def _fallback_answer(question: str, sources: dict) -> str:
    """Deterministic answer: top excerpt + live numbers, honestly labelled."""
    parts: list[str] = []
    if sources["excerpts"]:
        top = sources["excerpts"][0]
        parts.append(f'{top["text"]} [{top["chunk_id"]}]')
    lines = [
        f'{k}: {d["value"]} {d["unit"]} (as of {d["asof"]}) [driver:{k}]'
        for k, d in sorted(sources["drivers"].items())
    ]
    if lines:
        parts.append("Current readings — " + "; ".join(lines) + ".")
    return "\n\n".join(parts) if parts else (
        "No grounded material is available for this question right now."
    )


def answer_question(
    question: str, client: LLMClient, today: date | None = None
) -> dict:
    verdict = screen_input(question)
    if not verdict.allowed:
        return {
            "answer": REFUSAL_TEXT,
            "citations": [],
            "refused": True,
            "degraded": False,
            "confidence_cap": None,
        }

    sources = _sources(question, today)
    cap = confidence_cap(today)
    base = {
        "refused": False,
        "confidence_cap": cap,
        "citations": [e["chunk_id"] for e in sources["excerpts"]],
    }

    if client.configured:
        system = load_prompt("why_qa")
        user = json.dumps({"question": question, "sources": sources},
                          ensure_ascii=False, default=str)
        try:
            raw = client.complete(system, user)
            instrument_hits = scan_instruments(raw)
            has_citation = bool(_CITATION.search(raw))
            bad_numbers = diff_numbers(raw, _allowed_numbers(sources))
            if not instrument_hits and has_citation and not bad_numbers:
                return {**base, "answer": raw.strip(), "degraded": False}
            log.info("ask output rejected: instruments=%s citation=%s numbers=%s",
                     instrument_hits, has_citation, bad_numbers)
        except LLMUnavailable:
            pass

    return {**base, "answer": _fallback_answer(question, sources), "degraded": True}
