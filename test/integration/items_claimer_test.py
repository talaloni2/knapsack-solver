import pytest

from component_factory import get_items_claimer
from logic.items_claimer import ItemsClaimer
from models.knapsack_item import KnapsackItem
from test.utils import get_random_string


@pytest.mark.asyncio
async def test_claim_items(random_hash_name: str):
    claimer: ItemsClaimer = get_items_claimer(claimed_items_hash_name=random_hash_name)
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


@pytest.mark.asyncio
async def test_verify_claims_not_all_verified(random_hash_name: str):
    claimer: ItemsClaimer = get_items_claimer(claimed_items_hash_name=random_hash_name)
    non_claimed_items = [KnapsackItem(id=get_random_string(), value=1, volume=1)]
    expected_claim = [KnapsackItem(id=get_random_string(), value=3, volume=1)]
    current_knapsack = get_random_string()
    claim_verification_request = expected_claim + non_claimed_items

    other_claim = await claimer.claim_items(non_claimed_items, 1, get_random_string())
    current_claim = await claimer.claim_items(expected_claim, 1, current_knapsack)
    claims_verification: bool = await claimer.verify_claims(claim_verification_request, current_knapsack)

    assert non_claimed_items == other_claim
    assert expected_claim == current_claim
    assert not claims_verification


@pytest.mark.asyncio
async def test_verify_claims_none_verified(random_hash_name: str):
    claimer: ItemsClaimer = get_items_claimer(claimed_items_hash_name=random_hash_name)
    non_claimed_items = [KnapsackItem(id=get_random_string(), value=1, volume=1)]
    current_knapsack = get_random_string()

    other_claim = await claimer.claim_items(non_claimed_items, 1, get_random_string())
    claims_verification: bool = await claimer.verify_claims(non_claimed_items, current_knapsack)

    assert non_claimed_items == other_claim
    assert not claims_verification


@pytest.mark.asyncio
async def test_verify_claims_all_verified(random_hash_name: str):
    claimer: ItemsClaimer = get_items_claimer(claimed_items_hash_name=random_hash_name)
    expected_claim = [KnapsackItem(id=get_random_string(), value=3, volume=1)]
    current_knapsack = get_random_string()

    current_claim = await claimer.claim_items(expected_claim, 1, current_knapsack)
    claims_verification: bool = await claimer.verify_claims(expected_claim, current_knapsack)

    assert expected_claim == current_claim
    assert claims_verification


@pytest.mark.asyncio
async def test_verify_claims_item_not_exists(random_hash_name: str):
    claimer: ItemsClaimer = get_items_claimer(claimed_items_hash_name=random_hash_name)
    verification_request = [KnapsackItem(id=get_random_string(), value=3, volume=1)]
    current_knapsack = get_random_string()

    claims_verification: bool = await claimer.verify_claims(verification_request, current_knapsack)

    assert not claims_verification


@pytest.mark.asyncio
async def test_release_claims(random_hash_name: str):
    claimer: ItemsClaimer = get_items_claimer(claimed_items_hash_name=random_hash_name)
    expected_claim = [KnapsackItem(id=get_random_string(), value=3, volume=1)]
    current_knapsack = get_random_string()

    verification_before_claim: bool = await claimer.verify_claims(expected_claim, current_knapsack)
    current_claim = await claimer.claim_items(expected_claim, 1, current_knapsack)
    verification_after_claim: bool = await claimer.verify_claims(expected_claim, current_knapsack)
    await claimer.release_claims(expected_claim)
    verification_after_release: bool = await claimer.verify_claims(expected_claim, current_knapsack)

    assert not verification_before_claim
    assert current_claim == expected_claim
    assert verification_after_claim
    assert not verification_after_release
