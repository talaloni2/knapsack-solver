import pytest
from fastapi.testclient import TestClient

from server import app


@pytest.fixture()
def test_client() -> TestClient:
    return TestClient(app)
