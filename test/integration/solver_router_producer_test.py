import json

import aio_pika
import pytest

from logic.producer.solver_router_producer import SolverRouterProducer
from models.algorithms import Algorithms
from models.knapsack_item import KnapsackItem
from models.knapsack_solver_instance_dto import SolverInstanceRequest
from models.rabbit_connection_params import get_rabbit_connection_params
from test.utils import get_random_string


@pytest.fixture
async def random_queue_name(queues_cleaner: list) -> str:
    queue_name = get_random_string()
    queues_cleaner.append(queue_name)
    return queue_name


@pytest.mark.asyncio
async def test_solver_router_producer(random_queue_name: str):
    producer = SolverRouterProducer(get_rabbit_connection_params(), random_queue_name)
    expected_items = [KnapsackItem(id=get_random_string(), value=1, volume=1)]
    request = SolverInstanceRequest(
        items=expected_items,
        volume=1,
        knapsack_id=get_random_string(),
        algorithm=Algorithms.GREEDY,
    )
    async with producer:
        await producer.produce_solver_instance_request(request)

    produced_message = await _read_message_from_queue(random_queue_name)
    parsed_message = SolverInstanceRequest(**json.loads(produced_message))
    assert expected_items == parsed_message.items


# noinspection PyUnresolvedReferences
async def _read_message_from_queue(queue_name: str):
    host, port, user, password = get_rabbit_connection_params()
    connection = await aio_pika.connect_robust(
        f"amqp://{user}:{password}@{host}:{port}/",
    )

    async with connection:
        channel = await connection.channel()

        queue = await channel.declare_queue(queue_name)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    return message.body.decode()
