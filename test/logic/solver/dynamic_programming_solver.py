from logic.solver.dynamic_programming_solver import DynamicProgrammingSolver
from models.knapsack_item import KnapsackItem
from test.utils import get_random_string


def test_knapsack_dp():
    items = [KnapsackItem(id=get_random_string(), volume=10, value=60),
             KnapsackItem(id=get_random_string(), volume=20, value=100),
             KnapsackItem(id=get_random_string(), volume=30, value=120)]
    capacity = 50
    result = DynamicProgrammingSolver().solve(items, capacity)
    assert items[1] in result
    assert items[2] in result


def test_knapsack_dp_empty():
    assert DynamicProgrammingSolver().solve([], 50) == []


def test_knapsack_dp_large():
    values = [12, 24, 10, 8, 22, 9, 15, 14, 6, 18, 5, 25, 23, 21, 27, 28, 19, 13, 26, 11]
    weights = [10, 15, 8, 7, 16, 7, 9, 8, 5, 13, 4, 18, 17, 14, 20, 21, 12, 9, 19, 6]
    items = [KnapsackItem(id=get_random_string(), volume=weights[i], value=values[i]) for i in range(len(weights))]
    capacity = 50
    res = DynamicProgrammingSolver().solve(items, capacity)
    total_sum = sum(i.value for i in res)
    assert total_sum == 83
