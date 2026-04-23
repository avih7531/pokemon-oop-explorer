"""Visitor pattern for double-dispatch traversal of the domain model.

Using a visitor keeps cross-cutting operations (UML collection, summary
text, validation, ...) out of the domain classes themselves while exercising
real polymorphism instead of ``isinstance`` ladders.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .pokemon import PokemonInstance, PokemonSpecies
    from .trainer import Trainer


class DomainVisitor(ABC):
    """Abstract double-dispatch visitor over the domain model."""

    @abstractmethod
    def visit_species(self, species: "PokemonSpecies") -> None: ...

    @abstractmethod
    def visit_instance(self, instance: "PokemonInstance") -> None: ...

    @abstractmethod
    def visit_trainer(self, trainer: "Trainer") -> None: ...

    def visit_other(self, obj: object) -> None:
        """Hook for domain objects that don't have a dedicated dispatcher."""


class ClassUsageVisitor(DomainVisitor):
    """Records every concrete class encountered while walking sample data.

    The UML overview uses this to highlight the classes actually reachable
    from the seeded instances, rather than branching on ``isinstance``.
    """

    def __init__(self) -> None:
        self.seen_classes: set[type] = set()

    def _note(self, obj: object) -> None:
        self.seen_classes.add(type(obj))

    def visit_species(self, species: "PokemonSpecies") -> None:
        self._note(species)
        for ability in species.possible_abilities:
            self._note(ability)
        for rule in species.evolution_rules:
            self._note(rule)
        for move_list in species.learnset.moves_by_level.values():
            for move in move_list:
                self._note(move)
                for effect in getattr(move, "effects", []):
                    self._note(effect)

    def visit_instance(self, instance: "PokemonInstance") -> None:
        self._note(instance)
        if instance.species is not None:
            self.visit_species(instance.species)
        if instance.status is not None:
            self._note(instance.status)
        if instance.held_item is not None:
            self._note(instance.held_item)
        if instance.chosen_ability is not None:
            self._note(instance.chosen_ability)
        if instance.nature is not None:
            self._note(instance.nature)
        if instance.identity is not None:
            self._note(instance.identity)
        for slot in instance.move_slots:
            self._note(slot)
            self._note(slot.move)
            for effect in getattr(slot.move, "effects", []):
                self._note(effect)

    def visit_trainer(self, trainer: "Trainer") -> None:
        self._note(trainer)
        if trainer.identity is not None:
            self._note(trainer.identity)
        for instance in trainer.party:
            self.visit_instance(instance)


class SummaryVisitor(DomainVisitor):
    """Builds a short human-readable census for a collection of domain objects."""

    def __init__(self) -> None:
        self.species_count: int = 0
        self.instance_count: int = 0
        self.trainer_count: int = 0
        self.lines: list[str] = []

    def visit_species(self, species: "PokemonSpecies") -> None:
        self.species_count += 1
        self.lines.append(f"Species {species.name} ({species.__class__.__name__})")

    def visit_instance(self, instance: "PokemonInstance") -> None:
        self.instance_count += 1
        self.lines.append(
            f"Instance {instance.display_name} Lv{instance.level} "
            f"({instance.__class__.__name__})"
        )

    def visit_trainer(self, trainer: "Trainer") -> None:
        self.trainer_count += 1
        self.lines.append(
            f"Trainer {trainer.name} with {trainer.party_size} party members"
        )
