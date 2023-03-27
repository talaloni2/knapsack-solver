import aio_pika.abc

from models.cluster_availability import ClusterAvailabilityScore
from models.config.configuration import Config


class ClusterAvailabilityService:
    def __init__(self, rabbit_channel: aio_pika.abc.AbstractChannel, config: Config):
        self._channel = rabbit_channel
        self._config = config

    async def get_cluster_availability_score(self) -> ClusterAvailabilityScore:
        queue = await self._channel.declare_queue(self._config.solver_queue, passive=True)

        if queue.declaration_result.message_count >= self._config.solvers_very_busy_threshold:
            return ClusterAvailabilityScore.VERY_BUSY

        if queue.declaration_result.message_count >= self._config.solvers_busy_threshold:
            return ClusterAvailabilityScore.BUSY

        if queue.declaration_result.message_count >= self._config.solvers_moderate_busy_threshold:
            return ClusterAvailabilityScore.MODERATE

        return ClusterAvailabilityScore.AVAILABLE
