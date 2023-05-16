from __future__ import annotations

from aioredis import Redis

from models.knapsack_item import KnapsackItem


class ClaimsService:
    def __init__(
        self, redis: Redis, items_claim_hash: str, suggested_solutions_claim_hash: str, running_knapsack_claim_hash: str
    ):
        self._redis = redis
        self._items_claim_hash = items_claim_hash
        self._suggested_solutions_claim_hash = suggested_solutions_claim_hash
        self._running_knapsack_claim_hash = running_knapsack_claim_hash

    async def claim_items(self, items: list[KnapsackItem], volume: int, knapsack_id: str) -> list[KnapsackItem]:
        return [
            item
            for item in items
            if item.volume <= volume and await self._redis.hsetnx(self._items_claim_hash, item.id, knapsack_id)
        ]

    async def release_items_claims(self, items: list[KnapsackItem]) -> None:
        items_ids = {i.id for i in items}
        if not items_ids:
            return
        await self._redis.hdel(self._items_claim_hash, *items_ids)

    async def claim_suggested_solutions(self, knapsack_id: str) -> bool:
        return bool(await self._redis.hsetnx(self._suggested_solutions_claim_hash, knapsack_id, knapsack_id))

    async def release_claim_suggested_solutions(self, knapsack_id: str) -> None:
        await self._redis.hdel(self._suggested_solutions_claim_hash, knapsack_id)

    async def claim_running_knapsack(self, knapsack_id: str) -> bool:
        return bool(await self._redis.hsetnx(self._running_knapsack_claim_hash, knapsack_id, knapsack_id))

    async def release_claim_running_knapsack(self, knapsack_id: str) -> None:
        await self._redis.hdel(self._running_knapsack_claim_hash, knapsack_id)

    async def is_item_claimed(self, item_id: str):
        res = await self._redis.hget(self._items_claim_hash, item_id)
        return res is not None
