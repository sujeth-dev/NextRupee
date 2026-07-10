"""Financial profile intake schema. Money normalised to integer rupees (D-008)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

RiskTolerance = Literal["low", "medium", "high"]


class ProfileIn(BaseModel):
    """What the intake form submits."""

    session_id: str = Field(min_length=1, max_length=128)
    monthly_income: int = Field(ge=0, le=100_000_000)
    monthly_expenses: int = Field(ge=0, le=100_000_000)
    cash_savings: int = Field(ge=0, le=10_000_000_000)
    hi_debt_amount: int = Field(default=0, ge=0, le=10_000_000_000)
    hi_debt_apr: float = Field(default=0.0, ge=0, le=100, description="APR percent")
    dependents: bool = False
    term_insurance: bool = False
    risk_tolerance: RiskTolerance = "medium"
    goals: list[str] = Field(default_factory=list, max_length=10)

    @field_validator(
        "monthly_income", "monthly_expenses", "cash_savings", "hi_debt_amount", mode="before"
    )
    @classmethod
    def _to_int_rupees(cls, v: object) -> object:
        """Accept floats from JSON but store integer rupees."""
        if isinstance(v, float):
            return round(v)
        return v

    @property
    def monthly_surplus(self) -> int:
        return self.monthly_income - self.monthly_expenses

    @property
    def months_runway(self) -> float:
        if self.monthly_expenses <= 0:
            return float("inf")
        return self.cash_savings / self.monthly_expenses


class Profile(ProfileIn):
    """A stored, versioned profile row (append-only)."""

    id: UUID = Field(default_factory=uuid4)
    version: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
