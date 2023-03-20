import json
from typing import AsyncIterator

from aioredis import Redis

from models.solution import SolutionReport


class SolutionReportWaiter:
    def __init__(self, redis: Redis, solutions_channel_prefix: str, knapsack_id: str):
        self._redis = redis
        self._solutions_channel_prefix = solutions_channel_prefix
        self._knapsack_id = knapsack_id
        self._is_consuming = False
        self._pubsub = None

    async def __aenter__(self) -> "SolutionReportWaiter":
        self._pubsub_context = self._redis.pubsub()
        self._pubsub = await self._pubsub_context.__aenter__()
        channel_name: str = f"{self._solutions_channel_prefix}:{self._knapsack_id}"
        await self._pubsub.subscribe(channel_name)
        return self

    async def wait_for_solution_report(self) -> SolutionReport:
        self._is_consuming = True
        gen = self._subscribe_for_reports()
        final_report = None
        async for report in gen:
            if report:
                self._is_consuming = False
                final_report = report
        return final_report

    async def _subscribe_for_reports(self) -> AsyncIterator[SolutionReport]:
        while self._is_consuming:
            message = None
            while not message:
                message = await self._pubsub.get_message(True)
            response = SolutionReport(**json.loads(message["data"].decode()))
            yield response

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._pubsub_context.__aexit__(exc_type, exc_val, exc_tb)
