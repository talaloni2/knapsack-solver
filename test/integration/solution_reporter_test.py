import json
from uuid import uuid4

import aioredis
import pytest

from component_factory import get_redis_connection_params, get_solution_reporter
from models.knapsack_item import KnapsackItem
from models.solution import SolutionReport, SolutionReportCause, SuggestedSolution
from test.utils import get_random_string


@pytest.fixture
def knapsack_id() -> str:
    return get_random_string()


@pytest.fixture
def channel_prefix() -> str:
    return "solutions_test"


@pytest.fixture
def solution_suggestions_hash_name(hash_cleaner) -> str:
    hash_name = str(uuid4())
    hash_cleaner.append(hash_name)
    return hash_name


@pytest.fixture
async def redis_subscriber(channel_prefix: str, knapsack_id: str) -> aioredis.client.PubSub:
    host, port = get_redis_connection_params()
    redis = aioredis.from_url(f"redis://{host}:{port}")

    async with redis.pubsub() as pubsub:
        channel_name: str = f"{channel_prefix}:{knapsack_id}"
        await pubsub.subscribe(channel_name)
        yield pubsub
        await pubsub.unsubscribe(channel_name)


@pytest.fixture
def redis_client() -> aioredis.Redis:
    host, port = get_redis_connection_params()
    return aioredis.from_url(f"redis://{host}:{port}")


@pytest.mark.asyncio
async def test_solution_reporter_report_suggestion(
    redis_subscriber, redis_client, channel_prefix, knapsack_id, solution_suggestions_hash_name
):
    solution_reporter = get_solution_reporter(
        solutions_channel_prefix=channel_prefix, solution_suggestions_hash_name=solution_suggestions_hash_name
    )
    expected_solutions = [[KnapsackItem(id=get_random_string(), value=1, volume=1)]]
    expected_response = SolutionReport(cause=SolutionReportCause.SOLUTION_FOUND)

    await solution_reporter.report_solution_suggestions(expected_solutions, knapsack_id)
    msg = None
    while not msg:
        msg = await redis_subscriber.get_message(ignore_subscribe_messages=True)
    response = SolutionReport(**json.loads(msg["data"].decode()))
    suggested_solution = SuggestedSolution(
        **json.loads((await redis_client.hget(solution_suggestions_hash_name, knapsack_id)).decode())
    )
    solutions_without_ids = [s for s in suggested_solution.solutions.values()]

    assert expected_response == response
    assert expected_solutions == solutions_without_ids


@pytest.mark.asyncio
async def test_solution_reporter_report_error(
    redis_subscriber, redis_client, channel_prefix, knapsack_id, solution_suggestions_hash_name
):
    solution_reporter = get_solution_reporter(
        solutions_channel_prefix=channel_prefix, solution_suggestions_hash_name=solution_suggestions_hash_name
    )
    expected_response = SolutionReport(cause=SolutionReportCause.NO_ITEM_CLAIMED)

    await solution_reporter.report_error(knapsack_id, SolutionReportCause.NO_ITEM_CLAIMED)
    msg = None
    while not msg:
        msg = await redis_subscriber.get_message(ignore_subscribe_messages=True)
    response = SolutionReport(**json.loads(msg["data"].decode()))
    suggested_solutions = await redis_client.hget(solution_suggestions_hash_name, knapsack_id)

    assert expected_response == response
    assert suggested_solutions is None
