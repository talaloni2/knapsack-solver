from httpx import AsyncClient

from models.subscription import SubscriptionType, SubscriptionScore


class SubscriptionsService:
    def __init__(self, client: AsyncClient):
        self._subscription_type_to_score = {SubscriptionType.PREMIUM: SubscriptionScore.PREMIUM,
                                            SubscriptionType.STANDARD: SubscriptionScore.STANDARD}
        self._client: AsyncClient = client

    async def get_subscription_score(self, knapsack_id: str) -> SubscriptionScore:
        res = await self._client.get(f"/user_subscription_maps/{knapsack_id}")
        res.raise_for_status()

        return self._subscription_type_to_score.get(res.json()["result"]["subscription_name"], SubscriptionScore.STANDARD)
