import asyncio
import json
from datetime import timedelta

from aioredis import Redis
from discord.ext import tasks

from logic.claims_service import ClaimsService
from logic.suggested_solution_service import SuggestedSolutionsService
from logic.time_service import TimeService
from models.config.configuration import Config
from models.solution import SuggestedSolution, AcceptedSolution
from models.suggested_solutions_actions_statuses import RejectResult


class SolutionMaintainer:
    def __init__(
        self,
        suggested_solution_service: SuggestedSolutionsService,
        redis_client: Redis,
        time_service: TimeService,
        claims_service: ClaimsService,
        config: Config,
    ):
        self._suggested_solution_service = suggested_solution_service
        self._redis_client = redis_client
        self._time_service = time_service
        self._claims_service = claims_service
        self._config = config
        self.clean_old_suggestions = tasks.loop(seconds=config.clean_old_suggestion_interval_seconds)(self.clean_old_suggestions)
        self.clean_old_accepted_solutions = tasks.loop(seconds=config.clean_old_accepted_solutions_interval_seconds)(self.clean_old_accepted_solutions)

    async def clean_old_suggestions(self):
        suggested_solution_ttl = timedelta(seconds=self._config.suggestion_ttl_seconds)
        async for knapsack_id in self._redis_client.hscan_iter(self._config.suggested_solutions_hash):
            knapsack_id = knapsack_id.decode()
            suggestion: SuggestedSolution = await self._suggested_solution_service.get_solutions(knapsack_id)
            if not suggestion:
                continue

            if (self._time_service.now() - suggestion.time) >= suggested_solution_ttl:
                print(f"Deleting old suggestion for knapsack: {knapsack_id} issued at: {suggestion.time.isoformat()}")
                result = await self._suggested_solution_service.reject_suggested_solutions(knapsack_id)
                if result != RejectResult.REJECT_SUCCESS:
                    print(f"Could not reject solution. Rejection result is: {result}")

    async def clean_old_accepted_solutions(self):
        current_index = 0
        accepted_solutions = await self._get_accepted_solutions(current_index)
        accepted_solution_ttl = timedelta(seconds=self._config.accepted_solution_ttl_seconds)
        should_stop = False
        while accepted_solutions and not should_stop:
            for solution in accepted_solutions:
                solution = AcceptedSolution(**json.loads(solution.decode()))
                if (self._time_service.now() - solution.time) < accepted_solution_ttl:
                    should_stop = True
                    break
                print(
                    f"Deleting old solution for knapsack: {solution.knapsack_id} issued at: {solution.time.isoformat()}"
                )
                await self._release_accepted_items(solution)

            if should_stop:
                break
            current_index += self._config.accepted_solutions_prefect_count
            accepted_solutions = await self._get_accepted_solutions(current_index)

    async def _release_accepted_items(self, solution):
        await self._redis_client.lpop(self._config.accepted_solutions_list)
        await self._claims_service.release_items_claims(solution.solution)

    async def _get_accepted_solutions(self, current_index):
        return await self._redis_client.lrange(
            self._config.accepted_solutions_list, current_index, current_index + self._config.accepted_solutions_prefect_count
        )


async def run_tasks(solution_maintainer: SolutionMaintainer):
    solution_maintainer.clean_old_suggestions.start()
    solution_maintainer.clean_old_accepted_solutions.start()
