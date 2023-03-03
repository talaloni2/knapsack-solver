from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient

import component_factory
from models.knapsack_item import KnapsackItem
from models.knapsack_router_dto import RouterSolveRequest
from test.utils import get_random_string


@pytest.fixture
def override_solver_queue(test_client: TestClient, queues_cleaner):
    random_queue_name = get_random_string()
    test_client.app.dependency_overrides[component_factory.get_solver_queue] = lambda: random_queue_name
    queues_cleaner.append(random_queue_name)
    yield
    del test_client.app.dependency_overrides[component_factory.get_solver_queue]


def test_router_controller_endpoint_sanity(test_client: TestClient, override_solver_queue):
    expected_item = KnapsackItem(id=get_random_string(), value=10, volume=10)
    request = RouterSolveRequest(items=[expected_item], volume=10, knapsack_id=get_random_string())
    response = test_client.post("/knapsack-router/solve", json=request.dict())
    assert response.status_code == HTTPStatus.OK
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0] == expected_item
