import json
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock

import pytest
from aioredis import Redis

from logic.claims_service import ClaimsService
from logic.suggested_solution_service import SuggestedSolutionsService
from logic.time_service import TimeService
from models.config.configuration import Config
from models.knapsack_item import KnapsackItem
from models.solution import SuggestedSolution, AcceptedSolution, AlgorithmSolution
from models.suggested_solutions_actions_statuses import RejectResult, AcceptResult
from test.utils import get_random_string


@pytest.mark.asyncio
async def test_register_suggested_solutions(
    redis_mock: Redis,
    solution_suggestions_service_with_mocks: SuggestedSolutionsService,
    claims_service_mock: ClaimsService,
    time_service_mock: TimeService,
    knapsack_id: str,
):
    expected_time = datetime.now()
    time_service_mock.now = MagicMock(return_value=expected_time)
    expected_solutions: list[AlgorithmSolution] = [
        AlgorithmSolution(items=[KnapsackItem(id=get_random_string(), value=1, volume=1)]),
        AlgorithmSolution(items=[KnapsackItem(id=get_random_string(), value=1, volume=1)]),
    ]
    await solution_suggestions_service_with_mocks.register_suggested_solutions(expected_solutions, knapsack_id)

    # noinspection PyUnresolvedReferences
    redis_mock.hset.assert_called_once()
    # noinspection PyUnresolvedReferences
    solution = SuggestedSolution(**json.loads(redis_mock.mock_calls[0].args[2]))

    assert expected_time == solution.time
    assert expected_solutions == [i for i in solution.solutions.values()]


@pytest.mark.asyncio
async def test_accept_suggested_solution(
    solution_suggestions_service_with_mocks: SuggestedSolutionsService,
    redis_mock: Redis,
    time_service_mock: TimeService,
    knapsack_id: str,
    claims_service_mock: ClaimsService,
    config: Config,
):
    expected_time = datetime.now()
    time_service_mock.now = MagicMock(return_value=expected_time)
    shared_item_between_solutions = KnapsackItem(id=get_random_string(), value=1, volume=1)
    expected_solution: list[KnapsackItem] = [
        KnapsackItem(id=get_random_string(), value=1, volume=1),
        shared_item_between_solutions,
    ]
    chosen_solution_id: str = get_random_string()
    first_released_item = KnapsackItem(id=get_random_string(), value=1, volume=1)
    second_released_item = KnapsackItem(id=get_random_string(), value=1, volume=1)
    all_solutions: dict[str, AlgorithmSolution] = {
        get_random_string(): AlgorithmSolution(items=[first_released_item, shared_item_between_solutions]),
        get_random_string(): AlgorithmSolution(items=[second_released_item]),
        chosen_solution_id: AlgorithmSolution(items=expected_solution),
    }
    solution_suggestions_service_with_mocks.get_solutions = AsyncMock(
        return_value=SuggestedSolution(solutions=all_solutions, time=expected_time)
    )
    claims_service_mock.claim_suggested_solutions = AsyncMock(return_value=True)
    claims_service_mock.release_items_claims = AsyncMock()
    claims_service_mock.release_claim_suggested_solutions = AsyncMock()
    redis_mock.rpush = AsyncMock()
    redis_mock.hdel = AsyncMock()

    result = await solution_suggestions_service_with_mocks.accept_suggested_solution(knapsack_id, chosen_solution_id)

    assert AcceptResult.ACCEPT_SUCCESS == result
    claims_service_mock.claim_suggested_solutions.assert_called_once_with(knapsack_id)
    solution_suggestions_service_with_mocks.get_solutions.assert_called_once_with(knapsack_id)
    claims_service_mock.release_items_claims.assert_called_once_with([first_released_item, second_released_item])
    claims_service_mock.release_claim_suggested_solutions.assert_called_once_with(knapsack_id)
    redis_mock.rpush.assert_called_once_with(
        config.accepted_solutions_list,
        AcceptedSolution(time=expected_time, solution=expected_solution, knapsack_id=knapsack_id).json(),
    )
    redis_mock.hdel.assert_called_once_with(config.suggested_solutions_hash, knapsack_id)


