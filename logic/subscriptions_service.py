from http import HTTPStatus

from httpx import AsyncClient

from logger import logger
from models.subscription import SubscriptionType, SubscriptionScore


class SubscriptionsService:
    def __init__(self, client: AsyncClient):
        self._subscription_type_to_score = {SubscriptionType.PREMIUM: SubscriptionScore.PREMIUM,
                                            SubscriptionType.STANDARD: SubscriptionScore.STANDARD}
        self._client: AsyncClient = client

    async def get_subscription_score(self, knapsack_id: str) -> SubscriptionScore:
        res = await self._client.get(f"/user_subscription_maps/{knapsack_id}")
        if res.status_code != HTTPStatus.OK and res.status_code != HTTPStatus.NOT_FOUND:
            try:
                res.raise_for_status()
            except Exception as e:
                logger.error("Got unexpected error from subscriptions server. Aborting.", exc_info=e)
                raise

        elif res.status_code == HTTPStatus.NOT_FOUND:
            logger.info(f"Could not find subscription. Using 'standard' score. Error message: {res.content}")
            return SubscriptionScore.STANDARD

        return self._subscription_type_to_score.get(res.json()["result"]["subscription_name"], SubscriptionScore.STANDARD)
