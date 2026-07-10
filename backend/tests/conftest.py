from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import middleware
from app.main import create_app
from app.storage import get_storage


@pytest.fixture()
def client() -> TestClient:
    get_storage.cache_clear()  # fresh in-memory storage per test
    middleware.limiter = middleware.RateLimiter(limit_per_minute=1000)  # not under test here
    return TestClient(create_app())
