from __future__ import annotations
from logic.solver.base_solver import BaseSolver
from logic.solver.solver_loader import SolverLoader
from models.algorithms import Algorithms
from models.knapsack_item import KnapsackItem


class AlgorithmRunner:
    def __init__(self, solver_loader: SolverLoader):
        self._solver_loader = solver_loader

    def run_algorithm(self, items: list[KnapsackItem], volume: int, algorithm: Algorithms) -> list[KnapsackItem]:
        solver: BaseSolver = self._solver_loader.load(algorithm)
        solution = solver.solve(items, volume)
        return solution
