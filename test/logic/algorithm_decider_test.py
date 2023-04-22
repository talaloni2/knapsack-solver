from enum import Enum
from unittest.mock import AsyncMock

import pytest

from logic.algorithm_decider import AlgorithmDecider
from logic.cluster_availability_service import ClusterAvailabilityService
from models.algorithms import Algorithms
from models.cluster_availability import ClusterAvailabilityScore
from models.config.configuration import Config
from models.subscription import SubscriptionScore


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "availability,subscription,expected_algos",
    [
        [ClusterAvailabilityScore.AVAILABLE, SubscriptionScore.STANDARD, [Algorithms.GENETIC_HEAVY, Algorithms.GENETIC_LIGHT, Algorithms.GREEDY]],
        [ClusterAvailabilityScore.MODERATE, SubscriptionScore.STANDARD, [Algorithms.GENETIC_LIGHT, Algorithms.GENETIC_LIGHT, Algorithms.GREEDY]],
        [ClusterAvailabilityScore.BUSY, SubscriptionScore.STANDARD, [Algorithms.GREEDY]],
        [ClusterAvailabilityScore.VERY_BUSY, SubscriptionScore.STANDARD, [Algorithms.GREEDY]],
        [ClusterAvailabilityScore.AVAILABLE, SubscriptionScore.PREMIUM, [Algorithms.BRANCH_AND_BOUND, Algorithms.GENETIC_HEAVY, Algorithms.GENETIC_LIGHT, Algorithms.GREEDY]],
        [ClusterAvailabilityScore.MODERATE, SubscriptionScore.PREMIUM, [Algorithms.DYNAMIC_PROGRAMMING, Algorithms.GENETIC_HEAVY, Algorithms.GENETIC_LIGHT, Algorithms.GREEDY]],
        [ClusterAvailabilityScore.BUSY, SubscriptionScore.PREMIUM, [Algorithms.GENETIC_HEAVY]],
        [ClusterAvailabilityScore.VERY_BUSY, SubscriptionScore.PREMIUM, [Algorithms.GENETIC_LIGHT]],
    ],
)
async def test_algorithm_decider(
    availability: ClusterAvailabilityScore,
    subscription: SubscriptionScore,
    expected_algos: list[Algorithms],
    config: Config,
    knapsack_id: str,
):
    subscriptions_service = AsyncMock()
    subscriptions_service.get_subscription_score = AsyncMock(return_value=subscription)
    cluster_availability_service: ClusterAvailabilityService = AsyncMock()
    cluster_availability_service.get_cluster_availability_score = AsyncMock(return_value=availability)
    decider = AlgorithmDecider(
        subscriptions_service,
        cluster_availability_service,
        config.algo_decider_branch_and_bound_max_items,
        config.algo_decider_dynamic_programming_max_iterations,
    )
    algos = await decider.decide(knapsack_id, 10, 10)

    assert algos == expected_algos


class MockEnum(int, Enum):
    MOCK = 400000


@pytest.mark.asyncio
async def test_algorithm_decider_handle_non_existing_score(config: Config, knapsack_id: str):
    subscriptions_service = AsyncMock()
    subscriptions_service.get_subscription_score = AsyncMock(return_value=MockEnum.MOCK)
    cluster_availability_service: ClusterAvailabilityService = AsyncMock()
    cluster_availability_service.get_cluster_availability_score = AsyncMock(return_value=MockEnum.MOCK)
    decider = AlgorithmDecider(
        subscriptions_service,
        cluster_availability_service,
        config.algo_decider_branch_and_bound_max_items,
        config.algo_decider_dynamic_programming_max_iterations,
    )
    algo = await decider.decide(knapsack_id, 10, 10)

    assert algo == [Algorithms.FIRST_FIT]


@pytest.mark.asyncio
async def test_algorithm_decider_thresholds_bnb_to_dp(config: Config, knapsack_id: str):
    subscriptions_service = AsyncMock()
    subscriptions_service.get_subscription_score = AsyncMock(return_value=SubscriptionScore.PREMIUM)
    cluster_availability_service: ClusterAvailabilityService = AsyncMock()
    cluster_availability_service.get_cluster_availability_score = AsyncMock(
        return_value=ClusterAvailabilityScore.AVAILABLE
    )
    decider = AlgorithmDecider(subscriptions_service, cluster_availability_service, 1, 1000)
    algo = await decider.decide(knapsack_id, 2, 10)

    assert algo == [Algorithms.DYNAMIC_PROGRAMMING, Algorithms.GENETIC_HEAVY, Algorithms.GENETIC_LIGHT, Algorithms.GREEDY]


@pytest.mark.asyncio
async def test_algorithm_decider_thresholds_bnb_to_genetic(config: Config, knapsack_id: str):
    subscriptions_service = AsyncMock()
    subscriptions_service.get_subscription_score = AsyncMock(return_value=SubscriptionScore.PREMIUM)
    cluster_availability_service: ClusterAvailabilityService = AsyncMock()
    cluster_availability_service.get_cluster_availability_score = AsyncMock(
        return_value=ClusterAvailabilityScore.AVAILABLE
    )
    decider = AlgorithmDecider(subscriptions_service, cluster_availability_service, 1, 2)
    algo = await decider.decide(knapsack_id, 2, 10)

    assert algo == [Algorithms.GENETIC_HEAVY, Algorithms.GENETIC_HEAVY, Algorithms.GENETIC_LIGHT, Algorithms.GREEDY]


@pytest.mark.asyncio
async def test_algorithm_decider_thresholds_dp_to_genetic(config: Config, knapsack_id: str):
    subscriptions_service = AsyncMock()
    subscriptions_service.get_subscription_score = AsyncMock(return_value=SubscriptionScore.PREMIUM)
    cluster_availability_service: ClusterAvailabilityService = AsyncMock()
    cluster_availability_service.get_cluster_availability_score = AsyncMock(
        return_value=ClusterAvailabilityScore.MODERATE
    )
    decider = AlgorithmDecider(subscriptions_service, cluster_availability_service, 1, 2)
    algo = await decider.decide(knapsack_id, 2, 10)

    assert algo == [Algorithms.GENETIC_HEAVY, Algorithms.GENETIC_HEAVY, Algorithms.GENETIC_LIGHT, Algorithms.GREEDY]
