import json
from typing import Optional
from uuid import uuid4

from aioredis import Redis

from logic.claims_service import ClaimsService
from logic.time_service import TimeService
from models.knapsack_item import KnapsackItem
from models.solution import SuggestedSolution, AcceptedSolution, AlgorithmSolution
from models.suggested_solutions_actions_statuses import AcceptResult, RejectResult


class SuggestedSolutionsService:
    def __init__(
        self,
        redis: Redis,
        claims_service: ClaimsService,
        time_service: TimeService,
        solution_suggestions_hash_name: str,
        accepted_suggestions_list_name: str,
    ):
        self._redis = redis
        self._claims_service = claims_service
        self._time_service = time_service
        self._solution_suggestions_hash_name = solution_suggestions_hash_name
        self._accepted_suggestions_list_name = accepted_suggestions_list_name

    async def register_suggested_solutions(self, solutions: list[AlgorithmSolution], knapsack_id: str) -> None:
        solution_suggestion = SuggestedSolution(
            time=self._time_service.now(), solutions=self._assign_ids_to_suggested_solutions(solutions)
        )
        await self._redis.hset(self._solution_suggestions_hash_name, knapsack_id, solution_suggestion.json())

    async def accept_suggested_solution(self, knapsack_id: str, solution_id: str) -> AcceptResult:
        is_suggestions_claimed = await self._claims_service.claim_suggested_solutions(knapsack_id)
        if not is_suggestions_claimed:
            return AcceptResult.CLAIM_FAILED

        try:
            solutions_suggestions = await self.get_solutions(knapsack_id)
            if not solutions_suggestions:
                return AcceptResult.SOLUTION_NOT_EXISTS
            accepted_solution_items: AlgorithmSolution = solutions_suggestions.solutions[solution_id]
            await self._release_claims_of_non_accepted_solutions(accepted_solution_items, solutions_suggestions)
            await self._perform_accept_single_solution(accepted_solution_items, knapsack_id)
        finally:
            await self._claims_service.release_claim_suggested_solutions(knapsack_id)
        return AcceptResult.ACCEPT_SUCCESS

    async def reject_suggested_solutions(self, knapsack_id: str) -> RejectResult:
        is_suggestions_claimed = await self._claims_service.claim_suggested_solutions(knapsack_id)
        if not is_suggestions_claimed:
            return RejectResult.CLAIM_FAILED

        try:
            solutions_suggestions = await self.get_solutions(knapsack_id)
            if not solutions_suggestions:
                return RejectResult.SUGGESTION_NOT_EXISTS
            await self._release_claims_of_non_accepted_solutions(
                accepted_solution=AlgorithmSolution(items=[]), solutions_suggestions=solutions_suggestions
            )
            await self._remove_solution_suggestion(knapsack_id)
        finally:
            await self._claims_service.release_claim_suggested_solutions(knapsack_id)
        return RejectResult.REJECT_SUCCESS

    async def is_solution_exists(self, knapsack_id: str, solution_id: str) -> bool:
        solutions_suggestions = await self.get_solutions(knapsack_id)
        if not solutions_suggestions:
            return False

        if solution_id not in solutions_suggestions.solutions:
            return False

        return True

    async def get_solutions(self, knapsack_id: str) -> Optional[SuggestedSolution]:
        encoded_solution = await self._redis.hget(self._solution_suggestions_hash_name, knapsack_id)
        if not encoded_solution:
            return None

        return SuggestedSolution(**json.loads(encoded_solution.decode()))

    async def _release_claims_of_non_accepted_solutions(
        self, accepted_solution: AlgorithmSolution, solutions_suggestions: SuggestedSolution
    ) -> None:
        accepted_solution_item_ids: set[str] = {i.id for i in accepted_solution.items}
        items_claims_to_release: list[KnapsackItem] = [
            i for sol in solutions_suggestions.solutions.values() for i in sol.items if i.id not in accepted_solution_item_ids
        ]
        await self._claims_service.release_items_claims(items_claims_to_release)

    async def _perform_accept_single_solution(self, accepted_solution: AlgorithmSolution, knapsack_id: str):
        await self._register_accepted_solution(accepted_solution.items, knapsack_id)
        await self._remove_solution_suggestion(knapsack_id)

    async def _register_accepted_solution(self, accepted_solution_items: list[KnapsackItem], knapsack_id: str):
        accepted_solution = AcceptedSolution(
            time=self._time_service.now(), solution=accepted_solution_items, knapsack_id=knapsack_id
        )
        await self._redis.rpush(self._accepted_suggestions_list_name, accepted_solution.json())

    async def _remove_solution_suggestion(self, knapsack_id: str):
        await self._redis.hdel(self._solution_suggestions_hash_name, knapsack_id)

    @staticmethod
    def _assign_ids_to_suggested_solutions(solutions: list[AlgorithmSolution]) -> dict[str, AlgorithmSolution]:
        return {str(uuid4()): sol for sol in solutions}
