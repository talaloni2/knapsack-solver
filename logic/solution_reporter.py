from __future__ import annotations

from aioredis import Redis

from logic.suggested_solution_service import SuggestedSolutionsService
from models.solution import SolutionReportCause, SolutionReport, AlgorithmSolution


class SolutionReporter:
    def __init__(
        self, redis: Redis, solutions_channel_prefix: str, suggested_solution_service: SuggestedSolutionsService
    ):
        self._redis = redis
        self._solutions_channel_prefix = solutions_channel_prefix
        self._suggested_solution_service = suggested_solution_service

    async def report_solution_suggestions(self, solutions: list[AlgorithmSolution], knapsack_id: str):
        solution_report = SolutionReport(cause=SolutionReportCause.SOLUTION_FOUND)
        await self._suggested_solution_service.register_suggested_solutions(solutions, knapsack_id)
        await self._redis.publish(self._channel_name(knapsack_id), solution_report.json())

    async def report_error(self, knapsack_id: str, error: SolutionReportCause):
        solution_report = SolutionReport(cause=error)
        await self._redis.publish(self._channel_name(knapsack_id), solution_report.json())

    def _channel_name(self, knapsack_id: str):
        return f"{self._solutions_channel_prefix}:{knapsack_id}"
