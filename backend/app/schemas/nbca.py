"""NBCA (Next Best Course of Action) schema — the contract everything is built around.

Master Doc §4. Validation failure of LLM output against this schema triggers
one retry with error feedback, then the deterministic fallback card.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

EvidenceSource = Literal["rules_engine", "gold_engine", "document"]
Category = Literal["stabilize", "emergency_fund", "debt", "insurance", "invest_allocation"]
Confidence = Literal["high", "medium", "low"]


class Evidence(BaseModel):
    """A single traceable claim. Every number shown to the user lives here."""

    claim: str
    source: EvidenceSource
    ref: str = Field(description="calc id, driver id, or doc chunk id")
    value: str | None = Field(default=None, description="the actual number shown to the user")


class NBCA(BaseModel):
    """One ranked recommendation card. All numbers computed by the rules engine."""

    action: str = Field(description="imperative, no instrument names")
    category: Category
    amount_range: tuple[int, int] = Field(description="rupees, computed by rules engine")
    rationale_chain: list[str] = Field(min_length=1, description="ordered causal steps")
    evidence: list[Evidence] = Field(min_length=1)
    confidence: Confidence
    confidence_basis: str
    invalidation_conditions: list[str] = Field(min_length=1)
    alternatives: list[str] = Field(min_length=1)
    opportunity_cost: str
    degraded: bool = Field(
        default=False, description="true when the deterministic fallback produced this card"
    )

    @field_validator("amount_range")
    @classmethod
    def _range_ordered(cls, v: tuple[int, int]) -> tuple[int, int]:
        lo, hi = v
        if lo < 0 or hi < lo:
            raise ValueError("amount_range must be 0 <= low <= high")
        return v
