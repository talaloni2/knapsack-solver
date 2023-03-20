from unittest.mock import AsyncMock, MagicMock

import pytest

from logic.algorithm_runner import AlgorithmRunner
from logic.claims_service import ClaimsService
from logic.consumer.solver_instance_consumer import SolverInstanceConsumer
from logic.rabbit_channel_context import RabbitChannelContext
from logic.solution_reporter import SolutionReporter
from models.algorithms import Algorithms
from models.knapsack_item import KnapsackItem
from models.knapsack_solver_instance_dto import SolverInstanceRequest
from test.utils import get_random_string


@pytest.mark.asyncio
async def test_solver_consumer_claims(random_queue_name: str):
    expected_result = [KnapsackItem(id=get_random_string(), value=2, volume=1)]
    non_accepted_items = [KnapsackItem(id=get_random_string(), value=1, volume=1)]
    solution_request_items = expected_result + non_accepted_items
    request = SolverInstanceRequest(
        items=solution_request_items,
        volume=1,
        knapsack_id=get_random_string(),
        algorithm=Algorithms.FIRST_FIT,
    )

    channel_context = await _mock_channel_with_one_message_in_queue(request)
    items_claimer = AsyncMock(ClaimsService)
    items_claimer.claim_items = AsyncMock(return_value=solution_request_items)
    solution_reporter = AsyncMock(SolutionReporter)
    algorithm_runner = MagicMock(AlgorithmRunner)
    algorithm_runner.run_algorithm = MagicMock(return_value=expected_result)

    consumer = SolverInstanceConsumer(channel_context, algorithm_runner, items_claimer, solution_reporter)

    async with consumer:
        await consumer.start_consuming(random_queue_name)

    algorithm_runner.run_algorithm.assert_called_once()
    items_claimer.claim_items.assert_called_once()
    items_claimer.release_items_claims.assert_called_once_with(non_accepted_items)
    solution_reporter.report_solution_suggestions.assert_called_once()


async def _mock_channel_with_one_message_in_queue(request: SolverInstanceRequest):
    async def queue_iterator():
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
