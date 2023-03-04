import asyncio

import aio_pika
import aioredis
import pytest
from fastapi.testclient import TestClient

from component_factory import get_rabbit_connection_params, get_redis_connection_params
from server import app
from test.utils import get_random_string


@pytest.fixture()
def test_client() -> TestClient:
    return TestClient(app)


@pytest.fixture
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


@pytest.fixture
async def hash_cleaner():
    host, port = get_redis_connection_params()
    redis = aioredis.from_url(f"redis://{host}:{port}")

    created_hashes = []
    yield created_hashes

    await redis.delete(*created_hashes)


@pytest.fixture
async def random_hash_name(hash_cleaner: list) -> str:
    hash_name = get_random_string()
    hash_cleaner.append(hash_name)
    return hash_name


@pytest.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()
