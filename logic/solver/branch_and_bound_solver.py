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
        solver = pywrapknapsack_solver.KnapsackSolver(
            pywrapknapsack_solver.KnapsackSolver.KNAPSACK_MULTIDIMENSION_BRANCH_AND_BOUND_SOLVER, "BranchAndBound"
        )
        values = [i.value for i in items]
        weights = [[i.volume for i in items]]
        solver.Init(values, weights, [volume])
        solver.Solve()
        return [items[i] for i in range(len(values)) if solver.BestSolutionContains(i)]

    # def _bnb_solve(
    #     self,
    #     items: list[KnapsackItem],
    #     capacity: int,
    #     choosables: list[bool],
    #     upper_bound: int = sys.maxsize,
    #     index: int = 0,
    # ) -> Solution:
    #     chosen_items, cost, curr_upper_bound = self._choose_items(capacity, choosables, items)
    #
    #     if cost > upper_bound:
    #         return Solution([], sys.maxsize)
    #
    #     if index == len(items):
    #         return Solution(chosen_items, upper_bound)
    #
    #     res_with_idx = self._bnb_solve(
    #         items, capacity, choosables.copy(), min(upper_bound, curr_upper_bound), index + 1
    #     )
    #
    #     res_without_idx = self._bnb_solve(
    #         items,
    #         capacity,
    #         self._choosables_without_idx(choosables, index),
    #         min(upper_bound, curr_upper_bound, res_with_idx.upper_bound),
    #         index + 1,
    #     )
    #
    #     curr_res = Solution(chosen_items, upper_bound)
    #     return min(res_with_idx, res_without_idx, curr_res, key=lambda res: res.upper_bound)
    #
    # @staticmethod
    # def _choosables_without_idx(choosables, index):
    #     choosables_without_index = choosables.copy()
    #     choosables_without_index[index] = False
    #     return choosables_without_index
    #
    # @staticmethod
    # def _choose_items(capacity: int, choosables: list[bool], items: list[KnapsackItem]):
    #     curr_upper_bound = 0
    #     cost = 0
    #     chosen_items = []
    #     available_capacity = capacity
    #     for i, item in enumerate(items):
    #         if not choosables[i]:
    #             continue
    #         if item.volume > available_capacity:
    #             cost -= item.value * (available_capacity / item.volume)
    #             break
    #         cost -= item.value
    #         curr_upper_bound -= item.value
    #         chosen_items.append(item)
    #         available_capacity -= item.volume
    #     return chosen_items, cost, curr_upper_bound
