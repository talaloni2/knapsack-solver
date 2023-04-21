import random
from unittest.mock import MagicMock

from logic.algorithm_runner import AlgorithmRunner
from logic.solver.base_solver import BaseSolver
from logic.solver.solver_loader import SolverLoader
from models.algorithms import Algorithms
from models.knapsack_item import KnapsackItem
from test.utils import get_random_string


def test_algorithm_runner():
    solver_loader = MagicMock(SolverLoader)
    solver = MagicMock(BaseSolver)
    expected_result = [KnapsackItem(id=get_random_string(), value=10, volume=1)]
    solver.solve = MagicMock(return_value=expected_result)
    solver_loader.load = MagicMock(return_value=solver)
    runner = AlgorithmRunner(solver_loader)
    random_volume = random.randint(1, 5)

    result = runner.run_algorithm(expected_result, random_volume, MagicMock(Algorithms))

    assert expected_result == result
    solver_loader.load.assert_called_once()
    solver.solve.assert_called_once()
