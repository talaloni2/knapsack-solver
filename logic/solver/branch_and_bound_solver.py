import sys
from typing import NamedTuple

from ortools.algorithms import pywrapknapsack_solver

from logic.solver.base_solver import BaseSolver
from models.knapsack_item import KnapsackItem


class Solution(NamedTuple):
    items: list[KnapsackItem]
    upper_bound: int


class BranchAndBoundSolver(BaseSolver):
    def solve(self, items: list[KnapsackItem], volume: int) -> list[KnapsackItem]:
        if any(i.value < 0 for i in items):
            return []
        solver = pywrapknapsack_solver.KnapsackSolver(
            pywrapknapsack_solver.KnapsackSolver.KNAPSACK_MULTIDIMENSION_BRANCH_AND_BOUND_SOLVER, "BranchAndBound"
        )
        values = [i.value for i in items]
        weights = [[i.volume for i in items]]
        solver.Init(values, weights, [volume])
        solver.Solve()
        return [items[i] for i in range(len(values)) if solver.BestSolutionContains(i)]
