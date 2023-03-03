from models.algorithms import Algorithms


class AlgorithmDecider:
    async def decide(self):
        return Algorithms.GREEDY
