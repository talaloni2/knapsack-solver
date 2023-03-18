import pytest

from component_factory import get_claims_service
from logic.claims_service import ClaimsService
from models.knapsack_item import KnapsackItem
from test.utils import get_random_string


@pytest.mark.asyncio
async def test_claim_items(items_claim_hash_name: str):
    claimer: ClaimsService = get_claims_service(items_claim_hash_name=items_claim_hash_name)
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
async def test_release_claims(items_claim_hash_name: str):
    claimer: ClaimsService = get_claims_service(items_claim_hash_name=items_claim_hash_name)
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
