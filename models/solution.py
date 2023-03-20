from datetime import datetime
from enum import Enum

from models.base_model import BaseModel
from models.knapsack_item import KnapsackItem


class SolutionReportCause(str, Enum):
    NO_ITEM_CLAIMED = "no_item_claimed"
    SOLUTION_FOUND = "solution_found"
    SUGGESTION_ALREADY_EXISTS = "suggestion_already_exists"
    TIMEOUT = "timeout"


class SolutionReport(BaseModel):
    cause: SolutionReportCause


class SuggestedSolution(BaseModel):
    time: datetime
    solutions: dict[str, list[KnapsackItem]]


class AcceptedSolution(BaseModel):
    time: datetime
    solution: list[KnapsackItem]
    knapsack_id: str
