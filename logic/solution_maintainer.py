import asyncio
import json
import os
from datetime import timedelta

from aioredis import Redis
from discord.ext import tasks

from component_factory import (
    get_suggested_solutions_service,
    get_redis,
    get_time_service,
    get_claims_service, get_config,
)
from logic.claims_service import ClaimsService
from logic.suggested_solution_service import SuggestedSolutionsService
from logic.time_service import TimeService
from models.solution import SuggestedSolution, AcceptedSolution
from models.suggested_solutions_actions_statuses import RejectResult

CLEAN_OLD_SUGGESTION_INTERVAL_SECONDS = int(os.getenv("CLEAN_OLD_SUGGESTION_INTERVAL_SECONDS", "30"))
CLEAN_OLD_ACCEPTED_SOLUTIONS_INTERVAL_SECONDS = int(
    os.getenv("CLEAN_OLD_ACCEPTED_SOLUTIONS_INTERVAL_SECONDS", f"{60 * 30}")
)

SUGGESTION_TTL_SECONDS = int(os.getenv("SUGGESTION_TTL_SECONDS", "60"))
ACCEPTED_SOLUTION_TTL_SECONDS = int(os.getenv("ACCEPTED_SOLUTION_TTL_SECONDS", f"{60 * 60 * 4}"))
ACCEPTED_SOLUTIONS_PREFECT_COUNT = int(os.getenv("ACCEPTED_SOLUTIONS_PREFECT_COUNT", "5"))


class SolutionMaintainer:
    def __init__(
        self,
        suggested_solution_service: SuggestedSolutionsService,
        redis_client: Redis,
        time_service: TimeService,
        claims_service: ClaimsService,
        suggested_solutions_hash_name: str,
        accepted_solutions_list_name: str,
    ):
        self._suggested_solution_service = suggested_solution_service
        self._redis_client = redis_client
        self._time_service = time_service
        self._claims_service = claims_service
        self._suggested_solutions_hash_name = suggested_solutions_hash_name
        self._accepted_solutions_list_name = accepted_solutions_list_name

    @tasks.loop(seconds=CLEAN_OLD_SUGGESTION_INTERVAL_SECONDS)
    async def clean_old_suggestions(self):
        suggested_solution_ttl = timedelta(seconds=SUGGESTION_TTL_SECONDS)
        async for knapsack_id in self._redis_client.hscan_iter(self._suggested_solutions_hash_name):
            knapsack_id = knapsack_id.decode()
            suggestion: SuggestedSolution = await self._suggested_solution_service.get_solutions(knapsack_id)
            if not suggestion:
                continue

            if (self._time_service.now() - suggestion.time) >= suggested_solution_ttl:
                print(f"Deleting old suggestion for knapsack: {knapsack_id} issued at: {suggestion.time.isoformat()}")
                result = await self._suggested_solution_service.reject_suggested_solutions(knapsack_id)
                if result != RejectResult.REJECT_SUCCESS:
                    print(f"Could not reject solution. Rejection result is: {result}")

    @tasks.loop(seconds=CLEAN_OLD_ACCEPTED_SOLUTIONS_INTERVAL_SECONDS)
    async def clean_old_accepted_solutions(self):
        current_index = 0
        accepted_solutions = await self._get_accepted_solutions(current_index)
        accepted_solution_ttl = timedelta(seconds=ACCEPTED_SOLUTION_TTL_SECONDS)
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
            current_index += ACCEPTED_SOLUTIONS_PREFECT_COUNT
            accepted_solutions = await self._get_accepted_solutions(current_index)

    async def _release_accepted_items(self, solution):
        await self._redis_client.lpop(self._accepted_solutions_list_name)
        await self._claims_service.release_items_claims(solution.solution)

    async def _get_accepted_solutions(self, current_index):
        return await self._redis_client.lrange(
            self._accepted_solutions_list_name, current_index, current_index + ACCEPTED_SOLUTIONS_PREFECT_COUNT
        )


async def run_tasks(
    suggested_solution_service: SuggestedSolutionsService,
    redis_client: Redis,
    time_service: TimeService,
    claims_service: ClaimsService,
    suggested_solutions_hash_name: str,
    accepted_solutions_list_name: str,
):
    m = SolutionMaintainer(
        suggested_solution_service,
        redis_client,
        time_service,
        claims_service,
        suggested_solutions_hash_name,
        accepted_solutions_list_name,
    )
    m.clean_old_suggestions.start()
    m.clean_old_accepted_solutions.start()


if __name__ == "__main__":
    config = get_config()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(
        run_tasks(
            get_suggested_solutions_service(),
            get_redis(),
            get_time_service(),
            get_claims_service(),
            config.suggested_solutions_claims_hash,
            config.accepted_solutions_list
        )
    )
    loop.run_forever()
