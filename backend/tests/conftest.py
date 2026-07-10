from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.storage import get_storage


@pytest.fixture()
def client() -> TestClient:
    get_storage.cache_clear()  # fresh in-memory storage per test
    return TestClient(create_app())
