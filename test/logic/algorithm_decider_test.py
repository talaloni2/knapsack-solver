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
    "availability,subscription,expected_algo",
    [
        [ClusterAvailabilityScore.AVAILABLE, SubscriptionScore.STANDARD, Algorithms.GENETIC_LOTS_GENERATIONS],
        [ClusterAvailabilityScore.MODERATE, SubscriptionScore.STANDARD, Algorithms.GENETIC_FEW_GENERATIONS],
        [ClusterAvailabilityScore.BUSY, SubscriptionScore.STANDARD, Algorithms.GREEDY],
        [ClusterAvailabilityScore.VERY_BUSY, SubscriptionScore.STANDARD, Algorithms.GREEDY],
        [ClusterAvailabilityScore.AVAILABLE, SubscriptionScore.PREMIUM, Algorithms.BRANCH_AND_BOUND],
        [ClusterAvailabilityScore.MODERATE, SubscriptionScore.PREMIUM, Algorithms.DYNAMIC_PROGRAMMING],
        [ClusterAvailabilityScore.BUSY, SubscriptionScore.PREMIUM, Algorithms.GENETIC_LOTS_GENERATIONS],
        [ClusterAvailabilityScore.VERY_BUSY, SubscriptionScore.PREMIUM, Algorithms.GENETIC_FEW_GENERATIONS],
    ],
)
async def test_algorithm_decider(
    availability: ClusterAvailabilityScore,
    subscription: SubscriptionScore,
    expected_algo: Algorithms,
    config: Config,
    knapsack_id: str,
):
    subscriptions_service = AsyncMock()
    subscriptions_service.get_subscription_score = AsyncMock(return_value=subscription)
    cluster_availability_service: ClusterAvailabilityService = AsyncMock()
    cluster_availability_service.get_cluster_availability_score = AsyncMock(return_value=availability)
    decider = AlgorithmDecider(subscriptions_service, cluster_availability_service)
    algo = await decider.decide(knapsack_id)

    assert algo == expected_algo


class MockEnum(int, Enum):
    MOCK = 400000


@pytest.mark.asyncio
async def test_algorithm_decider_handle_non_existing_score(config: Config, knapsack_id: str):
    subscriptions_service = AsyncMock()
    subscriptions_service.get_subscription_score = AsyncMock(return_value=MockEnum.MOCK)
    cluster_availability_service: ClusterAvailabilityService = AsyncMock()
    cluster_availability_service.get_cluster_availability_score = AsyncMock(return_value=MockEnum.MOCK)
    decider = AlgorithmDecider(subscriptions_service, cluster_availability_service)
    algo = await decider.decide(knapsack_id)

    assert algo == Algorithms.FIRST_FIT
