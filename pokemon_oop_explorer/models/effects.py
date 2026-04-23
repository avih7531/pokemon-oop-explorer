"""Move-effect hierarchy.

``Move`` composes a list of ``AbstractEffect`` objects, so a single move can
e.g. deal damage *and* burn the target by combining multiple effect instances
instead of relying on flat numeric fields.
"""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .base import AbstractDomainObject
from .enums import StatKind

if TYPE_CHECKING:
    from .pokemon import PokemonInstance
    from .status import StatusCondition


@dataclass(slots=True)
class EffectContext:
    """Execution context passed through every ``AbstractEffect.apply`` call."""

    source: "PokemonInstance"
    target: "PokemonInstance"
    crit: bool = False


@dataclass(slots=True)
class EffectResult:
    """Structured summary of what a single effect did."""

    effect_name: str
    message: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AbstractEffect(AbstractDomainObject):
    """Polymorphic base class for move effects."""

    @abstractmethod
    def apply(self, context: EffectContext) -> EffectResult:
        """Execute this effect and return a description of the outcome."""


@dataclass(slots=True)
class DamageEffect(AbstractEffect):
    """Reduces the target's current HP by a base amount."""

    base_damage: int = 10

    def apply(self, context: EffectContext) -> EffectResult:
        multiplier = 2 if context.crit else 1
        damage = self.base_damage * multiplier
        before = context.target.current_hp
        context.target.current_hp = max(0, before - damage)
        return EffectResult(
            effect_name=self.name or "Damage",
            message=f"{context.target.display_name} lost {before - context.target.current_hp} HP.",
            data={"damage": before - context.target.current_hp, "crit": context.crit},
        )


@dataclass(slots=True)
class HealEffect(AbstractEffect):
    """Restores HP on the source (self-heal) or target."""

    heal_amount: int = 20
    target_self: bool = True

    def apply(self, context: EffectContext) -> EffectResult:
        receiver = context.source if self.target_self else context.target
        before = receiver.current_hp
        receiver.current_hp = before + self.heal_amount
        return EffectResult(
            effect_name=self.name or "Heal",
            message=f"{receiver.display_name} recovered {self.heal_amount} HP.",
            data={"recovered": self.heal_amount, "target_self": self.target_self},
        )


@dataclass(slots=True)
class StatusEffect(AbstractEffect):
    """Applies a :class:`StatusCondition` to the target."""

    condition_factory: "type[StatusCondition] | None" = None

    def apply(self, context: EffectContext) -> EffectResult:
        if self.condition_factory is None:
            return EffectResult(
                effect_name=self.name or "Status",
                message="No status condition configured.",
            )
        condition = self.condition_factory()
        context.target.status = condition
        return EffectResult(
            effect_name=self.name or "Status",
            message=f"{context.target.display_name} is now afflicted with {condition.name}.",
            data={"condition": condition.__class__.__name__},
        )


@dataclass(slots=True)
class StatStageEffect(AbstractEffect):
    """Raises or lowers a stat stage on the target."""

    stat: StatKind = StatKind.ATTACK
    delta: int = 1
    target_self: bool = False

    def apply(self, context: EffectContext) -> EffectResult:
        receiver = context.source if self.target_self else context.target
        stages = getattr(receiver, "stat_stages", None)
        if stages is None:
            stages = {}
            setattr(receiver, "stat_stages", stages)
        current = stages.get(self.stat.value, 0)
        new_value = max(-6, min(6, current + self.delta))
        stages[self.stat.value] = new_value
        direction = "rose" if self.delta > 0 else "fell"
        return EffectResult(
            effect_name=self.name or "StatStage",
            message=f"{receiver.display_name}'s {self.stat.value} {direction}.",
            data={"stat": self.stat.value, "from": current, "to": new_value},
        )
