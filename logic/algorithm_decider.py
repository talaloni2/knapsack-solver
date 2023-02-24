from models.algorithms import Algorithms


def get_algorithm_decider():
    return AlgorithmDecider()


class AlgorithmDecider:
    async def decide(self):
        return Algorithms.FIRST_FIT
