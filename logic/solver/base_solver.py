from models.knapsack_item import KnapsackItem


class BaseSolver:
    def solve(self, items: list[KnapsackItem], volume: int) -> list[KnapsackItem]:
        raise NotImplementedError()
