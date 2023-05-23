from datetime import timedelta
from unittest.mock import AsyncMock, call

import pytest
from aioredis import Redis

from logic.claims_service import ClaimsService
from logic.solution_maintainer import SolutionMaintainer
from logic.suggested_solution_service import SuggestedSolutionsService
from logic.time_service import TimeService
from models.config.configuration import Config
from models.knapsack_item import KnapsackItem
from models.solution import SuggestedSolution, AcceptedSolution, AlgorithmSolution
from models.suggested_solutions_actions_statuses import RejectResult
from test.utils import get_random_string


@pytest.fixture
async def solution_maintainer(
    solution_suggestions_service_with_mocks: SuggestedSolutionsService,
    redis_mock: Redis,
    time_service_mock: TimeService,
    claims_service_mock: ClaimsService,
    config: Config,
) -> SolutionMaintainer:
    return SolutionMaintainer(
        solution_suggestions_service_with_mocks,
        redis_mock,
        time_service_mock,
        claims_service_mock,
        config,
    )


class MockHscanIter:
    def __init__(self, *values):
        self._values = values
        self._pos = 0

    def __aiter__(self) -> "MockHscanIter":
        return self

    async def __anext__(self):
        if self._pos >= len(self._values):
            raise StopAsyncIteration
        val = self._values[self._pos]
        self._pos += 1
        return val.encode()

    def __call__(self, *args, **kwargs):
        return self


@pytest.mark.asyncio
async def test_clean_old_suggestions_sanity(
    solution_maintainer: SolutionMaintainer,
    time_service_mock: TimeService,
    redis_mock: Redis,
    knapsack_id: str,
    solution_suggestions_service_with_mocks,
    config: Config,
):
    redis_mock.hscan_iter = MockHscanIter(knapsack_id)
    expired_time = time_service_mock.now() - timedelta(config.suggestion_ttl_seconds + 1)
    expired_solution = SuggestedSolution(
        time=expired_time, solutions={get_random_string(): AlgorithmSolution(items=[])}
    )
    solution_suggestions_service_with_mocks.get_solutions = AsyncMock(return_value=expired_solution)
    solution_suggestions_service_with_mocks.reject_suggested_solutions = AsyncMock()

    await solution_maintainer.clean_old_suggestions()

    solution_suggestions_service_with_mocks.get_solutions.assert_called_once_with(knapsack_id)
    solution_suggestions_service_with_mocks.reject_suggested_solutions.assert_called_once_with(knapsack_id)


@pytest.mark.asyncio
async def test_clean_old_suggestions_no_suggestions_available(
    solution_maintainer: SolutionMaintainer,
    time_service_mock: TimeService,
    redis_mock: Redis,
    knapsack_id: str,
    solution_suggestions_service_with_mocks: SuggestedSolutionsService,
):
    redis_mock.hscan_iter = MockHscanIter()
    solution_suggestions_service_with_mocks.get_solutions = AsyncMock()
    solution_suggestions_service_with_mocks.reject_suggested_solutions = AsyncMock()

    await solution_maintainer.clean_old_suggestions()

    solution_suggestions_service_with_mocks.get_solutions.assert_not_called()
    solution_suggestions_service_with_mocks.reject_suggested_solutions.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("result", [RejectResult.CLAIM_FAILED, RejectResult.SUGGESTION_NOT_EXISTS])
async def test_clean_old_suggestions_error_result_still_working(
    result,
    solution_maintainer: SolutionMaintainer,
    time_service_mock: TimeService,
    redis_mock: Redis,
    knapsack_id: str,
    solution_suggestions_service_with_mocks: SuggestedSolutionsService,
    config: Config,
):
    redis_mock.hscan_iter = MockHscanIter(knapsack_id)
    expired_time = time_service_mock.now() - timedelta(config.suggestion_ttl_seconds + 1)
    expired_solution = SuggestedSolution(
        time=expired_time, solutions={get_random_string(): AlgorithmSolution(items=[])}
    )
    solution_suggestions_service_with_mocks.get_solutions = AsyncMock(return_value=expired_solution)
    solution_suggestions_service_with_mocks.reject_suggested_solutions = AsyncMock(return_value=result)

    await solution_maintainer.clean_old_suggestions()

    solution_suggestions_service_with_mocks.get_solutions.assert_called_once_with(knapsack_id)
    solution_suggestions_service_with_mocks.reject_suggested_solutions.assert_called_once_with(knapsack_id)


