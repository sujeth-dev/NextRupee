"""Explanation layer: the LLM rewrites engine output as clear prose — nothing else.

Flow per card (Master Doc §4/§7): build prompt from the RankedAction → complete →
parse+schema-validate prose fields → assemble NBCA with ENGINE numbers → output
guard (instrument scan + number diff). One retry with error feedback, then the
deterministic fallback card, flagged degraded=true.
"""

from __future__ import annotations

import json
import logging
import re

from pydantic import BaseModel, Field, ValidationError

from app.guardrails.output_guard import screen_output
from app.llm.client import LLMClient, LLMUnavailable
from app.llm.prompts import PROMPT_VERSION, load_prompt
from app.rules.engine import RankedAction
from app.schemas.nbca import NBCA, Confidence

log = logging.getLogger(__name__)

_CONF_ORDER = {"low": 0, "medium": 1, "high": 2}
_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


class ProseFields(BaseModel):
    """Exactly what the model may author. No numbers-bearing fields of its own."""

    action: str = Field(min_length=10)
    rationale_chain: list[str] = Field(min_length=1, max_length=6)
    confidence_basis: str = Field(min_length=10)
    invalidation_conditions: list[str] = Field(min_length=1, max_length=4)
    alternatives: list[str] = Field(min_length=1, max_length=4)
    opportunity_cost: str = Field(min_length=10)


def cap_confidence(engine_confidence: Confidence, cap: Confidence) -> Confidence:
    return engine_confidence if _CONF_ORDER[engine_confidence] <= _CONF_ORDER[cap] else cap


def _assemble(ranked: RankedAction, prose: ProseFields, confidence: Confidence) -> NBCA:
    return NBCA(
        action=prose.action,
        category=ranked.category,                # engine-owned
        amount_range=ranked.amount_range,        # engine-owned
        rationale_chain=prose.rationale_chain,
        evidence=ranked.evidence,                # engine-owned
        confidence=confidence,                   # engine-owned (freshness-capped)
        confidence_basis=prose.confidence_basis,
        invalidation_conditions=prose.invalidation_conditions,
        alternatives=prose.alternatives,
        opportunity_cost=prose.opportunity_cost,
        degraded=False,
    )


def _parse(raw: str) -> ProseFields:
    return ProseFields.model_validate(json.loads(_FENCE.sub("", raw.strip())))


def generate_card(
    ranked: RankedAction,
    client: LLMClient,
    freshness_cap: Confidence = "high",
    data_asof_note: str | None = None,
) -> NBCA:
    """One NBCA card. Never raises: worst case is the deterministic fallback."""
    confidence = cap_confidence(ranked.confidence, freshness_cap)
    fallback = ranked.to_fallback_nbca()
    fallback.confidence = confidence
    if not client.configured:
        return fallback

    system = load_prompt("card_explanation")
    payload = {
        "ranked_action": ranked.model_dump(),
        "confidence": confidence,
        "data_freshness_note": data_asof_note,
    }
    user = json.dumps(payload, ensure_ascii=False, default=str)

    feedback = ""
    for attempt in range(2):
        try:
            raw = client.complete(system, user + feedback)
            prose = _parse(raw)
        except LLMUnavailable:
            return fallback
        except (json.JSONDecodeError, ValidationError) as exc:
            feedback = (
                "\n\nYour previous reply was rejected: it was not the required bare "
                f"JSON object ({exc}). Reply with only the JSON object."
            )
            log.info("card prose rejected (parse) attempt=%d", attempt + 1)
            continue

        prose_text = " ".join(
            [prose.action, *prose.rationale_chain, prose.confidence_basis,
             *prose.invalidation_conditions, *prose.alternatives, prose.opportunity_cost]
        )
        verdict = screen_output(
            prose_text,
            ranked.evidence,
            extra_allowed_texts=[ranked.action, str(ranked.amount_range),
                                 *ranked.rationale_chain, ranked.opportunity_cost,
                                 *ranked.invalidation_conditions],
        )
        if verdict.allowed:
            return _assemble(ranked, prose, confidence)
        feedback = (
            "\n\nYour previous reply was rejected by the safety scanner: "
            f"{verdict.violations}. Do not name instruments; use only numbers that "
            "appear in the provided evidence, verbatim."
        )
        log.info("card prose rejected (guard) attempt=%d: %s", attempt + 1, verdict.violations)

    return fallback


def prompt_version() -> str:
    return PROMPT_VERSION
