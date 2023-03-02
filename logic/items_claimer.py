from __future__ import annotations
from models.knapsack_item import KnapsackItem


def get_items_claimer() -> ItemsClaimer:
    return ItemsClaimer()


class ItemsClaimer:
    async def claim_items(self, items: list[KnapsackItem], volume: int, knapsack_id: str) -> list[KnapsackItem]:
        """STUB"""
        return [i for i in items if i.volume <= volume]
