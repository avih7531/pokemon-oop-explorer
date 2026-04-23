"""Repository layer for explorer data access."""

from __future__ import annotations

from pathlib import Path

from pokemon_oop_explorer.data.starter_seed import DomainCatalog, build_catalog
from pokemon_oop_explorer.models.base import Inspectable
from pokemon_oop_explorer.models.pokemon import PokemonInstance, PokemonSpecies
from pokemon_oop_explorer.models.trainer import Trainer


class DomainRepository:
    """In-memory repository around static seeded data."""

    def __init__(self, project_root: Path) -> None:
        self._catalog: DomainCatalog = build_catalog(project_root=project_root)

    @property
    def families(self) -> dict[str, list[PokemonSpecies]]:
        return self._catalog.families

    @property
    def species_by_key(self) -> dict[str, PokemonSpecies]:
        return self._catalog.species_by_key

    @property
    def instances(self) -> list[PokemonInstance]:
        return self._catalog.instances

    @property
    def trainers(self) -> list[Trainer]:
        return self._catalog.trainers

    def all_inspectables(self) -> list[Inspectable]:
        objects: list[Inspectable] = list(self._catalog.species_by_key.values())
        objects.extend(self._catalog.instances)
        objects.extend(self._catalog.trainers)
        return objects
