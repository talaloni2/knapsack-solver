from models.algorithms import Algorithms
from models.base_model import BaseModel
from models.knapsack_item import KnapsackItem


class SolverInstanceRequest(BaseModel):
    items: list[KnapsackItem]
    volume: int
    knapsack_id: str
    algorithms: list[Algorithms]
