import json
import traceback
from typing import Optional

import aio_pika
import aio_pika.abc

from logic.algorithm_runner import AlgorithmRunner
from logic.claims_service import ClaimsService
from logic.rabbit_channel_context import RabbitChannelContext
from logic.solution_reporter import SolutionReporter
from logic.suggested_solution_service import SuggestedSolutionsService
from models.algorithms import Algorithms
from models.knapsack_item import KnapsackItem
from models.knapsack_solver_instance_dto import SolverInstanceRequest
from models.solution import SolutionReportCause, AlgorithmSolution


class SolverInstanceConsumer:
    def __init__(
        self,
        channel_context: RabbitChannelContext,
        algo_runner: AlgorithmRunner,
        claims_service: ClaimsService,
        solution_reporter: SolutionReporter,
        suggested_solutions_service: SuggestedSolutionsService,
    ):
        self._channel_context = channel_context
        self._algo_runner = algo_runner
        self._claims_service = claims_service
        self._solution_reporter = solution_reporter
        self._suggested_solutions_service = suggested_solutions_service

    async def __aenter__(self):
        self._channel = await self._channel_context.__aenter__()
        return self

    async def start_consuming(self, queue_name: str):
        queue: aio_pika.abc.AbstractQueue = await self._channel.declare_queue(queue_name)

        async for request in self._consume_messages(queue):
            await self._handle_message(request)

    # noinspection PyUnresolvedReferences
    @staticmethod
    async def _consume_messages(queue: aio_pika.abc.AbstractQueue):
        try:
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        try:
                            yield SolverInstanceRequest(**json.loads(message.body.decode()))
                        except Exception as e:
                            print(f"Skipping message {message} because could not parse solver request due to {e}")
                            continue
        except Exception as e:
            print(e)
            raise

    async def _handle_message(self, request: SolverInstanceRequest) -> None:
        if not await self._claims_service.claim_running_knapsack(request.knapsack_id):
            print(
                f"Knapsack {request.knapsack_id} is already running on a different node. Skipping execution. "
                f"This may cause timeouts in subscribers"
            )
            return

        try:
            if await self._suggested_solutions_service.get_solutions(request.knapsack_id):
                await self._solution_reporter.report_error(
                    request.knapsack_id, SolutionReportCause.SUGGESTION_ALREADY_EXISTS
                )
                return

            claimed_items: list[KnapsackItem] = await self._try_claim_items(request)
            if not claimed_items:
                await self._solution_reporter.report_error(
                    request.knapsack_id, SolutionReportCause.NO_ITEM_CLAIMED
                )
                return

            solutions = self._algo_runner.run_algorithms(claimed_items, request.volume, request.algorithms)
            solutions_with_algos = list(zip(request.algorithms, solutions))
            await self._release_non_needed_items(claimed_items, solutions)
            solutions = self._dedup_solutions(solutions_with_algos)
            solutions = [AlgorithmSolution(algorithm=alg, items=sol) for alg, sol in solutions]
            await self._solution_reporter.report_solution_suggestions(solutions, request.knapsack_id)
        except Exception as e:
            await self._claims_service.release_items_claims(request.items)
            await self._solution_reporter.report_error(request.knapsack_id, SolutionReportCause.GOT_EXCEPTION)
            traceback.print_exc()
        finally:
            if request:
                await self._claims_service.release_claim_running_knapsack(request.knapsack_id)

    async def _should_run(self, request: SolverInstanceRequest):
        if await self._suggested_solutions_service.get_solutions(request.knapsack_id):
            await self._solution_reporter.report_error(
                request.knapsack_id, SolutionReportCause.SUGGESTION_ALREADY_EXISTS
            )
            return False

        return True

    async def _try_claim_items(self, request: SolverInstanceRequest) -> Optional[list[KnapsackItem]]:
        claimed_items: list[KnapsackItem] = await self._claims_service.claim_items(
            request.items, request.volume, request.knapsack_id
        )
        if not claimed_items:
            await self._solution_reporter.report_error(request.knapsack_id, SolutionReportCause.NO_ITEM_CLAIMED)
            return
        return claimed_items

    async def _release_non_needed_items(self, claimed_items: list[KnapsackItem], solutions: list[list[KnapsackItem]]) -> None:
        solution_ids = {n.id for s in solutions for n in s}
        released_items = [i for i in claimed_items if i.id not in solution_ids]

        await self._claims_service.release_items_claims(released_items)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._channel_context.__aexit__(exc_type, exc_val, exc_tb)

    def _dedup_solutions(self, solutions: list[tuple[Algorithms, list[KnapsackItem]]]) -> list[tuple[Algorithms, list[KnapsackItem]]]:
        seen = list()
        return [seen.append(sol) or (alg, sol) for alg, sol in solutions if sol not in seen]
