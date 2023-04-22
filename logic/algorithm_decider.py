from logic.cluster_availability_service import ClusterAvailabilityService
from logic.subscriptions_service import SubscriptionsService
from models.algorithms import Algorithms
from models.cluster_availability import ClusterAvailabilityScore
from models.subscription import SubscriptionScore

_busyness_subscription_algo_mapping: dict[ClusterAvailabilityScore, dict[SubscriptionScore, Algorithms]] = {
    ClusterAvailabilityScore.AVAILABLE: {
        SubscriptionScore.PREMIUM: Algorithms.BRANCH_AND_BOUND,
        SubscriptionScore.STANDARD: Algorithms.GENETIC_HEAVY,
    },
    ClusterAvailabilityScore.MODERATE: {
        SubscriptionScore.PREMIUM: Algorithms.DYNAMIC_PROGRAMMING,
        SubscriptionScore.STANDARD: Algorithms.GENETIC_LIGHT,
    },
    ClusterAvailabilityScore.BUSY: {
        SubscriptionScore.PREMIUM: Algorithms.GENETIC_HEAVY,
        SubscriptionScore.STANDARD: Algorithms.GREEDY,
    },
    ClusterAvailabilityScore.VERY_BUSY: {
        SubscriptionScore.PREMIUM: Algorithms.GENETIC_LIGHT,
        SubscriptionScore.STANDARD: Algorithms.GREEDY,
    },
}


class AlgorithmDecider:
    def __init__(
        self,
        subscriptions_service: SubscriptionsService,
        cluster_availability_service: ClusterAvailabilityService,
        branch_and_bound_max_items: int,
        dynamic_programming_max_iterations: int,
    ):
        self._subscriptions_service: SubscriptionsService = subscriptions_service
        self._cluster_availability_service = cluster_availability_service
        self._branch_and_bound_max_items = branch_and_bound_max_items
        self._dynamic_programming_max_iterations = dynamic_programming_max_iterations

    async def decide(self, knapsack_id: str, items_count: int, capacity: int) -> Algorithms:
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
        algo = await self._include_complexity_in_decision(algo, capacity, items_count)
        return algo

    async def _include_complexity_in_decision(self, algo, capacity, items_count):
        if algo == Algorithms.BRANCH_AND_BOUND and items_count > self._branch_and_bound_max_items:
            algo = Algorithms.DYNAMIC_PROGRAMMING
        if algo == Algorithms.DYNAMIC_PROGRAMMING and capacity * items_count > self._dynamic_programming_max_iterations:
            algo = Algorithms.GENETIC_HEAVY
        return algo
