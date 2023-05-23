from unittest.mock import AsyncMock, MagicMock

import pytest

from logic.algorithm_runner import AlgorithmRunner
from logic.claims_service import ClaimsService
from logic.consumer.solver_instance_consumer import SolverInstanceConsumer
from logic.rabbit_channel_context import RabbitChannelContext
from logic.solution_reporter import SolutionReporter
from logic.suggested_solution_service import SuggestedSolutionsService
from models.algorithms import Algorithms
from models.config.configuration import Config
from models.knapsack_item import KnapsackItem
from models.knapsack_solver_instance_dto import SolverInstanceRequest
from models.solution import SolutionReportCause, AlgorithmSolution
from test.utils import get_random_string


@pytest.mark.asyncio
async def test_solver_consumer_claims(config: Config):
    expected_result = [KnapsackItem(id=get_random_string(), value=2, volume=1)]
    non_accepted_items = [KnapsackItem(id=get_random_string(), value=1, volume=1)]
    solution_request_items = expected_result + non_accepted_items
    request = SolverInstanceRequest(
        items=solution_request_items,
        volume=1,
        knapsack_id=get_random_string(),
        algorithms=[Algorithms.FIRST_FIT],
    )

    channel_context = await _mock_channel_with_messages(request)
    items_claimer = AsyncMock(ClaimsService)
    items_claimer.claim_items = AsyncMock(return_value=solution_request_items)
    solution_reporter = AsyncMock(SolutionReporter)
    algorithm_runner = MagicMock(AlgorithmRunner)
    algorithm_runner.run_algorithms = MagicMock(return_value=[expected_result])
    solution_suggestion_service = AsyncMock(SuggestedSolutionsService)
    solution_suggestion_service.get_solutions = AsyncMock(return_value=None)

    consumer = SolverInstanceConsumer(
        channel_context, algorithm_runner, items_claimer, solution_reporter, solution_suggestion_service
    )

    async with consumer:
        await consumer.start_consuming(config.solver_queue)

    algorithm_runner.run_algorithms.assert_called_once()
    items_claimer.claim_items.assert_called_once()
    items_claimer.release_items_claims.assert_called_once_with(non_accepted_items)
    solution_reporter.report_solution_suggestions.assert_called_once()


@pytest.mark.asyncio
async def test_solver_consumer_suggestion_already_exists(config: Config, knapsack_id: str):
    request = SolverInstanceRequest(
        items=[KnapsackItem(id=get_random_string(), value=1, volume=1)],
        volume=1,
        knapsack_id=knapsack_id,
        algorithms=[Algorithms.FIRST_FIT],
    )

    channel_context = await _mock_channel_with_messages(request)
    items_claimer = AsyncMock(ClaimsService)
    items_claimer.claim_items = AsyncMock()
    solution_reporter = AsyncMock(SolutionReporter)
    algorithm_runner = MagicMock(AlgorithmRunner)
    algorithm_runner.run_algorithm = MagicMock()
    solution_suggestion_service = AsyncMock(SuggestedSolutionsService)
    solution_suggestion_service.get_solutions = AsyncMock(return_value=["mock_existing_suggestion"])

    consumer = SolverInstanceConsumer(
        channel_context, algorithm_runner, items_claimer, solution_reporter, solution_suggestion_service
    )

    async with consumer:
        await consumer.start_consuming(config.solver_queue)

    solution_reporter.report_error.assert_called_once_with(knapsack_id, SolutionReportCause.SUGGESTION_ALREADY_EXISTS)
    algorithm_runner.run_algorithm.assert_not_called()
    items_claimer.claim_items.assert_not_called()
    items_claimer.release_items_claims.assert_not_called()
    solution_reporter.report_solution_suggestions.assert_not_called()


@pytest.mark.asyncio
async def test_solver_knapsack_already_running(config: Config, knapsack_id: str):
    expected_solution = [KnapsackItem(id=get_random_string(), value=1, volume=1)]
    request = SolverInstanceRequest(
        items=expected_solution,
        volume=1,
        knapsack_id=knapsack_id,
        algorithms=[Algorithms.FIRST_FIT],
    )

    channel_context = await _mock_channel_with_messages(request, request)
    claims_service = AsyncMock(ClaimsService)
    claims_service.claim_items = AsyncMock(return_value=expected_solution)
    claims_service.claim_running_knapsack = AsyncMock(side_effect=[True, False])
    claims_service.release_claim_running_knapsack = AsyncMock()
    solution_reporter = AsyncMock(SolutionReporter)
    algorithm_runner = MagicMock(AlgorithmRunner)
    algorithm_runner.run_algorithms = MagicMock(return_value=[expected_solution])
    solution_suggestion_service = AsyncMock(SuggestedSolutionsService)
    solution_suggestion_service.get_solutions = AsyncMock(return_value=None)

    consumer = SolverInstanceConsumer(
        channel_context, algorithm_runner, claims_service, solution_reporter, solution_suggestion_service
    )

    async with consumer:
        await consumer.start_consuming(config.solver_queue)

    solution_reporter.report_solution_suggestions.assert_called_once_with(
        [AlgorithmSolution(items=expected_solution)], knapsack_id
    )
    algorithm_runner.run_algorithms.assert_called_once_with(request.items, request.volume, request.algorithms)
    claims_service.claim_items.assert_called_once_with(request.items, request.volume, request.knapsack_id)
    claims_service.release_items_claims.assert_called_once_with([])
    claims_service.release_claim_running_knapsack.assert_called_once_with(knapsack_id)


async def _mock_channel_with_messages(*requests: SolverInstanceRequest):
    async def queue_iterator():
        for request in requests:
            message_mock = MagicMock()
            message_mock.body = request.json().encode()
            yield message_mock

    queue_mock = AsyncMock()
    queue_iterator_mock = AsyncMock()
    queue_iterator_mock.__aenter__ = AsyncMock(return_value=queue_iterator())
    queue_mock.iterator = MagicMock(return_value=queue_iterator_mock)
    channel_mock = AsyncMock()
    channel_mock.declare_queue = AsyncMock(return_value=queue_mock)
    channel_context = AsyncMock(RabbitChannelContext)
    channel_context.__aenter__ = AsyncMock(return_value=channel_mock)
    return channel_context
