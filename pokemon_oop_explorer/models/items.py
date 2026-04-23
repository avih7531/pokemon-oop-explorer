"""Item class hierarchy."""

from __future__ import annotations

from dataclasses import dataclass

from .base import AbstractDomainObject
from .enums import ItemCategory


@dataclass(slots=True)
class Item(AbstractDomainObject):
    category: ItemCategory = ItemCategory.CONSUMABLE


@dataclass(slots=True)
class HeldItem(Item):
    category: ItemCategory = ItemCategory.HELD


@dataclass(slots=True)
class ConsumableItem(Item):
    category: ItemCategory = ItemCategory.CONSUMABLE


@dataclass(slots=True)
class EvolutionItem(Item):
    category: ItemCategory = ItemCategory.EVOLUTION
