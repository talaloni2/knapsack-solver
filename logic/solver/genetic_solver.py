import random

from logic.solver.base_solver import BaseSolver
from models.knapsack_item import KnapsackItem


class GeneticSolver(BaseSolver):
    def __init__(self, generations: int, mutation_probability: float, initial_population_size: int):
        self._generations = generations
        self._mutation_probability = mutation_probability
        self._initial_population_size = initial_population_size

    def solve(self, items: list[KnapsackItem], volume: int) -> list[KnapsackItem]:
        return self._control_loop(items, volume)

    def _control_loop(self, items: list[KnapsackItem], capacity: int):
        items_count = len(items)
        population = self._generate_population(self._initial_population_size, items, capacity)

        for _ in range(self._generations):
            parent1, parent2 = self._select_chromosomes(population, items, capacity)

            child1, child2 = self._crossover(parent1, parent2, items_count)

            if random.uniform(0, 1) < self._mutation_probability:
                child1 = self._mutate(child1, items_count)
            if random.uniform(0, 1) < self._mutation_probability:
                child2 = self._mutate(child2, items_count)

            population = self._new_generation(population, [child1, child2], items, capacity)

        return self._get_best(population, items, capacity)

    @staticmethod
    def _generate_population(size: int, items: list[KnapsackItem], capacity: int) -> list[list[bool]]:
        population = []
        for _ in range(size):
            genes = [False, True]
            chromosome = []
            for _ in range(len(items)):
                chromosome.append(random.choice(genes))
                if sum(k.value for i, k in enumerate(items) if i < len(chromosome) and chromosome[i]) > capacity:
                    chromosome[-1] = False
                    chromosome += [False] * (len(items) - len(chromosome))
                    break
            population.append(chromosome)
        return population

    def _select_chromosomes(
        self, population: list[list[bool]], items: list[KnapsackItem], capacity: int
    ) -> tuple[list[bool], list[bool]]:
        fitness_values = []
        for chromosome in population:
            fitness_values.append(self._calculate_fitness(chromosome, items, capacity))

        fitness_values = [float(i) / (sum(fitness_values) or 1) for i in fitness_values]

        parent1 = random.choices(population, weights=fitness_values, k=1)[0]
        parent2 = random.choices(population, weights=fitness_values, k=1)[0]

        return parent1, parent2

    @staticmethod
    def _calculate_fitness(chromosome: list[bool], items: list[KnapsackItem], capacity: int) -> int:
        total_weight = 0
        total_value = 0
        for i in range(len(chromosome)):
            if chromosome[i]:
                total_weight += items[i].volume
                total_value += items[i].value
        if total_weight > capacity:
            return 0
        else:
            return total_value

    @staticmethod
    def _crossover(parent1: list[bool], parent2: list[bool], items_count: int):
        crossover_point = random.randint(0, items_count - 1)
        child1 = parent1[0:crossover_point] + parent2[crossover_point:]
        child2 = parent2[0:crossover_point] + parent1[crossover_point:]

        return child1, child2

    @staticmethod
    def _mutate(chromosome, items_count: int):
        mutation_point = random.randint(0, items_count - 1)
        if chromosome[mutation_point] == 0:
            chromosome[mutation_point] = 1
        else:
            chromosome[mutation_point] = 0
        return chromosome

    def _get_best(self, population: list[list[bool]], items: list[KnapsackItem], capacity: int) -> list[KnapsackItem]:
        fitness_values = []
        for chromosome in population:
            fitness_values.append(self._calculate_fitness(chromosome, items, capacity))

        max_value = max(fitness_values)
        max_index = fitness_values.index(max_value)
        return [items[i] for i, include in enumerate(population[max_index]) if include]

    def _new_generation(
        self, population: list[list[bool]], children: list[list[bool]], items: list[KnapsackItem], capacity: int
    ):
        population = self._mutate_misfits(population, items, capacity)
        return self._replace_children_into_population(population, children, items, capacity)

    def _mutate_misfits(
        self, population: list[list[bool]], items: list[KnapsackItem], capacity: int
    ) -> list[list[bool]]:
        for i, chromosome in enumerate(population):
            if not self._calculate_fitness(chromosome, items, capacity):
                population[i] = self._mutate(chromosome, len(items))
        return population

    def _replace_children_into_population(
        self, population: list[list[bool]], children: list[list[bool]], items: list[KnapsackItem], capacity: int
    ) -> list[list[bool]]:
        child_idx = 0
        for i, chromosome in enumerate(population):
            if not self._calculate_fitness(chromosome, items, capacity):
                population[i] = children[child_idx]
                child_idx += 1
            if child_idx == len(children):
                return population

        while child_idx < len(children):
            child_loc = random.randint(0, len(population) - 1)
            population[child_loc] = children[child_idx]
            child_idx += 1
        return population
