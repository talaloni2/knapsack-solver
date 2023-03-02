import aio_pika
import pytest
from fastapi.testclient import TestClient

from models.rabbit_connection_params import get_rabbit_connection_params
from server import app
from test.utils import get_random_string


@pytest.fixture()
def test_client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
async def queues_cleaner() -> list[str]:
    host, port, user, password = get_rabbit_connection_params()
    connection = await aio_pika.connect_robust(
        f"amqp://{user}:{password}@{host}:{port}/",
    )

    async with connection:
        channel = await connection.channel()
        created_queues: list[str] = []
        yield created_queues

        for q in created_queues:
            await channel.queue_delete(q)


@pytest.fixture
async def random_queue_name(queues_cleaner: list) -> str:
    queue_name = get_random_string()
    queues_cleaner.append(queue_name)
    return queue_name
