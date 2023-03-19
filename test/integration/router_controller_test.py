import asyncio
from http import HTTPStatus

import pytest
from aioredis import Redis
from fastapi.testclient import TestClient
from httpx import AsyncClient

import component_factory
from logic.suggested_solution_service import SuggestedSolutionsService
from models.knapsack_item import KnapsackItem
from models.knapsack_router_dto import RouterSolveRequest
from models.solution import SolutionReport, SolutionReportCause, SuggestedSolution
from server import app
from test.utils import get_random_string


@pytest.fixture
def override_solver_queue(queues_cleaner):
    random_queue_name = get_random_string()
    app.dependency_overrides[component_factory.get_solver_queue] = lambda: random_queue_name
    queues_cleaner.append(random_queue_name)
    yield
    del app.dependency_overrides[component_factory.get_solver_queue]


@pytest.mark.anyio
async def test_router_controller_endpoint_sanity(test_client: AsyncClient, override_solver_queue: None, redis_client: Redis, solution_reports_channel_name: str, knapsack_id: str, solution_suggestions_service: SuggestedSolutionsService):
    expected_item = KnapsackItem(id=get_random_string(), value=10, volume=10)
    request = RouterSolveRequest(items=[expected_item], volume=10, knapsack_id=knapsack_id)
    request_task = asyncio.create_task(test_client.post("/knapsack-router/solve", json=request.dict()))
    solution_reporter = component_factory.get_solution_reporter()

    await asyncio.sleep(0.2)
    await solution_reporter.report_solution_suggestions([[expected_item]], knapsack_id)

    response = await request_task
    assert response.status_code == HTTPStatus.OK
    deserialized_response = SuggestedSolution(**response.json())
    assert len(deserialized_response.solutions.values()) == 1
    assert next(iter(deserialized_response.solutions.values()))[0] == expected_item
