"""Sprite loading service."""

from __future__ import annotations

from pokemon_oop_explorer.models.pokemon import PokemonInstance, PokemonSpecies
from pokemon_oop_explorer.models.trainer import Trainer


class SpriteService:
    """Loads ANSI sprites from SpriteAsset objects."""

    def load_for_species(self, species: PokemonSpecies, *, shiny: bool = False) -> str:
        if species.sprite_asset is None:
            return f"No sprite configured for {species.name}."
        return species.sprite_asset.load(shiny=shiny)

    def load_for_instance(self, instance: PokemonInstance) -> str:
        if instance.species is None:
            return "No species attached to instance."
        shiny = False
        if instance.identity is not None:
            shiny = instance.identity.shiny_report().is_shiny
        return self.load_for_species(instance.species, shiny=shiny)

    def load_for_trainer(self, trainer: Trainer) -> str:
        if trainer.sprite_asset is not None:
            return trainer.sprite_asset.load(shiny=False)
        active = trainer.active_pokemon()
        if active is not None:
            return self.load_for_instance(active)
        return f"No sprite configured for {trainer.name}."
