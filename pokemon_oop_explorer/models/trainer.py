"""Trainer entity that aggregates owned Pokemon instances."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .base import AbstractDomainObject
from .value_objects import SpriteAsset

if TYPE_CHECKING:
    from .pokemon import PokemonInstance
    from .visitor import DomainVisitor


@dataclass(frozen=True, slots=True)
class TrainerIdentity:
    """Identity triplet shared by every owned Pokemon (for shiny math)."""

    trainer_id: int
    secret_id: int
    display_name: str = ""


@dataclass(slots=True)
class Trainer(AbstractDomainObject):
    """A trainer owns a party of :class:`PokemonInstance` objects."""

    identity: TrainerIdentity | None = None
    party: list["PokemonInstance"] = field(default_factory=list)
    badges: int = 0
    home_town: str = ""
    sprite_asset: SpriteAsset | None = None

    def add_to_party(self, instance: "PokemonInstance") -> None:
        self.party.append(instance)
        instance.owner = self

    def remove_from_party(self, instance: "PokemonInstance") -> None:
        if instance in self.party:
            self.party.remove(instance)
            if instance.owner is self:
                instance.owner = None

    @property
    def party_size(self) -> int:
        return len(self.party)

    def active_pokemon(self) -> "PokemonInstance | None":
        return self.party[0] if self.party else None

    def accept(self, visitor: "DomainVisitor") -> None:
        visitor.visit_trainer(self)

    def inspect_payload(self) -> dict[str, Any]:
        payload = super().inspect_payload()
        payload.update(
            {
                "trainer_id": self.identity.trainer_id if self.identity else None,
                "secret_id": self.identity.secret_id if self.identity else None,
                "display_name": self.identity.display_name
                if self.identity
                else self.name,
                "badges": self.badges,
                "home_town": self.home_town,
                "party_size": self.party_size,
                "party": [
                    {
                        "name": instance.display_name,
                        "class": instance.__class__.__name__,
                        "species": instance.species.name
                        if instance.species
                        else "Unknown",
                        "level": instance.level,
                    }
                    for instance in self.party
                ],
            }
        )
        return payload
