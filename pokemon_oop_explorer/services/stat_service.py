"""Stat and battle-related services."""

from __future__ import annotations

from pokemon_oop_explorer.models.pokemon import PokemonInstance


class StatService:
    """Application service for stat computations."""

    @staticmethod
    def compute_effective_stats(instance: PokemonInstance) -> dict[str, int]:
        return instance.effective_stats()
