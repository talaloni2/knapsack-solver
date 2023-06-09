from __future__ import annotations

from time import perf_counter_ns

from logger import logger
from logic.solver.base_solver import BaseSolver
from logic.solver.solver_loader import SolverLoader
from models.algorithms import Algorithms
from models.knapsack_item import KnapsackItem


class AlgorithmRunner:
    def __init__(self, solver_loader: SolverLoader):
        self._solver_loader = solver_loader

    def run_algorithms(
        self, items: list[KnapsackItem], volume: int, algorithms: list[Algorithms]
    ) -> list[list[KnapsackItem]]:
        return [self._run_algorithm(items, volume, alg) for alg in algorithms]

    def _run_algorithm(self, items: list[KnapsackItem], volume: int, algorithm: Algorithms) -> list[KnapsackItem]:
        start_time = perf_counter_ns()
        logger.info(f"Started running algorithm: {algorithm}")
        solver: BaseSolver = self._solver_loader.load(algorithm)
        solution = solver.solve(items, volume)
        end_time = perf_counter_ns()
        logger.info(f"Finished running algorithm: {algorithm}. took {int((end_time - start_time) / 1e6)} milliseconds")
        return solution
