import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from logic.algorithm_runner import AlgorithmRunner
from logic.consumer.solver_instance_consumer import SolverInstanceConsumer
from logic.claims_service import ClaimsService
from logic.producer.solver_router_producer import SolverRouterProducer
from logic.solution_reporter import SolutionReporter
from logic.suggested_solution_service import SuggestedSolutionsService
from models.algorithms import Algorithms
from models.config.configuration import Config
from models.knapsack_item import KnapsackItem
from models.knapsack_solver_instance_dto import SolverInstanceRequest
from component_factory import get_rabbit_channel_context
from test.utils import get_random_string


@pytest.mark.asyncio
async def test_solver_consumer_consume(config: Config):
    expected_result = [KnapsackItem(id=get_random_string(), value=2, volume=1)]
    non_accepted_items = [KnapsackItem(id=get_random_string(), value=1, volume=1)]
    request = SolverInstanceRequest(
        items=expected_result + non_accepted_items,
        volume=1,
        knapsack_id=get_random_string(),
        algorithm=Algorithms.FIRST_FIT,
    )

    producer = SolverRouterProducer(config.rabbit_connection_params, config.solver_queue)
    async with producer:
        await producer.produce_solver_instance_request(request)

    items_claimer = AsyncMock(ClaimsService)
    solution_reporter = AsyncMock(SolutionReporter)
    algorithm_runner = MagicMock(AlgorithmRunner)
    solution_suggestion_service = AsyncMock(SuggestedSolutionsService)
    solution_suggestion_service.get_solutions = AsyncMock(return_value=None)

    consumer = SolverInstanceConsumer(
        get_rabbit_channel_context(),
        algorithm_runner,
        items_claimer,
        solution_reporter,
        solution_suggestion_service,
    )

    async with consumer:
        consume_task = asyncio.create_task(consumer.start_consuming(config.solver_queue))
        await asyncio.sleep(1)
        consume_task.cancel()

    algorithm_runner.run_algorithm.assert_called_once()
    items_claimer.claim_items.assert_called_once()
    items_claimer.release_items_claims.assert_called_once()
    solution_reporter.report_solution_suggestions.assert_called_once()
