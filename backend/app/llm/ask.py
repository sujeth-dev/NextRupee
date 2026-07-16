"""Why-Q&A: grounded, cited answers about gold — or a graceful refusal/fallback.

Pipeline: input guard → graph-then-vector retrieval + live drivers → LLM answer
as {headline, detail} JSON with [chunk-id]/[driver:id] citations in the detail →
output guard (instruments + citation presence + number diff vs. sources), one
retry with error feedback. Guard failure or model unavailability degrades to a
deterministic answer assembled from the top retrieved chunk and current driver
values.

The response carries both fields plus `answer` (headline + detail concatenated),
kept populated for consumers that predate the split.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import date

from pydantic import BaseModel, Field, ValidationError

from app.gold.feeds import confidence_cap, freshness_report, usable_drivers
from app.gold.rag import causal_context, retrieve
from app.guardrails.input_guard import REFUSAL_HEADLINE, REFUSAL_TEXT, screen_input
from app.guardrails.output_guard import diff_numbers, scan_instruments
from app.llm.client import LLMClient, LLMUnavailable
from app.llm.prompts import load_prompt

log = logging.getLogger(__name__)

_CITATION = re.compile(r"\[(?:driver:)?[a-z0-9\-#_]+\]", re.IGNORECASE)
_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")
_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


class AskProse(BaseModel):
    """Exactly what the model may author for a why-answer."""

    headline: str = Field(min_length=5, max_length=140)
    detail: str = Field(min_length=50)


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


def _fallback_headline(sources: dict) -> str:
    """Deterministic one-liner pointing at the strongest grounded material."""
    if sources["excerpts"]:
        title = re.sub(r"^(reference|regime|note)\s*[:\-—]\s*", "",
                       sources["excerpts"][0]["title"], flags=re.IGNORECASE)
        return f"The key factor: {title.rstrip('.')}."
    if sources["drivers"]:
        return "Here's what today's data shows."
    return "There isn't enough grounded data to answer this yet."


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


def _result(base: dict, headline: str, detail: str, degraded: bool) -> dict:
    return {
        **base,
        "headline": headline,
        "detail": detail,
        "answer": f"{headline}\n\n{detail}",
        "degraded": degraded,
    }


def _parse(raw: str) -> AskProse:
    return AskProse.model_validate(json.loads(_FENCE.sub("", raw.strip())))


def answer_question(
    question: str, client: LLMClient, today: date | None = None
) -> dict:
    verdict = screen_input(question)
    if not verdict.allowed:
        return _result(
            {"citations": [], "refused": True, "confidence_cap": None},
            REFUSAL_HEADLINE, REFUSAL_TEXT, degraded=False,
        )

    sources = _sources(question, today)
    base = {
        "refused": False,
        "confidence_cap": confidence_cap(today),
        "citations": [e["chunk_id"] for e in sources["excerpts"]],
    }

    if client.configured:
        system = load_prompt("why_qa")
        user = json.dumps({"question": question, "sources": sources},
                          ensure_ascii=False, default=str)
        allowed = _allowed_numbers(sources)
        feedback = ""
        for attempt in range(2):
            try:
                prose = _parse(client.complete(system, user + feedback))
            except LLMUnavailable:
                break
            except (json.JSONDecodeError, ValidationError) as exc:
                feedback = (
                    "\n\nYour previous reply was rejected: it was not the required bare "
                    f"JSON object ({exc}). Reply with only the JSON object."
                )
                log.info("ask prose rejected (parse) attempt=%d", attempt + 1)
                continue

            # Both fields face the instrument and number guards; only the detail
            # must carry citations (the headline is required to have none).
            instrument_hits = scan_instruments(prose.headline) + scan_instruments(prose.detail)
            bad_numbers = diff_numbers(prose.headline, allowed) + diff_numbers(prose.detail, allowed)
            has_citation = bool(_CITATION.search(prose.detail))
            if not instrument_hits and has_citation and not bad_numbers:
                return _result(base, prose.headline.strip(), prose.detail.strip(), degraded=False)
            feedback = (
                "\n\nYour previous reply was rejected by the safety scanner: "
                f"instruments={instrument_hits} citation_in_detail={has_citation} "
                f"unsupported_numbers={bad_numbers}. Do not name instruments; cite every "
                "claim in detail; use only numbers from the provided sources, verbatim."
            )
            log.info("ask output rejected attempt=%d: instruments=%s citation=%s numbers=%s",
                     attempt + 1, instrument_hits, has_citation, bad_numbers)

    return _result(base, _fallback_headline(sources), _fallback_answer(question, sources),
                   degraded=True)
