import pytest

from logic.solver.genetic_solver import GeneticSolver
from models.knapsack_item import KnapsackItem
from test.utils import get_random_string


@pytest.mark.flaky(retries=2, delay=0)
def test_genetic_solver():
    items = [
        KnapsackItem(id=get_random_string(), volume=1, value=2),
        KnapsackItem(id=get_random_string(), volume=2, value=4),
        KnapsackItem(id=get_random_string(), volume=3, value=4),
        KnapsackItem(id=get_random_string(), volume=4, value=5),
        KnapsackItem(id=get_random_string(), volume=5, value=7),
        KnapsackItem(id=get_random_string(), volume=6, value=9),
    ]
    res = [sum(k.value for k in GeneticSolver(80, 0.2, 80).solve(items, 10)) for _ in range(20)]
    assert all(r in (14, 15) for r in res)


@pytest.mark.flaky(retries=2, delay=0)
def test_genetic_solver_large():
    values = [12, 24, 10, 8, 22, 9, 15, 14, 6, 18, 5, 25, 23, 21, 27, 28, 19, 13, 26, 11]
    weights = [10, 15, 8, 7, 16, 7, 9, 8, 5, 13, 4, 18, 17, 14, 20, 21, 12, 9, 19, 6]
    items = [KnapsackItem(id=get_random_string(), volume=weights[i], value=values[i]) for i in range(len(weights))]
    capacity = 50
    res = GeneticSolver(40, 0.2, 30).solve(items, capacity)
    total_sum = sum(i.value for i in res)
    # Optimal solution is 83, but it is unlikely for genetic to reach it
    assert 60 < total_sum <= 83


def test_genetic_solver_minimization():
    items = [
        KnapsackItem(id=get_random_string(), volume=1, value=-2),
        KnapsackItem(id=get_random_string(), volume=2, value=-4),
        KnapsackItem(id=get_random_string(), volume=3, value=-4),
        KnapsackItem(id=get_random_string(), volume=4, value=-5),
        KnapsackItem(id=get_random_string(), volume=5, value=-7),
        KnapsackItem(id=get_random_string(), volume=6, value=-9),
    ]
    capacity = 4
    results = [GeneticSolver(80, 0.2, 80).solve(items, capacity) for _ in range(20)]
    values = [sum(r.value for r in res) for res in results]
    volumes = [sum(r.volume for r in res) for res in results]
    all_values_smaller_than_zero = all(r < 0 for r in values)
    all_volumes_within_capacity_range = all(0 < r <= capacity for r in volumes)
    assert all_values_smaller_than_zero
    assert all_volumes_within_capacity_range
