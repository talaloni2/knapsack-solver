from logic.solver.brute_force_solver import BruteForceSolver
from models.knapsack_item import KnapsackItem
from test.utils import get_random_string


def test_brute_force_solver():
    solver = BruteForceSolver()
    expected_solution = [KnapsackItem(id=get_random_string(), value=5, volume=4)]
    items = [
        KnapsackItem(id=get_random_string(), value=2, volume=1),
        KnapsackItem(id=get_random_string(), value=2, volume=1),
        KnapsackItem(id=get_random_string(), value=2, volume=3),
    ] + expected_solution

    solution = solver.solve(items, 4)

    assert expected_solution == solution
