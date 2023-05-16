from models.base_model import BaseModel
from models.knapsack_item import KnapsackItem
from models.suggested_solutions_actions_statuses import AcceptResult, RejectResult


class RouterSolveRequest(BaseModel):
    items: list[KnapsackItem]
    volume: int
    knapsack_id: str


class RouterResolveResponse(BaseModel):
    items: list[KnapsackItem]
    knapsack_id: str


class AcceptSolutionRequest(BaseModel):
    solution_id: str
    knapsack_id: str


class AcceptSolutionResponse(BaseModel):
    result: AcceptResult


class RejectSolutionsRequest(BaseModel):
    knapsack_id: str


class RejectSolutionResponse(BaseModel):
    result: RejectResult


class ItemClaimedResponse(BaseModel):
    is_claimed: bool
