import json

import aioredis
import pytest

from component_factory import get_redis_connection_params, get_solution_reporter
from models.knapsack_item import KnapsackItem
from models.solution_report import SolutionReport, SolutionReportCause
from test.utils import get_random_string


@pytest.fixture
def knapsack_id() -> str:
    return get_random_string()


@pytest.fixture
def channel_prefix() -> str:
    return "solutions_test"


@pytest.fixture
async def redis_subscriber(channel_prefix: str, knapsack_id: str) -> aioredis.client.PubSub:
    host, port = get_redis_connection_params()
    redis = aioredis.from_url(f"redis://{host}:{port}")

    async with redis.pubsub() as pubsub:
        channel_name: str = f"{channel_prefix}:{knapsack_id}"
        await pubsub.subscribe(channel_name)
        yield pubsub
        await pubsub.unsubscribe(channel_name)


@pytest.mark.asyncio
async def test_solution_reporter_report_suggestion(redis_subscriber, channel_prefix, knapsack_id):
    solution_reporter = get_solution_reporter(solutions_channel_prefix=channel_prefix)
    expected_solutions = [[KnapsackItem(id=get_random_string(), value=1, volume=1)]]
    expected_response = SolutionReport(solutions=expected_solutions, cause=SolutionReportCause.SOLUTION_FOUND)

    await solution_reporter.report_solution_suggestions(expected_solutions, knapsack_id)
    msg = None
    while not msg:
        msg = await redis_subscriber.get_message(ignore_subscribe_messages=True)
    response = SolutionReport(**json.loads(msg["data"].decode()))

    assert expected_response == response


@pytest.mark.asyncio
async def test_solution_reporter_report_error(redis_subscriber, channel_prefix, knapsack_id):
    solution_reporter = get_solution_reporter(solutions_channel_prefix=channel_prefix)
    expected_solutions = []
    expected_response = SolutionReport(solutions=expected_solutions, cause=SolutionReportCause.NO_ITEM_CLAIMED)

    await solution_reporter.report_error(knapsack_id, SolutionReportCause.NO_ITEM_CLAIMED)
    msg = None
    while not msg:
        msg = await redis_subscriber.get_message(ignore_subscribe_messages=True)
    response = SolutionReport(**json.loads(msg["data"].decode()))

    assert expected_response == response
