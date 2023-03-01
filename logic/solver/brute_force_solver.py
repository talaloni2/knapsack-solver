from ortools.algorithms.pywrapknapsack_solver import KnapsackSolver

from logic.solver.base_solver import BaseSolver
from models.knapsack_item import KnapsackItem


class BruteForceSolver(BaseSolver):
    def solve(self, items: list[KnapsackItem], volume: int) -> list[KnapsackItem]:
        solver = KnapsackSolver(KnapsackSolver.KNAPSACK_BRUTE_FORCE_SOLVER, "KnapsackExample")
        values = [i.value for i in items]
        volumes = [[i.volume for i in items]]
        capacities = [volume]

        solver.Init(values, volumes, capacities)
        solver.Solve()

        return [items[i] for i in range(len(values)) if solver.BestSolutionContains(i)]
