import asyncio
import json

import aio_pika
import aio_pika.abc

from logic.algorithm_runner import AlgorithmRunner
from logic.items_claimer import ItemsClaimer
from logic.solution_reporter import SolutionReporter, SolutionReportCause
from models.knapsack_solver_instance_dto import SolverInstanceRequest
from models.rabbit_connection_params import RabbitConnectionParams


class SolverInstanceConsumer:
    def __init__(
        self,
        connection_params: RabbitConnectionParams,
        algo_runner: AlgorithmRunner,
        items_claimer: ItemsClaimer,
        solution_reporter: SolutionReporter,
    ):
        self._connection_params = connection_params
        self._algo_runner = algo_runner
        self._items_claimer = items_claimer
        self._solution_reporter = solution_reporter

    async def __aenter__(self):
        host, port, user, password = self._connection_params
        self._connection = await aio_pika.connect_robust(
            f"amqp://{user}:{password}@{host}:{port}/", loop=asyncio.get_event_loop()
        )
        await self._connection.__aenter__()

        self._channel: aio_pika.abc.AbstractChannel = await self._connection.channel()
        return self

    async def start_consuming(self, queue_name: str):
        queue: aio_pika.abc.AbstractQueue = await self._channel.declare_queue(queue_name)

        async for message in self._consume_messages(queue):
            await self._handle_message(message)

    # noinspection PyUnresolvedReferences
    @staticmethod
    async def _consume_messages(queue: aio_pika.abc.AbstractQueue):
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    yield message.body.decode()

    async def _handle_message(self, message: str) -> None:
        request: SolverInstanceRequest = SolverInstanceRequest(**json.loads(message))
        claimed_items = await self._items_claimer.claim_items(request.items, request.volume, request.knapsack_id)

        if not claimed_items:
            await self._solution_reporter.report_error(request.knapsack_id, SolutionReportCause.NO_ITEM_CLAIMED)

        solution = self._algo_runner.run_algorithm(claimed_items, request.volume, request.algorithm)
        await self._solution_reporter.report_solutions([solution], request.knapsack_id)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._connection.__aexit__(exc_type, exc_val, exc_tb)


#
# async def main():
#     consumer = SolverInstanceConsumer(
#         RabbitConnectionParams("localhost", 5672, "guest", "guest"), get_algorithm_runner()
#     )
#     async with consumer:
#         await consumer.start_consuming("test")
#
#
# if __name__ == "__main__":
#     loop = asyncio.get_event_loop()
#     loop.run_until_complete(main())
#     loop.close()
