"""Pokemon species and instance hierarchy."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .abilities import Ability
from .base import AbstractDomainObject
from .enums import Generation
from .evolution import EvolutionRule
from .items import HeldItem
from .status import StatusCondition
from .value_objects import (
    EvolutionLine,
    Learnset,
    MoveSlot,
    Nature,
    PokemonIdentity,
    SpriteAsset,
    StatBlock,
    Type,
)

if TYPE_CHECKING:
    from .trainer import Trainer
    from .visitor import DomainVisitor


@dataclass(slots=True)
class PokemonSpecies(AbstractDomainObject):
    """Species-level definition and behavior."""

    species_key: str = ""
    dex_number: int = 0
    generation: Generation = Generation.GEN_1
    types: list[Type] = field(default_factory=list)
    base_stats: StatBlock | None = None
    possible_abilities: list[Ability] = field(default_factory=list)
    learnset: Learnset = field(default_factory=Learnset)
    evolution_rules: list[EvolutionRule] = field(default_factory=list)
    sprite_asset: SpriteAsset | None = None
    evolution_line: EvolutionLine | None = None

    def can_evolve(self) -> bool:
        return bool(self.evolution_rules)

    def accept(self, visitor: "DomainVisitor") -> None:
        visitor.visit_species(self)

    def inspect_payload(self) -> dict[str, Any]:
        payload = super().inspect_payload()
        learnset_payload = {
            level: [
                {
                    "name": move.name,
                    "class": move.__class__.__name__,
                    "type": str(move.move_type) if move.move_type else None,
                    "category": move.category.value,
                    "power": move.power,
                    "accuracy": move.accuracy,
                    "pp": move.pp,
                }
                for move in moves
            ]
            for level, moves in sorted(self.learnset.moves_by_level.items())
        }
        payload.update(
            {
                "species_key": self.species_key,
                "dex_number": self.dex_number,
                "generation": int(self.generation),
                "types": [str(t) for t in self.types],
                "abilities": [
                    {
                        "name": ability.name,
                        "class": ability.__class__.__name__,
                        "summary": getattr(ability, "effect_summary", ""),
                    }
                    for ability in self.possible_abilities
                ],
                "base_stats": self.base_stats.as_dict() if self.base_stats else {},
                "learnset": learnset_payload,
                "evolution_rules": [
                    rule.short_description() for rule in self.evolution_rules
                ],
                "evolution_line": self.evolution_line.describe()
                if self.evolution_line
                else [],
                "can_evolve": self.can_evolve(),
            }
        )
        return payload


@dataclass(slots=True)
class StarterSpecies(PokemonSpecies):
    starter_kind: str = "Generic Starter"


@dataclass(slots=True)
class GrassStarterSpecies(StarterSpecies):
    starter_kind: str = "Grass Starter"


@dataclass(slots=True)
class FireStarterSpecies(StarterSpecies):
    starter_kind: str = "Fire Starter"


@dataclass(slots=True)
class WaterStarterSpecies(StarterSpecies):
    starter_kind: str = "Water Starter"


@dataclass(slots=True)
class EvolutionStageSpecies(PokemonSpecies):
    stage_index: int = 1


@dataclass(slots=True)
class PokemonInstance(AbstractDomainObject):
    """Owned Pokemon with mutable battle-relevant state."""

    species: PokemonSpecies | None = None
    nickname: str = ""
    level: int = 5
    current_hp: int = 1
    move_slots: list[MoveSlot] = field(default_factory=list)
    held_item: HeldItem | None = None
    chosen_ability: Ability | None = None
    identity: PokemonIdentity | None = None
    friendship: int = 70
    status: StatusCondition | None = None
    nature: Nature | None = None
    owner: "Trainer | None" = None
    stat_stages: dict[str, int] = field(default_factory=dict)

    def effective_stats(self) -> dict[str, int]:
        if self.species is None or self.species.base_stats is None:
            return {}
        from .enums import (
            StatKind,
        )  # Local import to avoid circular import at module load.

        base = self.species.base_stats.as_dict()
        level = self.level
        effective: dict[str, int] = {}
        for stat_name, stat_value in base.items():
            if stat_name == "HP":
                raw = ((2 * stat_value) * level) // 100 + level + 10
            else:
                raw = ((2 * stat_value) * level) // 100 + 5
            if self.nature is not None:
                try:
                    stat_kind = StatKind(stat_name)
                except ValueError:
                    stat_kind = None
                if stat_kind is not None:
                    raw = int(raw * self.nature.modifier_for(stat_kind))
            effective[stat_name] = raw
        return effective

    def can_evolve(self) -> bool:
        if self.species is None:
            return False
        return any(
            rule.is_satisfied(level=self.level, friendship=self.friendship)
            for rule in self.species.evolution_rules
        )

    @property
    def display_name(self) -> str:
        return self.nickname or (self.species.name if self.species else self.name)

    def accept(self, visitor: "DomainVisitor") -> None:
        visitor.visit_instance(self)

    def inspect_payload(self) -> dict[str, Any]:
        payload = super().inspect_payload()
        shiny_data = self.identity.shiny_report() if self.identity else None
        move_payload = [
            {
                "name": slot.move.name,
                "class": slot.move.__class__.__name__,
                "type": str(slot.move.move_type) if slot.move.move_type else None,
                "category": slot.move.category.value,
                "power": slot.move.power,
                "accuracy": slot.move.accuracy,
                "pp": f"{slot.current_pp}/{slot.move.pp}",
            }
            for slot in self.move_slots
        ]
        payload.update(
            {
                "display_name": self.display_name,
                "species": self.species.name if self.species else "Unknown",
                "level": self.level,
                "current_hp": self.current_hp,
                "can_evolve_now": self.can_evolve(),
                "held_item": self.held_item.name if self.held_item else "None",
                "chosen_ability": self.chosen_ability.name
                if self.chosen_ability
                else "None",
                "status": self.status.name if self.status else "None",
                "nature": self.nature.name if self.nature else "None",
                "owner": self.owner.name if self.owner else "None",
                "moves": move_payload,
                "effective_stats": self.effective_stats(),
                "identity": {
                    "trainer_id": self.identity.trainer_id if self.identity else None,
                    "secret_id": self.identity.secret_id if self.identity else None,
                    "pid": self.identity.personality_value if self.identity else None,
                    "pid_hex": f"0x{self.identity.personality_value:08X}"
                    if self.identity
                    else None,
                    "pid_high": shiny_data.pid_high if shiny_data else None,
                    "pid_low": shiny_data.pid_low if shiny_data else None,
                    "shiny_value": shiny_data.shiny_value if shiny_data else None,
                    "is_shiny": shiny_data.is_shiny if shiny_data else None,
                    "formula": (
                        "TID xor SID xor PID_high xor PID_low < 8"
                        if shiny_data
                        else "Identity unavailable"
                    ),
                },
            }
        )
        return payload


@dataclass(slots=True)
class StarterPokemon(PokemonInstance):
    pass


@dataclass(slots=True)
class GrassStarterPokemon(StarterPokemon):
    pass


@dataclass(slots=True)
class FireStarterPokemon(StarterPokemon):
    pass


@dataclass(slots=True)
class WaterStarterPokemon(StarterPokemon):
    pass


@dataclass(slots=True)
class BattleReadyPokemon(PokemonInstance):
    ev_spread: dict[str, int] = field(default_factory=dict)

    def available_moves(self) -> list[str]:
        return [slot.move.name for slot in self.move_slots]
