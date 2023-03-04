from __future__ import annotations

from aioredis import Redis

from models.knapsack_item import KnapsackItem
from models.solution_report import SolutionReportCause, SolutionReport


class SolutionReporter:
    def __init__(self, redis: Redis, solutions_channel_prefix: str):
        self._redis = redis
        self._solutions_channel_prefix = solutions_channel_prefix

    async def report_solution_suggestions(self, solutions: list[list[KnapsackItem]], knapsack_id: str):
        solution_report = SolutionReport(solutions=solutions, cause=SolutionReportCause.SOLUTION_FOUND)
        await self._redis.publish(self._channel_name(knapsack_id), solution_report.json())

    async def report_error(self, knapsack_id: str, error: SolutionReportCause):
        solution_report = SolutionReport(solutions=[], cause=error)
        await self._redis.publish(self._channel_name(knapsack_id), solution_report.json())

    def _channel_name(self, knapsack_id: str):
        return f"{self._solutions_channel_prefix}:{knapsack_id}"
