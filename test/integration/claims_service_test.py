import pytest
from aioredis import Redis
from pytest_mock import MockerFixture

from component_factory import get_claims_service
from logic.claims_service import ClaimsService
from models.config.configuration import Config
from models.knapsack_item import KnapsackItem
from test.utils import get_random_string


@pytest.mark.asyncio
async def test_claim_items(config: Config):
    claimer: ClaimsService = get_claims_service(config=config)
    previously_claimed_items = [KnapsackItem(id=get_random_string(), value=1, volume=1)]
    expected_claim = [
        KnapsackItem(id=get_random_string(), value=2, volume=1),
        KnapsackItem(id=get_random_string(), value=3, volume=1),
    ]
    claim_request = expected_claim + previously_claimed_items

    previously_claimed = await claimer.claim_items(previously_claimed_items, 1, get_random_string())
    claim = await claimer.claim_items(claim_request, 1, get_random_string())

    assert previously_claimed_items == previously_claimed
    assert expected_claim == claim


async def _claim_suggested_solution(redis_client, suggested_solution_claimed_items, suggested_solutions_hash_name):
    await redis_client.hset(suggested_solutions_hash_name, suggested_solution_claimed_items[0].id, get_random_string())


@pytest.mark.asyncio
async def test_release_claims(config: Config):
    claimer: ClaimsService = get_claims_service(config=config)
    expected_claim = [
        KnapsackItem(id=get_random_string(), value=3, volume=1),
        KnapsackItem(id=get_random_string(), value=2, volume=1),
    ]
    current_knapsack = get_random_string()

    current_claim = await claimer.claim_items(expected_claim, 1, current_knapsack)
    await claimer.release_items_claims(expected_claim)
    second_claim = await claimer.claim_items(expected_claim, 1, current_knapsack)

    assert current_claim == expected_claim
    assert second_claim == expected_claim


@pytest.mark.asyncio
async def test_release_no_item_claims_do_not_perform_delete(config: Config, mocker: MockerFixture, redis_client: Redis):
    hdel_spy = mocker.spy(redis_client, "hdel")
    claimer: ClaimsService = get_claims_service(config=config)

    await claimer.release_items_claims([])

    hdel_spy.assert_not_called()


@pytest.mark.asyncio
async def test_claim_running_knapsack(config: Config, knapsack_id):
    claimer: ClaimsService = get_claims_service(config=config)

    first_claim = await claimer.claim_running_knapsack(knapsack_id)
    unsuccessful_claim = await claimer.claim_running_knapsack(knapsack_id)
    await claimer.release_claim_running_knapsack(knapsack_id)
    second_claim = await claimer.claim_running_knapsack(knapsack_id)

    assert first_claim is True
    assert unsuccessful_claim is False
    assert second_claim is True


@pytest.mark.asyncio
async def test_check_claims(config: Config, knapsack_id):
    claimer: ClaimsService = get_claims_service(config=config)
    expected_claim = [
        KnapsackItem(id=get_random_string(), value=3, volume=1),
        KnapsackItem(id=get_random_string(), value=2, volume=1),
    ]

    no_claims_expected = [await claimer.is_item_claimed(i.id) for i in expected_claim]
    assert not any(no_claims_expected), "No item should be claimed"
    await claimer.claim_items(expected_claim, 1, knapsack_id)
    all_claims_expected = [await claimer.is_item_claimed(i.id) for i in expected_claim]
    assert all(all_claims_expected), "Not all items claimed"
    await claimer.release_items_claims(expected_claim)
