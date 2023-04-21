from enum import Enum


class Algorithms(str, Enum):
    GREEDY = "greedy"
    FIRST_FIT = "firstFit"
    DYNAMIC_PROGRAMMING = "dynamicProgramming"
    GENETIC_LIGHT = "geneticFewGenerations"
    GENETIC_HEAVY = "geneticLotsGenerations"
    BRANCH_AND_BOUND = "branchAndBound"
