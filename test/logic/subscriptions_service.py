from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient

from logic.subscriptions_service import SubscriptionsService
from models.subscription import SubscriptionScore


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "subscription_type,subscription_score",
    [
        ["Premium", SubscriptionScore.PREMIUM],
        ["Basic", SubscriptionScore.STANDARD],
    ],
)
async def test_subscriptions_service(subscription_type: str, subscription_score: SubscriptionScore):
    client = AsyncMock(AsyncClient)
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value={"result": {"subscription_name": subscription_type}})
    client.get = AsyncMock(return_value=resp)

    sub = await SubscriptionsService(client).get_subscription_score("mock")

    assert sub == subscription_score
