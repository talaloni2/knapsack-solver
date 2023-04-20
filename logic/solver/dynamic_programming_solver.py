from logic.solver.base_solver import BaseSolver
from models.knapsack_item import KnapsackItem


class KnapsackCell:
    def __init__(self, total_value: int, items: list[KnapsackItem]):
        self.total_value: int = total_value
        self.items: list[KnapsackItem] = items

    def __lt__(self, other: 'KnapsackCell'):
        return self.total_value < other.total_value


class DynamicProgrammingSolver(BaseSolver):

    def solve(self, items: list[KnapsackItem], volume: int) -> list[KnapsackItem]:
        values = [i.value for i in items]
        volumes = [i.volume for i in items]
        return self._knapsack_dp(values, volumes, volume, items)

    @staticmethod
    def _knapsack_dp(values, weights, capacity, items: list[KnapsackItem]) -> list[KnapsackItem]:
        n = len(values)
        table: list[list[KnapsackCell]] = [[(KnapsackCell(0, [])) for _ in range(capacity + 1)] for _ in range(n + 1)]
        for i in range(1, n + 1):
            for j in range(1, capacity + 1):
                if weights[i - 1] > j:
                    table[i][j] = table[i - 1][j]
                else:
                    upper_option: KnapsackCell = table[i - 1][j]
                    upper_value_minus_current_weight: KnapsackCell = table[i - 1][j - weights[i - 1]]
                    new_option = KnapsackCell(upper_value_minus_current_weight.total_value + values[i - 1],
                                              upper_value_minus_current_weight.items + [items[i - 1]])
                    table[i][j] = max(upper_option, new_option)
        return table[n][capacity].items
