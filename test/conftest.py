import asyncio
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock
from uuid import uuid4

import aio_pika
import aioredis
import pytest
from aioredis import Redis
from fastapi.testclient import TestClient
from httpx import AsyncClient

from component_factory import get_rabbit_connection_params, get_redis_connection_params, get_claims_service
from logic.claims_service import ClaimsService
from logic.suggested_solution_service import SuggestedSolutionsService
from logic.time_service import TimeService
from server import app
from test.utils import get_random_string


@pytest.fixture()
async def test_client() -> AsyncClient:
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


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
async def hash_cleaner(redis_client):
    created_hashes = []
    yield created_hashes

    await redis_client.delete(*created_hashes)


@pytest.fixture
async def items_claim_hash_name(hash_cleaner: list) -> str:
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


@pytest.fixture
def knapsack_id() -> str:
    return get_random_string()


@pytest.fixture
def channel_prefix() -> str:
    return "solutions_test"


@pytest.fixture
def solution_reports_channel_name(channel_prefix: str, knapsack_id: str):
    return f"{channel_prefix}:{knapsack_id}"


@pytest.fixture
async def redis_subscriber(redis_client: Redis, solution_reports_channel_name: str) -> aioredis.client.PubSub:
    async with redis_client.pubsub() as pubsub:
        await pubsub.subscribe(solution_reports_channel_name)
        yield pubsub
        await pubsub.unsubscribe(solution_reports_channel_name)


@pytest.fixture
def redis_client() -> aioredis.Redis:
    host, port = get_redis_connection_params()
    return aioredis.from_url(f"redis://{host}:{port}")


@pytest.fixture
def claims_service(hash_cleaner, redis_client) -> ClaimsService:
    items_claim_hash_name: str = get_random_string()
    suggested_solutions_claims_hash_name: str = get_random_string()
    hash_cleaner.append(items_claim_hash_name)
    hash_cleaner.append(suggested_solutions_claims_hash_name)
    return get_claims_service(redis_client, items_claim_hash_name, suggested_solutions_claims_hash_name)


@pytest.fixture
def time_service_mock() -> MagicMock:
    m = MagicMock(TimeService)
    m.now = MagicMock(return_value=datetime.now())
    return m


@pytest.fixture
def suggested_solutions_hash_name(hash_cleaner) -> str:
    suggested_solutions_hash_name = get_random_string()
    hash_cleaner.append(suggested_solutions_hash_name)
    return suggested_solutions_hash_name


@pytest.fixture
def accepted_solutions_list_name(hash_cleaner) -> str:
    accepted_solutions_list_name = get_random_string()
    hash_cleaner.append(accepted_solutions_list_name)
    return accepted_solutions_list_name


@pytest.fixture
def solution_suggestions_service(
    hash_cleaner,
    redis_client,
    claims_service,
    time_service_mock,
    suggested_solutions_hash_name,
    accepted_solutions_list_name,
) -> SuggestedSolutionsService:
    return SuggestedSolutionsService(
        redis_client, claims_service, time_service_mock, suggested_solutions_hash_name, accepted_solutions_list_name
    )


@pytest.fixture
def claims_service_mock() -> ClaimsService:
    return AsyncMock(ClaimsService)


@pytest.fixture
def redis_mock() -> AsyncMock:
    mock = AsyncMock(Redis)
    mock.hset = AsyncMock()
    return mock


@pytest.fixture
def solution_suggestions_service_with_mocks(
    redis_mock: Redis,
    claims_service_mock: ClaimsService,
    time_service_mock: TimeService,
    suggested_solutions_hash_name: str,
    accepted_solutions_list_name: str,
) -> SuggestedSolutionsService:
    return SuggestedSolutionsService(
        redis_mock, claims_service_mock, time_service_mock, suggested_solutions_hash_name, accepted_solutions_list_name
    )
