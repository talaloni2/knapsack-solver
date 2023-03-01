from logic.solver.first_fit_solver import FitFirstSolver
from models.knapsack_item import KnapsackItem
from test.utils import get_random_string


def test_fit_first_solver():
    solver = FitFirstSolver()
    expected_results = [KnapsackItem(id=get_random_string(), value=10, volume=2)]
    items = (
        [KnapsackItem(id=get_random_string(), value=50, volume=5)]
        + expected_results
        + [KnapsackItem(id=get_random_string(), value=50, volume=4)]
    )
    available_volume = 4

    result = solver.solve(items, available_volume)

    assert expected_results == result
