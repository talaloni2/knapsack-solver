from enum import Enum

from models.base_model import BaseModel
from models.knapsack_item import KnapsackItem


class SolutionReportCause(str, Enum):
    NO_ITEM_CLAIMED = "no_item_claimed"
    SOLUTION_FOUND = "solution_found"


class SolutionReport(BaseModel):
    solutions: list[list[KnapsackItem]]
    cause: SolutionReportCause
