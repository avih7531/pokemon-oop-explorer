"""Evolution rule hierarchy."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .base import AbstractDomainObject


class EvolutionContextTimeOfDay(str, Enum):
    """Abstracted in-game clock for time-based evolutions."""

    DAY = "Day"
    NIGHT = "Night"
    ANY = "Any"


@dataclass(slots=True)
class EvolutionRule(AbstractDomainObject):
    target_species_key: str = ""

    def is_satisfied(
        self,
        *,
        level: int,
        friendship: int = 0,
        item_key: str | None = None,
        traded: bool = False,
        location: str | None = None,
        time_of_day: EvolutionContextTimeOfDay = EvolutionContextTimeOfDay.ANY,
    ) -> bool:
        return False

    def short_description(self) -> str:
        return self.description or self.name


@dataclass(slots=True)
class LevelEvolutionRule(EvolutionRule):
    minimum_level: int = 0

    def is_satisfied(
        self,
        *,
        level: int,
        friendship: int = 0,
        item_key: str | None = None,
        traded: bool = False,
        location: str | None = None,
        time_of_day: EvolutionContextTimeOfDay = EvolutionContextTimeOfDay.ANY,
    ) -> bool:
        return level >= self.minimum_level

    def short_description(self) -> str:
        return f"Level >= {self.minimum_level}"


@dataclass(slots=True)
class ItemEvolutionRule(EvolutionRule):
    required_item_key: str = ""

    def is_satisfied(
        self,
        *,
        level: int,
        friendship: int = 0,
        item_key: str | None = None,
        traded: bool = False,
        location: str | None = None,
        time_of_day: EvolutionContextTimeOfDay = EvolutionContextTimeOfDay.ANY,
    ) -> bool:
        return item_key == self.required_item_key

    def short_description(self) -> str:
        return f"Use item: {self.required_item_key}"


@dataclass(slots=True)
class FriendshipEvolutionRule(EvolutionRule):
    minimum_friendship: int = 220

    def is_satisfied(
        self,
        *,
        level: int,
        friendship: int = 0,
        item_key: str | None = None,
        traded: bool = False,
        location: str | None = None,
        time_of_day: EvolutionContextTimeOfDay = EvolutionContextTimeOfDay.ANY,
    ) -> bool:
        return friendship >= self.minimum_friendship

    def short_description(self) -> str:
        return f"Friendship >= {self.minimum_friendship}"


@dataclass(slots=True)
class TradeEvolutionRule(EvolutionRule):
    """Evolves when the Pokemon is traded (optionally while holding an item)."""

    required_held_item: str | None = None

    def is_satisfied(
        self,
        *,
        level: int,
        friendship: int = 0,
        item_key: str | None = None,
        traded: bool = False,
        location: str | None = None,
        time_of_day: EvolutionContextTimeOfDay = EvolutionContextTimeOfDay.ANY,
    ) -> bool:
        if not traded:
            return False
        if self.required_held_item is None:
            return True
        return item_key == self.required_held_item

    def short_description(self) -> str:
        if self.required_held_item:
            return f"Trade while holding {self.required_held_item}"
        return "Trade"


@dataclass(slots=True)
class LocationEvolutionRule(EvolutionRule):
    """Evolves only while training at a particular location."""

    required_location: str = ""

    def is_satisfied(
        self,
        *,
        level: int,
        friendship: int = 0,
        item_key: str | None = None,
        traded: bool = False,
        location: str | None = None,
        time_of_day: EvolutionContextTimeOfDay = EvolutionContextTimeOfDay.ANY,
    ) -> bool:
        return location == self.required_location

    def short_description(self) -> str:
        return f"Train at {self.required_location}"


@dataclass(slots=True)
class TimeOfDayEvolutionRule(EvolutionRule):
    """Level-based rule that additionally depends on the in-game clock."""

    minimum_level: int = 0
    required_time: EvolutionContextTimeOfDay = EvolutionContextTimeOfDay.DAY

    def is_satisfied(
        self,
        *,
        level: int,
        friendship: int = 0,
        item_key: str | None = None,
        traded: bool = False,
        location: str | None = None,
        time_of_day: EvolutionContextTimeOfDay = EvolutionContextTimeOfDay.ANY,
    ) -> bool:
        if level < self.minimum_level:
            return False
        if self.required_time is EvolutionContextTimeOfDay.ANY:
            return True
        return time_of_day is self.required_time

    def short_description(self) -> str:
        return f"Level >= {self.minimum_level} at {self.required_time.value}"


@dataclass(slots=True)
class CompositeEvolutionRule(EvolutionRule):
    """Composite pattern: combines child rules with AND / OR semantics."""

    children: list[EvolutionRule] = field(default_factory=list)
    require_all: bool = True

    def is_satisfied(
        self,
        *,
        level: int,
        friendship: int = 0,
        item_key: str | None = None,
        traded: bool = False,
        location: str | None = None,
        time_of_day: EvolutionContextTimeOfDay = EvolutionContextTimeOfDay.ANY,
    ) -> bool:
        if not self.children:
            return False
        checks = [
            child.is_satisfied(
                level=level,
                friendship=friendship,
                item_key=item_key,
                traded=traded,
                location=location,
                time_of_day=time_of_day,
            )
            for child in self.children
        ]
        return all(checks) if self.require_all else any(checks)

    def short_description(self) -> str:
        joiner = " AND " if self.require_all else " OR "
        return (
            joiner.join(child.short_description() for child in self.children)
            or "Composite"
        )
