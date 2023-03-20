import json

from aioredis import Redis

from models.solution import SolutionReport, SolutionReportCause


class SolutionReportWaiter:
    def __init__(
        self, redis: Redis, solutions_channel_prefix: str, knapsack_id: str, wait_for_report_timeout_seconds: float
    ):
        self._redis = redis
        self._solutions_channel_prefix = solutions_channel_prefix
        self._knapsack_id = knapsack_id
        self._is_consuming = False
        self._pubsub = None
        self._wait_for_report_timeout_seconds = wait_for_report_timeout_seconds

    async def __aenter__(self) -> "SolutionReportWaiter":
        self._pubsub_context = self._redis.pubsub()
        self._pubsub = await self._pubsub_context.__aenter__()
        channel_name: str = f"{self._solutions_channel_prefix}:{self._knapsack_id}"
        await self._pubsub.subscribe(channel_name)
        return self

    async def wait_for_solution_report(self) -> SolutionReport:
        timeout_or_finished = False
        message = None
        while not timeout_or_finished:
            message = await self._pubsub.get_message(timeout=self._wait_for_report_timeout_seconds)
            if isinstance(message, dict) and message["type"] == "subscribe":
                continue
            timeout_or_finished = True
        if not message:
            return SolutionReport(cause=SolutionReportCause.TIMEOUT)

        response = SolutionReport(**json.loads(message["data"].decode()))
        return response

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._pubsub_context.__aexit__(exc_type, exc_val, exc_tb)
