"""NBCA generation endpoint: rank (deterministic) → explain (guarded LLM) → log."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.gold.feeds import confidence_cap, freshness_report
from app.gold.regime import regime_adjustment
from app.llm.client import get_client
from app.llm.explain import generate_card, prompt_version
from app.rules.allocation import Allocation, compute_allocation
from app.rules.distress import assess_distress
from app.rules.engine import rank
from app.schemas.nbca import NBCA
from app.schemas.profile import ProfileIn
from app.storage import Storage, get_storage

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["nbca"])

MAX_CARDS = 5


class NBCARequest(BaseModel):
    session_id: str | None = Field(default=None, description="use latest stored profile")
    profile: ProfileIn | None = Field(default=None, description="or rank this profile inline")


class NBCAResponse(BaseModel):
    cards: list[NBCA]
    in_distress: bool
    gold_adjustment_pts: int
    confidence_cap: str
    data_freshness: dict
    model: str
    prompt_version: str
    degraded_count: int
    allocation: Allocation


@router.post("/nbca", response_model=NBCAResponse)
def generate_nbca(body: NBCARequest, storage: Storage = Depends(get_storage)) -> NBCAResponse:
    if body.profile is not None:
        profile = storage.save_profile(body.profile)
    elif body.session_id:
        stored = storage.latest_profile(body.session_id)
        if stored is None:
            raise HTTPException(status_code=404, detail="No profile for this session")
        profile = stored
    else:
        raise HTTPException(status_code=422, detail="Provide session_id or profile")

    adj = regime_adjustment()
    ranked = rank(profile, gold_adjustment_pts=adj)[:MAX_CARDS]

    client = get_client()
    cap = confidence_cap()
    freshness = freshness_report()
    stale = [k for k, v in freshness.items() if v["status"] != "fresh"]
    asof_note = (
        f"Some data is not fresh ({', '.join(sorted(stale))}); confidence is capped."
        if stale else None
    )

    cards = [generate_card(r, client, freshness_cap=cap, data_asof_note=asof_note)
             for r in ranked]

    asof_values = [v["asof"] for v in freshness.values()]
    engine_asof = min(asof_values) if asof_values else None
    for r, card in zip(ranked, cards, strict=True):
        storage.log_nbca(
            profile_id=str(profile.id),
            rank=r.rank,
            nbca=card.model_dump(mode="json"),
            model=client.models[0] if client.configured else "deterministic-fallback",
            prompt_version=prompt_version(),
            engine_data_asof=engine_asof,
        )

    return NBCAResponse(
        cards=cards,
        in_distress=assess_distress(profile).in_distress,
        gold_adjustment_pts=adj,
        confidence_cap=cap,
        data_freshness=freshness,
        model=client.models[0] if client.configured else "deterministic-fallback",
        prompt_version=prompt_version(),
        degraded_count=sum(1 for c in cards if c.degraded),
        allocation=compute_allocation(profile, gold_adjustment_pts=adj),
    )
