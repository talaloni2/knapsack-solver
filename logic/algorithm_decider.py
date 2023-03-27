from logic.cluster_availability_service import ClusterAvailabilityService
from logic.subscriptions_service import SubscriptionsService
from models.algorithms import Algorithms
from models.cluster_availability import ClusterAvailabilityScore
from models.subscription import SubscriptionScore

_busyness_subscription_algo_mapping: dict[ClusterAvailabilityScore, dict[SubscriptionScore, Algorithms]] = {
    ClusterAvailabilityScore.AVAILABLE: {
        SubscriptionScore.PREMIUM: Algorithms.GREEDY,
        SubscriptionScore.STANDARD: Algorithms.GREEDY,
    },
    ClusterAvailabilityScore.MODERATE: {
        SubscriptionScore.PREMIUM: Algorithms.GREEDY,
        SubscriptionScore.STANDARD: Algorithms.GREEDY,
    },
    ClusterAvailabilityScore.BUSY: {
        SubscriptionScore.PREMIUM: Algorithms.GREEDY,
        SubscriptionScore.STANDARD: Algorithms.FIRST_FIT,
    },
    ClusterAvailabilityScore.VERY_BUSY: {
        SubscriptionScore.PREMIUM: Algorithms.GREEDY,
        SubscriptionScore.STANDARD: Algorithms.FIRST_FIT,
    },
}


class AlgorithmDecider:
    def __init__(
        self, subscriptions_service: SubscriptionsService, cluster_availability_service: ClusterAvailabilityService
    ):
        self._subscriptions_service: SubscriptionsService = subscriptions_service
        self._cluster_availability_service = cluster_availability_service

    async def decide(self, knapsack_id: str) -> Algorithms:
        availability = await self._cluster_availability_service.get_cluster_availability_score()
        subscription_score = await self._subscriptions_service.get_subscription_score(knapsack_id)
        algo = _busyness_subscription_algo_mapping.get(availability, {}).get(subscription_score)
        if not algo:
            print(
                f"Could not find score mapping for availability {availability.name} "
                f"and subscription {subscription_score.name} given to knapsack {knapsack_id}. "
                "Returning lightest algorithm"
            )
            return Algorithms.FIRST_FIT
        return algo
