from enum import Enum


class Algorithms(str, Enum):
    GREEDY = "greedy"
    FIRST_FIT = "firstFit"
    DYNAMIC_PROGRAMMING = "dynamicProgramming"
    GENETIC_FEW_GENERATIONS = "geneticFewGenerations"
    GENETIC_LOTS_GENERATIONS = "geneticLotsGenerations"
    BRANCH_AND_BOUND = "branchAndBound"
