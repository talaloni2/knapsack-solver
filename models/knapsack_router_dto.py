from models.base_model import BaseModel
from models.knapsack_item import KnapsackItem


class RouterSolveRequest(BaseModel):
    items: list[KnapsackItem]
    volume: int
    knapsack_id: str


class RouterResolveResponse(BaseModel):
    items: list[KnapsackItem]
    knapsack_id: str
