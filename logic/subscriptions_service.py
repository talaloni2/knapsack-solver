from models.subscription import SubscriptionType, SubscriptionScore


class SubscriptionsService:
    def __init__(self):
        self._subscription_type_to_score = {SubscriptionType.PREMIUM: 2, SubscriptionType.STANDARD: 1}

    async def get_subscription_score(self, knapsack_id: str) -> SubscriptionScore:
        return SubscriptionScore.STANDARD
