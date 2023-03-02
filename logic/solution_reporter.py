from __future__ import annotations
from enum import Enum

from models.knapsack_item import KnapsackItem


class SolutionReportCause(str, Enum):
    NO_ITEM_CLAIMED = "no_item_claimed"
    SOLUTION_FOUND = "solution_found"


def get_solution_reporter() -> SolutionReporter:
    return SolutionReporter()


class SolutionReporter:
    async def report_solutions(self, solutions: list[list[KnapsackItem]], knapsack_id: str):
        """STUB"""
        pass

    async def report_error(self, knapsack_id: str, error: SolutionReportCause):
        pass
