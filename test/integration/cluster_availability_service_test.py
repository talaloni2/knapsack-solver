from typing import NamedTuple

import aio_pika.abc
import pytest

from logic.cluster_availability_service import ClusterAvailabilityService
from models.cluster_availability import ClusterAvailabilityScore
from models.config.configuration import Config


class ThresholdParameters(NamedTuple):
    moderate: int
    busy: int
    very_busy: int


def config_thresholds(config: Config, threshold_config: ThresholdParameters):
    original = config
    return Config(
        server_port=8000,
        deployment_type=None,
        rabbit_connection_params=original.rabbit_connection_params,
        redis_connection_params=original.redis_connection_params,
        solver_queue=original.solver_queue,
        items_claim_hash=original.items_claim_hash,
        suggested_solutions_claims_hash=original.suggested_solutions_claims_hash,
        running_knapsack_claims_hash=original.running_knapsack_claims_hash,
        solutions_channel_prefix=original.solutions_channel_prefix,
        wait_for_report_timeout_seconds=original.wait_for_report_timeout_seconds,
        suggested_solutions_hash=original.suggested_solutions_hash,
        accepted_solutions_list=original.accepted_solutions_list,
        clean_old_suggestion_interval_seconds=original.clean_old_suggestion_interval_seconds,
        clean_old_accepted_solutions_interval_seconds=original.clean_old_accepted_solutions_interval_seconds,
        suggestion_ttl_seconds=original.suggestion_ttl_seconds,
        accepted_solution_ttl_seconds=original.accepted_solution_ttl_seconds,
        accepted_solutions_prefect_count=original.accepted_solutions_prefect_count,
        solvers_moderate_busy_threshold=threshold_config.moderate,
        solvers_busy_threshold=threshold_config.busy,
        solvers_very_busy_threshold=threshold_config.very_busy,
        genetic_light_generations=original.genetic_light_generations,
        genetic_light_mutation_probability=original.genetic_light_mutation_probability,
        genetic_light_population=original.genetic_light_population,
        genetic_heavy_generations=original.genetic_heavy_generations,
        genetic_heavy_mutation_probability=original.genetic_heavy_mutation_probability,
        genetic_heavy_population=original.genetic_heavy_population,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "threshold_config, expected_score",
    [
        [ThresholdParameters(1, 1, 1), ClusterAvailabilityScore.VERY_BUSY],
        [ThresholdParameters(1, 1, 2), ClusterAvailabilityScore.BUSY],
        [ThresholdParameters(1, 2, 3), ClusterAvailabilityScore.MODERATE],
        [ThresholdParameters(2, 3, 4), ClusterAvailabilityScore.AVAILABLE],
    ],
)
async def test_cluster_availability_service_return_available(
    threshold_config,
    expected_score: ClusterAvailabilityScore,
    config: Config,
    rabbit_channel: aio_pika.abc.AbstractChannel,
):
    conf = config_thresholds(config, threshold_config)
    service = ClusterAvailabilityService(rabbit_channel, conf)
    await rabbit_channel.declare_queue(conf.solver_queue)
    await rabbit_channel.default_exchange.publish(
        routing_key=conf.solver_queue, message=aio_pika.Message(body=b"lololololololo")
    )

    score = await service.get_cluster_availability_score()
    assert score == expected_score
