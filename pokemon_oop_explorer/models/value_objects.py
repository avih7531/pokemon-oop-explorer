"""Supporting value objects used across the domain model."""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from .enums import ElementType, StatKind

if TYPE_CHECKING:
    from .moves import Move
    from .pokemon import PokemonSpecies
    from .evolution import EvolutionRule


@dataclass(frozen=True, slots=True)
class Type:
    """A type wrapper around the enum to keep value-object semantics."""

    element: ElementType

    def __str__(self) -> str:
        return self.element.value


@dataclass(slots=True)
class PokemonIdentity:
    """Identity values for an owned Pokemon instance."""

    trainer_id: int
    secret_id: int
    personality_value: int

    @dataclass(frozen=True, slots=True)
    class ShinyComputation:
        """Gen 3 shiny computation helper."""

        trainer_id: int
        secret_id: int
        personality_value: int

        @property
        def pid_high(self) -> int:
            return (self.personality_value >> 16) & 0xFFFF

        @property
        def pid_low(self) -> int:
            return self.personality_value & 0xFFFF

        @property
        def shiny_value(self) -> int:
            return self.trainer_id ^ self.secret_id ^ self.pid_high ^ self.pid_low

        @property
        def is_shiny(self) -> bool:
            return self.shiny_value < 8

    def shiny_report(self) -> "PokemonIdentity.ShinyComputation":
        return PokemonIdentity.ShinyComputation(
            trainer_id=self.trainer_id,
            secret_id=self.secret_id,
            personality_value=self.personality_value,
        )


@dataclass(frozen=True, slots=True)
class BaseStat(ABC):
    """A named stat value object."""

    value: int

    @property
    def kind(self) -> StatKind:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class HPStat(BaseStat):
    @property
    def kind(self) -> StatKind:
        return StatKind.HP


@dataclass(frozen=True, slots=True)
class AttackStat(BaseStat):
    @property
    def kind(self) -> StatKind:
        return StatKind.ATTACK


@dataclass(frozen=True, slots=True)
class DefenseStat(BaseStat):
    @property
    def kind(self) -> StatKind:
        return StatKind.DEFENSE


@dataclass(frozen=True, slots=True)
class SpecialAttackStat(BaseStat):
    @property
    def kind(self) -> StatKind:
        return StatKind.SPECIAL_ATTACK


@dataclass(frozen=True, slots=True)
class SpecialDefenseStat(BaseStat):
    @property
    def kind(self) -> StatKind:
        return StatKind.SPECIAL_DEFENSE


@dataclass(frozen=True, slots=True)
class SpeedStat(BaseStat):
    @property
    def kind(self) -> StatKind:
        return StatKind.SPEED


@dataclass(frozen=True, slots=True)
class Nature:
    """Value object capturing a Pokemon's personality-driven stat bias.

    A nature raises one stat by 10% and lowers another by 10% (or is neutral
    when both sides point at the same stat). The 25 canonical natures are
    available as class-level constants below.
    """

    name: str
    boosted_stat: StatKind
    hindered_stat: StatKind

    @property
    def is_neutral(self) -> bool:
        return self.boosted_stat is self.hindered_stat

    def modifier_for(self, stat: StatKind) -> float:
        if self.is_neutral:
            return 1.0
        if stat is self.boosted_stat:
            return 1.1
        if stat is self.hindered_stat:
            return 0.9
        return 1.0


NATURES: dict[str, Nature] = {
    nature.name: nature
    for nature in (
        Nature(
            name="Hardy", boosted_stat=StatKind.ATTACK, hindered_stat=StatKind.ATTACK
        ),
        Nature(
            name="Adamant",
            boosted_stat=StatKind.ATTACK,
            hindered_stat=StatKind.SPECIAL_ATTACK,
        ),
        Nature(
            name="Modest",
            boosted_stat=StatKind.SPECIAL_ATTACK,
            hindered_stat=StatKind.ATTACK,
        ),
        Nature(
            name="Timid", boosted_stat=StatKind.SPEED, hindered_stat=StatKind.ATTACK
        ),
        Nature(
            name="Bold", boosted_stat=StatKind.DEFENSE, hindered_stat=StatKind.ATTACK
        ),
        Nature(
            name="Jolly",
            boosted_stat=StatKind.SPEED,
            hindered_stat=StatKind.SPECIAL_ATTACK,
        ),
        Nature(
            name="Calm",
            boosted_stat=StatKind.SPECIAL_DEFENSE,
            hindered_stat=StatKind.ATTACK,
        ),
        Nature(
            name="Careful",
            boosted_stat=StatKind.SPECIAL_DEFENSE,
            hindered_stat=StatKind.SPECIAL_ATTACK,
        ),
    )
}


@dataclass(slots=True)
class StatBlock:
    """Container object for all major battle stats."""

    hp: HPStat
    attack: AttackStat
    defense: DefenseStat
    special_attack: SpecialAttackStat
    special_defense: SpecialDefenseStat
    speed: SpeedStat

    def as_dict(self) -> dict[str, int]:
        return {
            "HP": self.hp.value,
            "Attack": self.attack.value,
            "Defense": self.defense.value,
            "Sp. Attack": self.special_attack.value,
            "Sp. Defense": self.special_defense.value,
            "Speed": self.speed.value,
        }


@dataclass(frozen=True, slots=True)
class MoveSlot:
    """A learned move assigned to an instance slot."""

    move: "Move"
    current_pp: int


@dataclass(slots=True)
class Learnset:
    """Species-level learnset keyed by minimum level."""

    moves_by_level: dict[int, list["Move"]] = field(default_factory=dict)

    def add_move(self, level: int, move: "Move") -> None:
        self.moves_by_level.setdefault(level, []).append(move)

    def moves_up_to_level(self, level: int) -> list["Move"]:
        known: list["Move"] = []
        for learned_level, moves in sorted(self.moves_by_level.items()):
            if learned_level <= level:
                known.extend(moves)
        return known


@dataclass(frozen=True, slots=True)
class SpriteAsset:
    """Pointer to a local ANSI sprite file."""

    species_key: str
    regular_path: Path
    shiny_path: Path

    def load(self, *, shiny: bool) -> str:
        target = self.shiny_path if shiny else self.regular_path
        if not target.exists():
            return f"Sprite not found for {self.species_key}."
        return target.read_text(encoding="utf-8")


@dataclass(slots=True)
class EvolutionLine:
    """Sequence of species stages in one family evolution chain."""

    @dataclass(frozen=True, slots=True)
    class EvolutionStage:
        species: "PokemonSpecies"
        index: int
        rule: "EvolutionRule | None" = None

    stages: list["EvolutionLine.EvolutionStage"] = field(default_factory=list)

    def add_stage(
        self, species: "PokemonSpecies", index: int, rule: "EvolutionRule | None"
    ) -> None:
        self.stages.append(
            EvolutionLine.EvolutionStage(species=species, index=index, rule=rule)
        )

    def describe(self) -> list[str]:
        lines: list[str] = []
        for stage in sorted(self.stages, key=lambda s: s.index):
            if stage.rule is None:
                lines.append(f"{stage.index}. {stage.species.name} (base stage)")
            else:
                lines.append(
                    f"{stage.index}. {stage.species.name} <- {stage.rule.short_description()}"
                )
        return lines
