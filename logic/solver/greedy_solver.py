from __future__ import annotations

from dataclasses import dataclass

from logic.solver.base_solver import BaseSolver
from models.knapsack_item import KnapsackItem


@dataclass
class SortableKnapsackItem:
    item: KnapsackItem
    specific_weight: float

    def __lt__(self, other: SortableKnapsackItem):
        return self.specific_weight < other.specific_weight


class GreedySolver(BaseSolver):
    def solve(self, items: list[KnapsackItem], volume: int) -> list[KnapsackItem]:
        sorted_items: list[SortableKnapsackItem] = self._sort_items_by_specific_weight_descending(items)
        picked_items = self._fill_sack(sorted_items, volume)

        return picked_items

    @staticmethod
    def _sort_items_by_specific_weight_descending(items: list[KnapsackItem]) -> list[SortableKnapsackItem]:
        return list(reversed(sorted((SortableKnapsackItem(item=i, specific_weight=i.value / i.volume) for i in items))))

    @staticmethod
    def _fill_sack(sorted_items: list[SortableKnapsackItem], volume: int):
        picked_items: list[KnapsackItem] = []
        for item in sorted_items:
            if volume == 0:
                break
            if volume - item.item.volume >= 0:
                picked_items.append(item.item)
                volume -= item.item.volume
        return picked_items
