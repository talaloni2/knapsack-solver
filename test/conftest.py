import asyncio
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock

import aio_pika
import aioredis
import pytest
from aioredis import Redis
from httpx import AsyncClient

from component_factory import get_claims_service, get_config
from logic.claims_service import ClaimsService
from logic.suggested_solution_service import SuggestedSolutionsService
from logic.time_service import TimeService
from models.config.configuration import Config
from server import app
from test.utils import get_random_string


@pytest.fixture()
async def test_client() -> AsyncClient:
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def queues_cleaner() -> list[str]:
    host, port, user, password = get_config().rabbit_connection_params
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
async def hash_cleaner(redis_client):
    created_hashes = []
    yield created_hashes

    await redis_client.delete(*created_hashes)


@pytest.fixture
async def rabbit_channel() -> aio_pika.abc.AbstractChannel:
    host, port, user, password = get_config().rabbit_connection_params
    connection = await aio_pika.connect_robust(
        f"amqp://{user}:{password}@{host}:{port}/",
    )

    async with connection:
        yield await connection.channel()


@pytest.fixture
async def config(hash_cleaner, queues_cleaner) -> Config:
    original = get_config()
    return Config(
        server_port=8000,
        deployment_type=None,
        rabbit_connection_params=original.rabbit_connection_params,
        redis_connection_params=original.redis_connection_params,
        solver_queue=_append_random_string_to_cleaner(queues_cleaner),
        items_claim_hash=_append_random_string_to_cleaner(hash_cleaner),
        suggested_solutions_claims_hash=_append_random_string_to_cleaner(hash_cleaner),
        running_knapsack_claims_hash=_append_random_string_to_cleaner(hash_cleaner),
        solutions_channel_prefix=get_random_string(),
        wait_for_report_timeout_seconds=original.wait_for_report_timeout_seconds,
        suggested_solutions_hash=_append_random_string_to_cleaner(hash_cleaner),
        accepted_solutions_list=_append_random_string_to_cleaner(hash_cleaner),
        clean_old_suggestion_interval_seconds=original.clean_old_suggestion_interval_seconds,
        clean_old_accepted_solutions_interval_seconds=original.clean_old_accepted_solutions_interval_seconds,
        suggestion_ttl_seconds=original.suggestion_ttl_seconds,
        accepted_solution_ttl_seconds=original.accepted_solution_ttl_seconds,
        accepted_solutions_prefect_count=original.accepted_solutions_prefect_count,
        solvers_moderate_busy_threshold=original.solvers_moderate_busy_threshold,
        solvers_busy_threshold=original.solvers_busy_threshold,
        solvers_very_busy_threshold=original.solvers_very_busy_threshold,
        genetic_light_generations=original.genetic_light_generations,
        genetic_light_mutation_probability=original.genetic_light_mutation_probability,
        genetic_light_population=original.genetic_light_population,
        genetic_heavy_generations=original.genetic_heavy_generations,
        genetic_heavy_mutation_probability=original.genetic_heavy_mutation_probability,
        genetic_heavy_population=original.genetic_heavy_population,
        algo_decider_branch_and_bound_max_items=original.algo_decider_branch_and_bound_max_items,
        algo_decider_dynamic_programming_max_iterations=original.algo_decider_dynamic_programming_max_iterations,
    )


@pytest.fixture
async def solver_queue(config: Config, rabbit_channel: aio_pika.abc.AbstractChannel) -> aio_pika.abc.AbstractQueue:
    return await rabbit_channel.declare_queue(config.solver_queue)


def _append_random_string_to_cleaner(cleaner: list[str]):
    name = get_random_string()
    cleaner.append(name)
    return name


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
def solution_reports_channel_name(config: Config, knapsack_id: str):
    return f"{config.solutions_channel_prefix}:{knapsack_id}"


@pytest.fixture
async def redis_subscriber(redis_client: Redis, solution_reports_channel_name: str) -> aioredis.client.PubSub:
    async with redis_client.pubsub() as pubsub:
        await pubsub.subscribe(solution_reports_channel_name)
        yield pubsub
        await pubsub.unsubscribe(solution_reports_channel_name)


@pytest.fixture
def redis_client() -> aioredis.Redis:
    host, port = get_config().redis_connection_params
    return aioredis.from_url(f"redis://{host}:{port}")


@pytest.fixture
def claims_service(config: Config, redis_client) -> ClaimsService:
    return get_claims_service(redis_client, config)


@pytest.fixture
def time_service_mock() -> MagicMock:
    m = MagicMock(TimeService)
    m.now = MagicMock(return_value=datetime.now())
    return m


@pytest.fixture
def solution_suggestions_service(
    hash_cleaner,
    redis_client,
    claims_service,
    time_service_mock,
    config: Config,
) -> SuggestedSolutionsService:
    return SuggestedSolutionsService(
        redis_client, claims_service, time_service_mock, config.suggested_solutions_hash, config.accepted_solutions_list
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
    redis_mock: Redis, claims_service_mock: ClaimsService, time_service_mock: TimeService, config: Config
) -> SuggestedSolutionsService:
    return SuggestedSolutionsService(
        redis_mock,
        claims_service_mock,
        time_service_mock,
        config.suggested_solutions_hash,
        config.accepted_solutions_list,
    )
