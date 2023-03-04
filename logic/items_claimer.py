from __future__ import annotations

from aioredis import Redis

from models.knapsack_item import KnapsackItem


class ItemsClaimer:
    def __init__(self, redis: Redis, items_claim_hash: str):
        self._redis = redis
        self._items_claim_hash = items_claim_hash

    async def claim_items(self, items: list[KnapsackItem], volume: int, knapsack_id: str) -> list[KnapsackItem]:
        return [
            item
            for item in items
            if item.volume <= volume and await self._redis.hsetnx(self._items_claim_hash, item.id, knapsack_id)
        ]

    async def release_claims(self, items: list[KnapsackItem]) -> None:
        await self._redis.hdel(self._items_claim_hash, *(i.id for i in items))
