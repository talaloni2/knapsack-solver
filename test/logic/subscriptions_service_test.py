from http import HTTPStatus
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
    resp.status_code = HTTPStatus.OK
    resp.json = MagicMock(return_value={"result": {"subscription_name": subscription_type}})
    client.get = AsyncMock(return_value=resp)

    sub = await SubscriptionsService(client).get_subscription_score("mock")

    assert sub == subscription_score


async def test_subscription_not_found():
    client = AsyncMock(AsyncClient)
    resp = MagicMock()
    resp.status_code = HTTPStatus.NOT_FOUND
    client.get = AsyncMock(return_value=resp)

    sub = await SubscriptionsService(client).get_subscription_score("mock")

    assert sub == SubscriptionScore.STANDARD


class SubscriptionTestException(Exception):
    pass


async def test_subscription_unknown_error():
    client = AsyncMock(AsyncClient)
    resp = MagicMock()
    resp.raise_for_status = MagicMock(side_effect=SubscriptionTestException("lalala"))
    resp.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    client.get = AsyncMock(return_value=resp)

    with pytest.raises(SubscriptionTestException):
        await SubscriptionsService(client).get_subscription_score("mock")
