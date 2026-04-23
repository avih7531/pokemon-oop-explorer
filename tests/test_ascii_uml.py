"""Tests for the ASCII UML renderer."""

from __future__ import annotations

import pokemon_oop_explorer.models as models_pkg
from pokemon_oop_explorer.introspect import AsciiUmlRenderer, ClassGraphBuilder
from pokemon_oop_explorer.models.pokemon import PokemonSpecies
from pokemon_oop_explorer.models.trainer import Trainer


def test_focused_render_includes_class_name_and_inheritance_glyph() -> None:
    graph = ClassGraphBuilder(models_pkg).build()
    rendered = AsciiUmlRenderer().render(graph, focus=PokemonSpecies)
    assert "PokemonSpecies" in rendered
    assert "AbstractDomainObject" in rendered
    assert "--|>" in rendered


def test_focused_render_contains_composition_glyph() -> None:
    graph = ClassGraphBuilder(models_pkg).build()
    rendered = AsciiUmlRenderer().render(graph, focus=PokemonSpecies)
    assert "*--" in rendered, "PokemonSpecies should show a composition edge in UML"
    assert "o--" in rendered, (
        "PokemonSpecies aggregates should show an aggregation edge"
    )


def test_trainer_render_shows_party_aggregation() -> None:
    graph = ClassGraphBuilder(models_pkg).build()
    rendered = AsciiUmlRenderer().render(graph, focus=Trainer)
    assert "Trainer" in rendered
    assert "PokemonInstance" in rendered
    assert "o--" in rendered


def test_overview_render_lists_modules() -> None:
    graph = ClassGraphBuilder(models_pkg).build()
    rendered = AsciiUmlRenderer().render(graph, focus=None)
    assert "Domain Class Overview" in rendered
    assert "pokemon_oop_explorer.models.pokemon" in rendered
