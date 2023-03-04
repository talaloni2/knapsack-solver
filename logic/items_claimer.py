from __future__ import annotations

import asyncio

from aioredis import Redis

from models.knapsack_item import KnapsackItem


class ItemsClaimer:
    def __init__(self, redis: Redis, claimed_items_hash_name: str):
        self._redis = redis
        self._claimed_items_hash_name = claimed_items_hash_name

    async def claim_items(self, items: list[KnapsackItem], volume: int, knapsack_id: str) -> list[KnapsackItem]:
        return [
            item
            for item in items
            if item.volume <= volume and await self._redis.hsetnx(self._claimed_items_hash_name, item.id, knapsack_id)
        ]

    async def verify_claims(self, items: list[KnapsackItem], knapsack_id: str) -> bool:
        knapsack_ids = await asyncio.gather(
            *(self._redis.hget(self._claimed_items_hash_name, item.id) for item in items)
        )
        return all((kid.decode() == knapsack_id if kid else False) for kid in knapsack_ids )

    async def release_claims(self, items: list[KnapsackItem]) -> None:
        await self._redis.hdel(self._claimed_items_hash_name, *(i.id for i in items))
