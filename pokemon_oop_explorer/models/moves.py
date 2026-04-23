"""Move class hierarchy."""

from __future__ import annotations

from dataclasses import dataclass, field

from .base import AbstractDomainObject
from .effects import AbstractEffect
from .enums import MoveCategory
from .value_objects import Type


@dataclass(slots=True)
class Move(AbstractDomainObject):
    power: int | None = None
    accuracy: int | None = None
    pp: int = 0
    move_type: Type | None = None
    category: MoveCategory = MoveCategory.STATUS
    effects: list[AbstractEffect] = field(default_factory=list)


@dataclass(slots=True)
class OffensiveMove(Move):
    power: int = 40
    accuracy: int = 100


@dataclass(slots=True)
class PhysicalMove(OffensiveMove):
    category: MoveCategory = MoveCategory.PHYSICAL


@dataclass(slots=True)
class SpecialMove(OffensiveMove):
    category: MoveCategory = MoveCategory.SPECIAL


@dataclass(slots=True)
class StatusMove(Move):
    category: MoveCategory = MoveCategory.STATUS
    power: int | None = None