@pytest.mark.asyncio
async def test_accept_suggested_solution_solution_claim_failed(
    solution_suggestions_service_with_mocks: SuggestedSolutionsService,
    redis_mock: Redis,
    knapsack_id: str,
    claims_service_mock: ClaimsService,
):
    chosen_solution_id: str = get_random_string()
    claims_service_mock.claim_suggested_solutions = AsyncMock(return_value=False)
    claims_service_mock.release_items_claims = AsyncMock()
    claims_service_mock.release_claim_suggested_solutions = AsyncMock()

    result = await solution_suggestions_service_with_mocks.accept_suggested_solution(knapsack_id, chosen_solution_id)

    assert AcceptResult.CLAIM_FAILED == result
    claims_service_mock.claim_suggested_solutions.assert_called_once_with(knapsack_id)
    claims_service_mock.release_items_claims.assert_not_called()
    claims_service_mock.release_claim_suggested_solutions.assert_not_called()


@pytest.mark.asyncio
async def test_accept_suggested_solution_solution_deleted(
    solution_suggestions_service_with_mocks: SuggestedSolutionsService,
    redis_mock: Redis,
    knapsack_id: str,
    claims_service_mock: ClaimsService,
):
    chosen_solution_id: str = get_random_string()
    solution_suggestions_service_with_mocks.get_solutions = AsyncMock(return_value=None)
    claims_service_mock.claim_suggested_solutions = AsyncMock(return_value=True)
    claims_service_mock.release_items_claims = AsyncMock()
    claims_service_mock.release_claim_suggested_solutions = AsyncMock()
    redis_mock.rpush = AsyncMock()
    redis_mock.hdel = AsyncMock()

    result = await solution_suggestions_service_with_mocks.accept_suggested_solution(knapsack_id, chosen_solution_id)

    assert AcceptResult.SOLUTION_NOT_EXISTS == result
    claims_service_mock.claim_suggested_solutions.assert_called_once_with(knapsack_id)
    solution_suggestions_service_with_mocks.get_solutions.assert_called_once_with(knapsack_id)
    claims_service_mock.release_items_claims.assert_not_called()
    redis_mock.rpush.assert_not_called()
    redis_mock.hdel.assert_not_called()
    claims_service_mock.release_claim_suggested_solutions.assert_called_once_with(knapsack_id)


@pytest.mark.asyncio
async def test_is_solution_exists(solution_suggestions_service_with_mocks: SuggestedSolutionsService, knapsack_id: str):
    solution_id = get_random_string()
    suggested_solution = SuggestedSolution(
        time=datetime.now(), solutions={solution_id: AlgorithmSolution(items=[KnapsackItem(id=get_random_string(), volume=1, value=1)])}
    )
    solution_suggestions_service_with_mocks.get_solutions = AsyncMock(return_value=suggested_solution)

    is_solution_exists = await solution_suggestions_service_with_mocks.is_solution_exists(knapsack_id, solution_id)

    solution_suggestions_service_with_mocks.get_solutions.assert_called_once_with(knapsack_id)
    assert is_solution_exists is True


@pytest.mark.asyncio
async def test_is_solution_exists_suggestion_not_exists(
    solution_suggestions_service_with_mocks: SuggestedSolutionsService, knapsack_id: str
):
    solution_suggestions_service_with_mocks.get_solutions = AsyncMock(return_value=None)

    solution_id = get_random_string()
    is_solution_exists = await solution_suggestions_service_with_mocks.is_solution_exists(knapsack_id, solution_id)

    solution_suggestions_service_with_mocks.get_solutions.assert_called_once_with(knapsack_id)
    assert is_solution_exists is False


@pytest.mark.asyncio
async def test_is_solution_exists_suggestion_exists_solution_not_exists(
    solution_suggestions_service_with_mocks: SuggestedSolutionsService, knapsack_id: str
):
    suggested_solution = SuggestedSolution(
        time=datetime.now(), solutions={get_random_string(): AlgorithmSolution(items=[KnapsackItem(id=get_random_string(), volume=1, value=1)])}
    )
    solution_suggestions_service_with_mocks.get_solutions = AsyncMock(return_value=suggested_solution)

    solution_id = get_random_string()
    is_solution_exists = await solution_suggestions_service_with_mocks.is_solution_exists(knapsack_id, solution_id)

    solution_suggestions_service_with_mocks.get_solutions.assert_called_once_with(knapsack_id)
    assert is_solution_exists is False


@pytest.mark.asyncio
async def test_get_solutions(
    solution_suggestions_service_with_mocks: SuggestedSolutionsService,
    knapsack_id: str,
    redis_mock: Redis,
    config: Config,
):
    expected_solution = SuggestedSolution(
        time=datetime.now(), solutions={get_random_string(): AlgorithmSolution(items=[KnapsackItem(id=get_random_string(), volume=1, value=1)])}
    )
    redis_mock.hget = AsyncMock(return_value=expected_solution.json().encode())

    suggested_solution = await solution_suggestions_service_with_mocks.get_solutions(knapsack_id)

    redis_mock.hget.assert_called_once_with(config.suggested_solutions_hash, knapsack_id)
    assert expected_solution == suggested_solution


