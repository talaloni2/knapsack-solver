import asyncio

import pytest
from aioredis import Redis

from logic.solution_report_waiter import SolutionReportWaiter
from models.solution import SolutionReport, SolutionReportCause


@pytest.mark.asyncio
@pytest.mark.parametrize("cause", [SolutionReportCause.SOLUTION_FOUND, SolutionReportCause.NO_ITEM_CLAIMED])
async def test_solution_reports_waiter(
    cause: SolutionReportCause,
    redis_client: Redis,
    channel_prefix: str,
    knapsack_id: str,
    solution_reports_channel_name: str,
):
    waiter = SolutionReportWaiter(redis_client, channel_prefix, knapsack_id)
    async with waiter:
        wait_task = asyncio.create_task(waiter.wait_for_solution_report())
        await redis_client.publish(solution_reports_channel_name, SolutionReport(cause=cause).json().encode())
        result: SolutionReport = await wait_task
    assert cause == result.cause
