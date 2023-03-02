import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from logic.algorithm_runner import AlgorithmRunner
from logic.consumer.solver_instance_consumer import SolverInstanceConsumer
from logic.items_claimer import ItemsClaimer
from logic.producer.solver_router_producer import SolverRouterProducer
from logic.solution_reporter import SolutionReporter
from models.algorithms import Algorithms
from models.knapsack_item import KnapsackItem
from models.knapsack_solver_instance_dto import SolverInstanceRequest
from models.rabbit_connection_params import get_rabbit_connection_params
from test.utils import get_random_string


@pytest.mark.asyncio
async def test_solver_consumer(random_queue_name: str):
    expected_result = [KnapsackItem(id=get_random_string(), value=1, volume=1)]
    request = SolverInstanceRequest(
        items=expected_result,
        volume=1,
        knapsack_id=get_random_string(),
        algorithm=Algorithms.FIRST_FIT,
    )

    producer = SolverRouterProducer(get_rabbit_connection_params(), random_queue_name)
    async with producer:
        await producer.produce_solver_instance_request(request)

    items_claimer = AsyncMock(ItemsClaimer)
    solution_reporter = AsyncMock(SolutionReporter)
    algorithm_runner = MagicMock(AlgorithmRunner)

    consumer = SolverInstanceConsumer(
        get_rabbit_connection_params(),
        algorithm_runner,
        items_claimer,
        solution_reporter,
    )

    async with consumer:
        consume_task = asyncio.create_task(consumer.start_consuming(random_queue_name))
        await asyncio.sleep(1)
        consume_task.cancel()

    algorithm_runner.run_algorithm.assert_called_once()
    items_claimer.claim_items.assert_called_once()
    solution_reporter.report_solutions.assert_called_once()
