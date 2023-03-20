import asyncio

import pytest
from aioredis import Redis

from component_factory import get_wait_for_report_timeout_seconds
from logic.solution_report_waiter import SolutionReportWaiter
from models.solution import SolutionReport, SolutionReportCause


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "cause",
    [
        SolutionReportCause.SOLUTION_FOUND,
        SolutionReportCause.NO_ITEM_CLAIMED,
        SolutionReportCause.SUGGESTION_ALREADY_EXISTS,
    ],
)
async def test_solution_reports_waiter(
    cause: SolutionReportCause,
    redis_client: Redis,
    channel_prefix: str,
    knapsack_id: str,
    solution_reports_channel_name: str,
):
    waiter = SolutionReportWaiter(redis_client, channel_prefix, knapsack_id, get_wait_for_report_timeout_seconds())
    async with waiter:
        wait_task = asyncio.create_task(waiter.wait_for_solution_report())
        await redis_client.publish(solution_reports_channel_name, SolutionReport(cause=cause).json().encode())
        result: SolutionReport = await wait_task
    assert result.cause == cause


@pytest.mark.asyncio
async def test_solution_reports_waiter_got_timeout(
    redis_client: Redis,
    channel_prefix: str,
    knapsack_id: str,
    solution_reports_channel_name: str,
):
    waiter = SolutionReportWaiter(redis_client, channel_prefix, knapsack_id, 0.01)
    async with waiter:
        wait_task = asyncio.create_task(waiter.wait_for_solution_report())
        result: SolutionReport = await wait_task
    assert result.cause == SolutionReportCause.TIMEOUT
