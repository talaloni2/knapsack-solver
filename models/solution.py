from datetime import datetime
from enum import Enum

from models.algorithms import Algorithms
from models.base_model import BaseModel
from models.knapsack_item import KnapsackItem


class SolutionReportCause(str, Enum):
    NO_ITEM_CLAIMED = "no_item_claimed"
    SOLUTION_FOUND = "solution_found"
    SUGGESTION_ALREADY_EXISTS = "suggestion_already_exists"
    TIMEOUT = "timeout"
    GOT_EXCEPTION = "exception"


class SolutionReport(BaseModel):
    cause: SolutionReportCause


class AlgorithmSolution(BaseModel):
    algorithm: Algorithms = Algorithms.FIRST_FIT
    items: list[KnapsackItem]


class SuggestedSolution(BaseModel):
    time: datetime
    solutions: dict[str, AlgorithmSolution]


class AcceptedSolution(BaseModel):
    time: datetime
    solution: list[KnapsackItem]
    knapsack_id: str
