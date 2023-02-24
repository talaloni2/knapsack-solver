from http import HTTPStatus

from fastapi.testclient import TestClient

from models.knapsack_item import KnapsackItem
from models.knapsack_router_dto import RouterSolveRequest
from test.utils import get_random_string


def test_router_controller_endpoint_sanity(test_client: TestClient):
    expected_item = KnapsackItem(id=get_random_string(), value=10, volume=10)
    request = RouterSolveRequest(
        items=[expected_item], volume=10, knapsack_id=get_random_string()
    )
    response = test_client.post("/knapsack-router/solve", json=request.dict())
    assert response.status_code == HTTPStatus.OK
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0] == expected_item
