import aio_pika

from models.knapsack_solver_instance_dto import SolverInstanceRequest


class SolverRouterProducer:
    def __init__(self, rabbit_channel: aio_pika.abc.AbstractChannel, queue: str):
        self._channel = rabbit_channel
        self._queue_name = queue

    async def __aenter__(self):
        await self._channel.declare_queue(self._queue_name)
        return self

    async def produce_solver_instance_request(self, request: SolverInstanceRequest):
        await self._channel.default_exchange.publish(
            aio_pika.Message(body=request.json().encode()),
            routing_key=self._queue_name,
        )

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
