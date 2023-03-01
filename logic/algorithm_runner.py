from fastapi import Depends

from logic.solver.base_solver import BaseSolver
from logic.solver.solver_loader import SolverLoader
from models.algorithms import Algorithms
from models.knapsack_item import KnapsackItem


def get_algorithm_runner():
    return AlgorithmRunner(SolverLoader())


class AlgorithmRunner:
    def __init__(self, solver_loader: SolverLoader):
        self._solver_loader = solver_loader

    def run_algorithm(self, items: list[KnapsackItem], volume: int, algorithm: Algorithms) -> list[KnapsackItem]:
        solver: BaseSolver = self._solver_loader.load(algorithm)
        items = self._claim_items(items, volume)
        solution = solver.solve(items, volume)
        self._report_solution(solution)
        return solution

    def _report_solution(self, items: list[KnapsackItem]):
        """STUB"""
        pass

    def _claim_items(self, items: list[KnapsackItem], volume: int) -> list[KnapsackItem]:
        """STUB"""
        return [i for i in items if i.volume <= volume]
