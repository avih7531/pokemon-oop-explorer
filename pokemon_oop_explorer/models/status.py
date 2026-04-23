"""Status-condition hierarchy applied to :class:`PokemonInstance` objects."""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .base import AbstractDomainObject

if TYPE_CHECKING:
    from .pokemon import PokemonInstance


@dataclass(slots=True)
class StatusCondition(AbstractDomainObject):
    """Polymorphic non-volatile condition attached to a Pokemon instance."""

    @abstractmethod
    def tick(self, instance: "PokemonInstance") -> str:
        """Advance the condition one turn; return a log message."""

    def can_act(self, instance: "PokemonInstance") -> bool:  # noqa: ARG002
        """Whether the afflicted Pokemon can act this turn."""
        return True


@dataclass(slots=True)
class BurnStatus(StatusCondition):
    name: str = "Burn"
    description: str = "Deals damage each turn and halves physical attack."
    damage_per_turn: int = 6

    def tick(self, instance: "PokemonInstance") -> str:
        instance.current_hp = max(0, instance.current_hp - self.damage_per_turn)
        return (
            f"{instance.display_name} is hurt by its burn ({self.damage_per_turn} HP)."
        )


@dataclass(slots=True)
class PoisonStatus(StatusCondition):
    name: str = "Poison"
    description: str = "Deals damage each turn."
    damage_per_turn: int = 4

    def tick(self, instance: "PokemonInstance") -> str:
        instance.current_hp = max(0, instance.current_hp - self.damage_per_turn)
        return f"{instance.display_name} is hurt by poison ({self.damage_per_turn} HP)."


@dataclass(slots=True)
class ParalysisStatus(StatusCondition):
    name: str = "Paralysis"
    description: str = "Speed is reduced and the Pokemon may fail to act."
    skip_chance: float = 0.25

    def tick(self, instance: "PokemonInstance") -> str:  # noqa: ARG002
        return f"Paralysis slows {instance.display_name}."

    def can_act(self, instance: "PokemonInstance") -> bool:  # noqa: ARG002
        return True


@dataclass(slots=True)
class SleepStatus(StatusCondition):
    name: str = "Sleep"
    description: str = "The Pokemon cannot act while asleep."
    turns_remaining: int = 2

    def tick(self, instance: "PokemonInstance") -> str:
        self.turns_remaining = max(0, self.turns_remaining - 1)
        if self.turns_remaining == 0:
            return f"{instance.display_name} woke up!"
        return f"{instance.display_name} is fast asleep."

    def can_act(self, instance: "PokemonInstance") -> bool:  # noqa: ARG002
        return self.turns_remaining == 0


@dataclass(slots=True)
class FreezeStatus(StatusCondition):
    name: str = "Freeze"
    description: str = "The Pokemon is frozen solid and cannot act."
    thaw_chance: float = 0.2

    def tick(self, instance: "PokemonInstance") -> str:
        return f"{instance.display_name} is frozen solid."

    def can_act(self, instance: "PokemonInstance") -> bool:  # noqa: ARG002
        return False
