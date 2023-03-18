import json

import aio_pika
import aio_pika.abc

from logic.algorithm_runner import AlgorithmRunner
from logic.claims_service import ClaimsService
from logic.rabbit_channel_context import RabbitChannelContext
from logic.solution_reporter import SolutionReporter
from models.knapsack_item import KnapsackItem
from models.knapsack_solver_instance_dto import SolverInstanceRequest
from models.solution import SolutionReportCause


class SolverInstanceConsumer:
    def __init__(
        self,
        channel_context: RabbitChannelContext,
        algo_runner: AlgorithmRunner,
        items_claimer: ClaimsService,
        solution_reporter: SolutionReporter,
    ):
        self._channel_context = channel_context
        self._algo_runner = algo_runner
        self._items_claimer = items_claimer
        self._solution_reporter = solution_reporter

    async def __aenter__(self):
        self._channel = await self._channel_context.__aenter__()
        return self

    async def start_consuming(self, queue_name: str):
        queue: aio_pika.abc.AbstractQueue = await self._channel.declare_queue(queue_name)

        async for message in self._consume_messages(queue):
            await self._handle_message(message)

    # noinspection PyUnresolvedReferences
    @staticmethod
    async def _consume_messages(queue: aio_pika.abc.AbstractQueue):
        try:
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        yield message.body.decode()
        except Exception as e:
            print(e)
            raise

    async def _handle_message(self, message: str) -> None:
        try:
            request: SolverInstanceRequest = SolverInstanceRequest(**json.loads(message))
            claimed_items: list[KnapsackItem] = await self._items_claimer.claim_items(
                request.items, request.volume, request.knapsack_id
            )
            if not claimed_items:
                await self._solution_reporter.report_error(request.knapsack_id, SolutionReportCause.NO_ITEM_CLAIMED)
                return

            solution = self._algo_runner.run_algorithm(claimed_items, request.volume, request.algorithm)
            await self._release_non_needed_items(claimed_items, solution)
            await self._solution_reporter.report_solution_suggestions([solution], request.knapsack_id)
        except Exception as e:
            print(e)

    async def _release_non_needed_items(self, claimed_items: list[KnapsackItem], solution: list[KnapsackItem]) -> None:
        solution_ids = {n.id for n in solution}
        released_items = [i for i in claimed_items if i.id not in solution_ids]

        await self._items_claimer.release_items_claims(released_items)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._channel_context.__aexit__(exc_type, exc_val, exc_tb)
