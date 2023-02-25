from logic.solver.greedy_solver import GreedySolver
from models.knapsack_item import KnapsackItem
from test.utils import get_random_string


def test_greedy_solver():
    solver = GreedySolver()
    expected_result = [KnapsackItem(id=get_random_string(), value=100, volume=1),
                       KnapsackItem(id=get_random_string(), value=200, volume=2),
                       KnapsackItem(id=get_random_string(), value=100, volume=1)]
    items = [KnapsackItem(id=get_random_string(), value=40, volume=2),
             KnapsackItem(id=get_random_string(), value=400, volume=4)] + expected_result
    available_volume = 4

    result = solver.solve(items, available_volume)

    assert len(result) == len(expected_result)
    assert {i.id for i in expected_result} == {i.id for i in result}


