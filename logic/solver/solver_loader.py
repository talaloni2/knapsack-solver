from logic.solver.base_solver import BaseSolver
from logic.solver.first_fit_solver import FitFirstSolver
from logic.solver.greedy_solver import GreedySolver
from models.algorithms import Algorithms


class SolverLoader:
    _solvers: dict[Algorithms, BaseSolver]

    def __init__(self):
        self._solvers = {
            Algorithms.FIRST_FIT: FitFirstSolver(),
            Algorithms.GREEDY: GreedySolver(),
        }

    def load(self, algorithm: Algorithms):
        return self._solvers.get(algorithm, Algorithms.FIRST_FIT)
