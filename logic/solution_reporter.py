from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from aioredis import Redis

from models.knapsack_item import KnapsackItem
from models.solution import SolutionReportCause, SolutionReport, SuggestedSolution


class SolutionReporter:
    def __init__(self, redis: Redis, solutions_channel_prefix: str, solution_suggestions_hash_name: str):
        self._redis = redis
        self._solutions_channel_prefix = solutions_channel_prefix
        self._solution_suggestions_hash_name = solution_suggestions_hash_name

    async def report_solution_suggestions(self, solutions: list[list[KnapsackItem]], knapsack_id: str):
        solution_report = SolutionReport(cause=SolutionReportCause.SOLUTION_FOUND)
        solution_suggestion = SuggestedSolution(
            time=datetime.now(), solutions=self._assign_ids_to_suggested_solutions(solutions)
        )
        await self._redis.hset(self._solution_suggestions_hash_name, knapsack_id, solution_suggestion.json())
        await self._redis.publish(self._channel_name(knapsack_id), solution_report.json())

    async def report_error(self, knapsack_id: str, error: SolutionReportCause):
        solution_report = SolutionReport(cause=error)
        await self._redis.publish(self._channel_name(knapsack_id), solution_report.json())

    def _channel_name(self, knapsack_id: str):
        return f"{self._solutions_channel_prefix}:{knapsack_id}"

    @staticmethod
    def _assign_ids_to_suggested_solutions(solutions: list[list[KnapsackItem]]) -> dict[str, list[KnapsackItem]]:
        return {str(uuid4()): sol for sol in solutions}
