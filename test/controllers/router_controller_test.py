from unittest.mock import MagicMock

import pytest

from controllers.router_controller import route_solve
from logic.algorithm_decider import AlgorithmDecider
from models.knapsack_item import KnapsackItem
from models.knapsack_router_dto import RouterSolveRequest
from test.utils import get_random_string


@pytest.mark.asyncio
async def test_route_solve_sanity():
    expected_item = KnapsackItem(id=get_random_string(), value=10, volume=10)
    request = RouterSolveRequest(items=[expected_item], volume=10, knapsack_id=get_random_string())
    algo_decider = MagicMock(AlgorithmDecider)

    response = await route_solve(request, algo_decider)

    assert len(response.items) == 1
    assert response.items[0] == expected_item
    algo_decider.decide.assert_called_once()
