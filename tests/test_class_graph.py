"""Tests for the introspection class-graph builder."""

from __future__ import annotations

import pokemon_oop_explorer.models as models_pkg
from pokemon_oop_explorer.introspect import (
    AggregationDetector,
    ClassGraph,
    ClassGraphBuilder,
    CompositionDetector,
    InheritanceDetector,
    RelationshipKind,
)
from pokemon_oop_explorer.models.abilities import Ability
from pokemon_oop_explorer.models.base import AbstractDomainObject
from pokemon_oop_explorer.models.evolution import EvolutionRule
from pokemon_oop_explorer.models.pokemon import PokemonInstance, PokemonSpecies
from pokemon_oop_explorer.models.trainer import Trainer
from pokemon_oop_explorer.models.value_objects import StatBlock


def _build_graph() -> ClassGraph:
    return ClassGraphBuilder(models_pkg).build()


def test_graph_contains_core_domain_classes() -> None:
    graph = _build_graph()
    assert PokemonSpecies in graph.nodes
    assert PokemonInstance in graph.nodes
    assert Trainer in graph.nodes
    assert AbstractDomainObject in graph.nodes


def test_inheritance_edges_detected() -> None:
    graph = _build_graph()
    edge_pairs = {
        (e.source, e.target) for e in graph.edges if e.kind is RelationshipKind.INHERITS
    }
    assert (PokemonSpecies, AbstractDomainObject) in edge_pairs
    assert (PokemonInstance, AbstractDomainObject) in edge_pairs
    assert (Trainer, AbstractDomainObject) in edge_pairs


def test_composition_edge_on_statblock() -> None:
    graph = _build_graph()
    composes = [
        edge
        for edge in graph.outgoing(PokemonSpecies)
        if edge.kind is RelationshipKind.COMPOSES and edge.target is StatBlock
    ]
    assert composes, (
        "PokemonSpecies.base_stats should be a composition edge to StatBlock"
    )
    assert composes[0].label == "base_stats"


def test_aggregation_edges_on_list_fields() -> None:
    graph = _build_graph()
    aggregates = {
        edge.target
        for edge in graph.outgoing(PokemonSpecies)
        if edge.kind is RelationshipKind.AGGREGATES
    }
    assert Ability in aggregates, (
        "possible_abilities: list[Ability] should aggregate Ability"
    )
    assert EvolutionRule in aggregates, (
        "evolution_rules: list[EvolutionRule] should aggregate EvolutionRule"
    )


def test_trainer_aggregates_instances() -> None:
    graph = _build_graph()
    aggregates = {
        edge.target
        for edge in graph.outgoing(Trainer)
        if edge.kind is RelationshipKind.AGGREGATES
    }
    assert PokemonInstance in aggregates


def test_detector_strategies_are_independent() -> None:
    """Inheritance detector alone produces only INHERITS edges."""

    graph = ClassGraphBuilder(models_pkg, detectors=[InheritanceDetector()]).build()
    assert graph.edges
    assert all(edge.kind is RelationshipKind.INHERITS for edge in graph.edges)


def test_composition_and_aggregation_are_disjoint() -> None:
    graph = ClassGraphBuilder(
        models_pkg,
        detectors=[CompositionDetector(), AggregationDetector()],
    ).build()
    for edge in graph.edges:
        # No edge is both composes and aggregates (different detectors emit different kinds).
        assert edge.kind in {RelationshipKind.COMPOSES, RelationshipKind.AGGREGATES}