@pytest.mark.asyncio
async def test_get_solutions_solutions_not_exist(
    solution_suggestions_service_with_mocks: SuggestedSolutionsService,
    knapsack_id: str,
    redis_mock: Redis,
    config: Config,
):
    redis_mock.hget = AsyncMock(return_value=None)

    suggested_solution = await solution_suggestions_service_with_mocks.get_solutions(knapsack_id)

    redis_mock.hget.assert_called_once_with(config.suggested_solutions_hash, knapsack_id)
    assert suggested_solution is None


@pytest.mark.asyncio
async def test_reject_suggested_solutions(
    solution_suggestions_service_with_mocks: SuggestedSolutionsService,
    redis_mock: Redis,
    knapsack_id: str,
    claims_service_mock: ClaimsService,
    config: Config,
):
    first_released_item = KnapsackItem(id=get_random_string(), value=1, volume=1)
    second_released_item = KnapsackItem(id=get_random_string(), value=1, volume=1)
    all_solutions: dict[str, list[KnapsackItem]] = {
        get_random_string(): AlgorithmSolution(items=[first_released_item]),
        get_random_string(): AlgorithmSolution(items=[second_released_item]),
    }
    solution_suggestions_service_with_mocks.get_solutions = AsyncMock(
        return_value=SuggestedSolution(solutions=all_solutions, time=datetime.now())
    )
    claims_service_mock.claim_suggested_solutions = AsyncMock(return_value=True)
    claims_service_mock.release_items_claims = AsyncMock()
    claims_service_mock.release_claim_suggested_solutions = AsyncMock()
    redis_mock.hdel = AsyncMock()

    result = await solution_suggestions_service_with_mocks.reject_suggested_solutions(knapsack_id)

    assert RejectResult.REJECT_SUCCESS == result
    claims_service_mock.claim_suggested_solutions.assert_called_once_with(knapsack_id)
    solution_suggestions_service_with_mocks.get_solutions.assert_called_once_with(knapsack_id)
    claims_service_mock.release_items_claims.assert_called_once_with([first_released_item, second_released_item])
    redis_mock.hdel.assert_called_once_with(config.suggested_solutions_hash, knapsack_id)
    claims_service_mock.release_claim_suggested_solutions.assert_called_once_with(knapsack_id)


@pytest.mark.asyncio
async def test_reject_suggested_solution_solution_claim_failed(
    solution_suggestions_service_with_mocks: SuggestedSolutionsService,
    redis_mock: Redis,
    knapsack_id: str,
    claims_service_mock: ClaimsService,
):
    claims_service_mock.claim_suggested_solutions = AsyncMock(return_value=False)
    claims_service_mock.release_items_claims = AsyncMock()
    claims_service_mock.release_claim_suggested_solutions = AsyncMock()

    result = await solution_suggestions_service_with_mocks.reject_suggested_solutions(knapsack_id)

    assert RejectResult.CLAIM_FAILED == result
    claims_service_mock.claim_suggested_solutions.assert_called_once_with(knapsack_id)
    claims_service_mock.release_items_claims.assert_not_called()
    claims_service_mock.release_claim_suggested_solutions.assert_not_called()


@pytest.mark.asyncio
async def test_reject_suggested_solution_solution_deleted(
    solution_suggestions_service_with_mocks: SuggestedSolutionsService,
    redis_mock: Redis,
    knapsack_id: str,
    claims_service_mock: ClaimsService,
):
    solution_suggestions_service_with_mocks.get_solutions = AsyncMock(return_value=None)
    claims_service_mock.claim_suggested_solutions = AsyncMock(return_value=True)
    claims_service_mock.release_items_claims = AsyncMock()
    claims_service_mock.release_claim_suggested_solutions = AsyncMock()
    redis_mock.hdel = AsyncMock()

    result = await solution_suggestions_service_with_mocks.reject_suggested_solutions(knapsack_id)

    assert RejectResult.SUGGESTION_NOT_EXISTS == result
    claims_service_mock.claim_suggested_solutions.assert_called_once_with(knapsack_id)
    solution_suggestions_service_with_mocks.get_solutions.assert_called_once_with(knapsack_id)
    claims_service_mock.release_items_claims.assert_not_called()
    redis_mock.hdel.assert_not_called()
    claims_service_mock.release_claim_suggested_solutions.assert_called_once_with(knapsack_id)
