from ortools.algorithms import pywrapknapsack_solver

from logic.solver.branch_and_bound_solver import BranchAndBoundSolver
from models.knapsack_item import KnapsackItem
from test.utils import get_random_string


def test_branch_and_bound_solver():
    items = [
        KnapsackItem(id=get_random_string(), value=10, volume=2),
        KnapsackItem(id=get_random_string(), value=10, volume=4),
        KnapsackItem(id=get_random_string(), value=12, volume=6),
        KnapsackItem(id=get_random_string(), value=18, volume=9),
    ]
    capacity = 15
    solution = BranchAndBoundSolver().solve(items, capacity)
    expected_solution = [items[0], items[1], items[3]]

    assert solution == expected_solution


def test_knapsack_branch_and_bound_large():
    values = [12, 24, 10, 8, 22, 9, 15, 14, 6, 18, 5, 25, 23, 21, 27, 28, 19, 13, 26, 11]
    weights = [10, 15, 8, 7, 16, 7, 9, 8, 5, 13, 4, 18, 17, 14, 20, 21, 12, 9, 19, 6]
    items = [KnapsackItem(id=get_random_string(), volume=weights[i], value=values[i]) for i in range(len(weights))]
    capacity = 50

    res = BranchAndBoundSolver().solve(items, capacity)
    total_sum = sum(i.value for i in res)
    assert total_sum == 83
