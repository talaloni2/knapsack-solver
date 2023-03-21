import asyncio

import aio_pika

from models.config.rabbit_connection_params import RabbitConnectionParams


class RabbitChannelContext:
    def __init__(self, connection_params: RabbitConnectionParams):
        self._connection_params = connection_params

    async def __aenter__(self) -> aio_pika.abc.AbstractChannel:
        host, port, user, password = self._connection_params
        self._connection = await aio_pika.connect_robust(
            f"amqp://{user}:{password}@{host}:{port}/", loop=asyncio.get_event_loop()
        )
        await self._connection.__aenter__()

        return await self._connection.channel()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._connection.__aexit__(exc_type, exc_val, exc_tb)
