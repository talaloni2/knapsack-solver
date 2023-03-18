from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from controllers.router_controller import route_solve, accept_solution, reject_solutions
from logic.algorithm_decider import AlgorithmDecider
from logic.producer.solver_router_producer import SolverRouterProducer
from logic.suggested_solution_service import SuggestedSolutionsService
from models.algorithms import Algorithms
from models.knapsack_item import KnapsackItem
from models.knapsack_router_dto import RouterSolveRequest, AcceptSolutionRequest, RejectSolutionsRequest
from models.solution import SuggestedSolution
from models.suggested_solutions_actions_statuses import AcceptResult, RejectResult
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


@pytest.mark.asyncio
async def test_accept_solution_sanity(
    solution_suggestions_service_with_mocks: SuggestedSolutionsService, knapsack_id: str
):
    solution_suggestions_service_with_mocks.is_solution_exists = AsyncMock(return_value=True)
    solution_suggestions_service_with_mocks.accept_suggested_solution = AsyncMock(
        return_value=AcceptResult.ACCEPT_SUCCESS
    )
    solution_id: str = get_random_string()
    request = AcceptSolutionRequest(knapsack_id=knapsack_id, solution_id=solution_id)

    response = await accept_solution(request, solution_suggestions_service_with_mocks)

    assert AcceptResult.ACCEPT_SUCCESS == response.result
    solution_suggestions_service_with_mocks.is_solution_exists.assert_called_once_with(knapsack_id, solution_id)
    solution_suggestions_service_with_mocks.accept_suggested_solution.assert_called_once_with(knapsack_id, solution_id)


@pytest.mark.asyncio
async def test_accept_solution_solution_not_exists(
    solution_suggestions_service_with_mocks: SuggestedSolutionsService, knapsack_id: str
):
    solution_suggestions_service_with_mocks.is_solution_exists = AsyncMock(return_value=False)
    solution_suggestions_service_with_mocks.accept_suggested_solution = AsyncMock(
        return_value=AcceptResult.ACCEPT_SUCCESS
    )
    solution_id: str = get_random_string()
    request = AcceptSolutionRequest(knapsack_id=knapsack_id, solution_id=solution_id)

    response = await accept_solution(request, solution_suggestions_service_with_mocks)

    assert AcceptResult.SOLUTION_NOT_EXISTS == response.result
    solution_suggestions_service_with_mocks.is_solution_exists.assert_called_once_with(knapsack_id, solution_id)
    solution_suggestions_service_with_mocks.accept_suggested_solution.assert_not_called()


@pytest.mark.asyncio
async def test_reject_solution_sanity(
    solution_suggestions_service_with_mocks: SuggestedSolutionsService, knapsack_id: str
):
    solution_suggestions_service_with_mocks.get_solutions = AsyncMock(
        return_value=SuggestedSolution(time=datetime.now(), solutions={})
    )
    solution_suggestions_service_with_mocks.reject_suggested_solutions = AsyncMock(
        return_value=RejectResult.REJECT_SUCCESS
    )
    request = RejectSolutionsRequest(knapsack_id=knapsack_id)

    response = await reject_solutions(request, solution_suggestions_service_with_mocks)

    assert RejectResult.REJECT_SUCCESS == response.result
    solution_suggestions_service_with_mocks.get_solutions.assert_called_once_with(knapsack_id)
    solution_suggestions_service_with_mocks.reject_suggested_solutions.assert_called_once_with(knapsack_id)


@pytest.mark.asyncio
async def test_reject_solution_solution_not_exists(
    solution_suggestions_service_with_mocks: SuggestedSolutionsService, knapsack_id: str
):
    solution_suggestions_service_with_mocks.get_solutions = AsyncMock(return_value=None)
    solution_suggestions_service_with_mocks.reject_suggested_solutions = AsyncMock(
        return_value=RejectResult.REJECT_SUCCESS
    )
    request = RejectSolutionsRequest(knapsack_id=knapsack_id)

    response = await reject_solutions(request, solution_suggestions_service_with_mocks)

    assert RejectResult.SUGGESTION_NOT_EXISTS == response.result
    solution_suggestions_service_with_mocks.get_solutions.assert_called_once_with(knapsack_id)
    solution_suggestions_service_with_mocks.reject_suggested_solutions.assert_not_called()
