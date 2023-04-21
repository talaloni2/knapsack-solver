from logic.solver.base_solver import BaseSolver
from logic.solver.branch_and_bound_solver import BranchAndBoundSolver
from logic.solver.dynamic_programming_solver import DynamicProgrammingSolver
from logic.solver.first_fit_solver import FitFirstSolver
from logic.solver.genetic_solver import GeneticSolver
from logic.solver.greedy_solver import GreedySolver
from models.algorithms import Algorithms
from models.config.configuration import Config


class SolverLoader:
    _solvers: dict[Algorithms, BaseSolver]

    def __init__(self, config: Config):
        self._solvers = {
            Algorithms.FIRST_FIT: FitFirstSolver(),
            Algorithms.GREEDY: GreedySolver(),
            Algorithms.GENETIC_LIGHT: GeneticSolver(
                config.genetic_light_generations,
                config.genetic_light_mutation_probability,
                config.genetic_light_population,
            ),
            Algorithms.GENETIC_HEAVY: GeneticSolver(
                config.genetic_heavy_generations,
                config.genetic_heavy_mutation_probability,
                config.genetic_heavy_population,
            ),
            Algorithms.BRANCH_AND_BOUND: BranchAndBoundSolver(),
            Algorithms.DYNAMIC_PROGRAMMING: DynamicProgrammingSolver(),
        }

    def load(self, algorithm: Algorithms):
        return self._solvers.get(algorithm, Algorithms.FIRST_FIT)
