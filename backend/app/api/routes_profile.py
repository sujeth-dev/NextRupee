"""Profile intake endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.profile import Profile, ProfileIn
from app.storage import Storage, get_storage

router = APIRouter(prefix="/api", tags=["profile"])


@router.post("/profile", response_model=Profile, status_code=201)
def create_profile(body: ProfileIn, storage: Storage = Depends(get_storage)) -> Profile:
    return storage.save_profile(body)


@router.get("/profile/{session_id}", response_model=Profile)
def get_latest_profile(session_id: str, storage: Storage = Depends(get_storage)) -> Profile:
    profile = storage.latest_profile(session_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="No profile for this session")
    return profile
