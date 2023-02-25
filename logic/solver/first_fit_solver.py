from logic.solver.base_solver import BaseSolver
from models.knapsack_item import KnapsackItem


class FitFirstSolver(BaseSolver):
    def solve(self, items: list[KnapsackItem], volume: int) -> list[KnapsackItem]:
        return [next(item for item in items if item.volume <= volume)]