async def test_clean_old_suggestions_keep_non_expired_suggestions(
    solution_maintainer: SolutionMaintainer,
    time_service_mock: TimeService,
    redis_mock: Redis,
    knapsack_id: str,
    solution_suggestions_service_with_mocks: SuggestedSolutionsService,
    config: Config,
):
    non_expired_knapsack_id = get_random_string()
    redis_mock.hscan_iter = MockHscanIter(knapsack_id, non_expired_knapsack_id)
    expired_time = time_service_mock.now() - timedelta(config.suggestion_ttl_seconds + 1)
    expired_solution = SuggestedSolution(
        time=expired_time, solutions={get_random_string(): AlgorithmSolution(items=[])}
    )
    non_expired_time = time_service_mock.now()
    non_expired_solution = SuggestedSolution(
        time=non_expired_time, solutions={get_random_string(): AlgorithmSolution(items=[])}
    )
    solution_suggestions_service_with_mocks.get_solutions = AsyncMock(
        side_effect=[expired_solution, non_expired_solution]
    )
    solution_suggestions_service_with_mocks.reject_suggested_solutions = AsyncMock()

    await solution_maintainer.clean_old_suggestions()

    assert 2 == solution_suggestions_service_with_mocks.get_solutions.call_count
    solution_suggestions_service_with_mocks.get_solutions.assert_has_calls(
        [call(knapsack_id), call(non_expired_knapsack_id)]
    )
    solution_suggestions_service_with_mocks.reject_suggested_solutions.assert_called_once_with(knapsack_id)


@pytest.mark.asyncio
async def test_clean_old_accepted_solutions_delete_all_solutions(
    solution_maintainer: SolutionMaintainer,
    time_service_mock: TimeService,
    redis_mock: Redis,
    knapsack_id: str,
    solution_suggestions_service_with_mocks: SuggestedSolutionsService,
    claims_service_mock: ClaimsService,
    config: Config,
):
    expired_time = time_service_mock.now() - timedelta(seconds=config.accepted_solution_ttl_seconds + 1)
    first_expired_item = KnapsackItem(id=get_random_string(), value=1, volume=1)
    first_expired_sol = AcceptedSolution(time=expired_time, solution=[first_expired_item], knapsack_id=knapsack_id)
    second_expired_item = KnapsackItem(id=get_random_string(), value=1, volume=1)
    second_expired_sol = AcceptedSolution(time=expired_time, solution=[second_expired_item], knapsack_id=knapsack_id)
    redis_mock.lrange = AsyncMock(
        side_effect=[[first_expired_sol.json().encode()], [second_expired_sol.json().encode()], None]
    )
    redis_mock.lpop = AsyncMock()
    claims_service_mock.release_items_claims = AsyncMock()

    await solution_maintainer.clean_old_accepted_solutions()

    assert 3 == redis_mock.lrange.call_count
    assert 2 == redis_mock.lpop.call_count
    redis_mock.lpop.assert_has_calls([call(config.accepted_solutions_list)] * 2)
    assert 2 == claims_service_mock.release_items_claims.call_count
    claims_service_mock.release_items_claims.assert_has_calls([call([first_expired_item]), call([second_expired_item])])


@pytest.mark.asyncio
async def test_clean_old_accepted_solutions_encountered_live_solution_should_not_continue_iterating(
    solution_maintainer: SolutionMaintainer,
    time_service_mock: TimeService,
    redis_mock: Redis,
    knapsack_id: str,
    solution_suggestions_service_with_mocks: SuggestedSolutionsService,
    claims_service_mock: ClaimsService,
    config: Config,
):
    expired_time = time_service_mock.now() - timedelta(seconds=config.accepted_solution_ttl_seconds + 1)
    expired_item = KnapsackItem(id=get_random_string(), value=1, volume=1)
    expired_sol = AcceptedSolution(time=expired_time, solution=[expired_item], knapsack_id=knapsack_id)
    non_expired_time = time_service_mock.now()
    non_expired_item = KnapsackItem(id=get_random_string(), value=1, volume=1)
    non_expired_sol = AcceptedSolution(time=non_expired_time, solution=[non_expired_item], knapsack_id=knapsack_id)
    redis_mock.lrange = AsyncMock(side_effect=[[expired_sol.json().encode()], [non_expired_sol.json().encode()]])
    redis_mock.lpop = AsyncMock()
    claims_service_mock.release_items_claims = AsyncMock()

    await solution_maintainer.clean_old_accepted_solutions()

    assert 2 == redis_mock.lrange.call_count
    redis_mock.lpop.assert_called_once_with(config.accepted_solutions_list)
    claims_service_mock.release_items_claims.assert_called_once_with([expired_item])
