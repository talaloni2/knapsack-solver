import asyncio
from http import HTTPStatus

import pytest
from aioredis import Redis
from httpx import AsyncClient

import component_factory
from logic.solution_reporter import SolutionReporter
from logic.suggested_solution_service import SuggestedSolutionsService
from models.config.configuration import Config
from models.knapsack_item import KnapsackItem
from models.knapsack_router_dto import RouterSolveRequest
from models.solution import SuggestedSolution, AlgorithmSolution
from server import app
from test.utils import get_random_string


@pytest.fixture
def override_config(config: Config):
    app.dependency_overrides[component_factory.get_config] = lambda: config
    yield
    del app.dependency_overrides[component_factory.get_config]


@pytest.fixture
def solution_reporter(config: Config, solution_suggestions_service: SuggestedSolutionsService) -> SolutionReporter:
    return component_factory.get_solution_reporter(
        suggested_solutions_service=solution_suggestions_service, config=config
    )


@pytest.mark.anyio
async def test_router_controller_endpoint_sanity(
    test_client: AsyncClient,
    override_config: None,
    redis_client: Redis,
    knapsack_id: str,
    solution_reporter: SolutionReporter,
    solver_queue,
):
    expected_item = KnapsackItem(id=get_random_string(), value=10, volume=10)
    request = RouterSolveRequest(items=[expected_item], volume=10, knapsack_id=knapsack_id)
    request_task = asyncio.create_task(test_client.post("/knapsack-router/solve", json=request.dict()))

    await asyncio.sleep(0.2)
    await solution_reporter.report_solution_suggestions([AlgorithmSolution(items=[expected_item])], knapsack_id)

    response = await request_task
    assert response.status_code == HTTPStatus.OK
    deserialized_response = SuggestedSolution(**response.json())
    assert len(deserialized_response.solutions.values()) == 1
    assert next(iter(deserialized_response.solutions.values())).items[0] == expected_item
