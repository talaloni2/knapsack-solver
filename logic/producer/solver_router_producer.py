import asyncio

import aio_pika

from models.knapsack_solver_instance_dto import SolverInstanceRequest
from models.rabbit_connection_params import RabbitConnectionParams


class SolverRouterProducer:
    def __init__(self, connection_params: RabbitConnectionParams, queue: str):
        self._connection_params = connection_params
        self._queue_name = queue

    async def __aenter__(self):
        host, port, user, password = self._connection_params
        self._connection = await aio_pika.connect_robust(
            f"amqp://{user}:{password}@{host}:{port}/", loop=asyncio.get_event_loop()
        )
        await self._connection.__aenter__()

        self._channel: aio_pika.abc.AbstractChannel = await self._connection.channel()
        await self._channel.declare_queue(self._queue_name)
        return self

    async def produce_solver_instance_request(self, request: SolverInstanceRequest):
        await self._channel.default_exchange.publish(
            aio_pika.Message(body=request.json().encode()),
            routing_key=self._queue_name,
        )

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._connection.__aexit__(exc_type, exc_val, exc_tb)
