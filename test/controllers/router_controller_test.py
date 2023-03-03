from unittest.mock import AsyncMock

import pytest

from controllers.router_controller import route_solve
from logic.algorithm_decider import AlgorithmDecider
from logic.producer.solver_router_producer import SolverRouterProducer
from models.algorithms import Algorithms
from models.knapsack_item import KnapsackItem
from models.knapsack_router_dto import RouterSolveRequest
from test.utils import get_random_string


@pytest.mark.asyncio
async def test_route_solve_sanity():
    expected_item = KnapsackItem(id=get_random_string(), value=10, volume=10)
    request = RouterSolveRequest(items=[expected_item], volume=10, knapsack_id=get_random_string())
    solve_request_producer = AsyncMock(SolverRouterProducer)
    algo_decider = AsyncMock(AlgorithmDecider)
    algo_decider.decide = AsyncMock(return_value=Algorithms.FIRST_FIT)

    response = await route_solve(request, algo_decider, solve_request_producer)

    assert len(response.items) == 1
    assert response.items[0] == expected_item
    algo_decider.decide.assert_called_once()
    solve_request_producer.produce_solver_instance_request.assert_called_once()
