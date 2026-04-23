"""Formatting/presentation helpers for inspector data."""

from __future__ import annotations

import inspect
import json
from dataclasses import fields, is_dataclass

from pokemon_oop_explorer.introspect import (
    AsciiUmlRenderer,
    ClassGraph,
    RelationshipKind,
    UmlRenderer,
)
from pokemon_oop_explorer.models.base import Inspectable
from pokemon_oop_explorer.models.pokemon import PokemonInstance, PokemonSpecies
from pokemon_oop_explorer.models.trainer import Trainer


def _class_link(name: str) -> str:
    """Render a class name as a Textual [@click] action that triggers UML zoom."""
    return f"[@click=app.zoom_class('{name}')]{name}[/]"


def _linked_join(names: list[str], separator: str = ", ") -> str:
    if not names:
        return "None"
    return separator.join(_class_link(name) for name in names)


def inheritance_chain(obj: object) -> str:
    classes = [
        cls.__name__
        for cls in inspect.getmro(obj.__class__)
        if cls.__name__ != "object"
    ]
    return " -> ".join(classes)


def inheritance_chain_markup(obj: object) -> str:
    classes = [
        cls.__name__
        for cls in inspect.getmro(obj.__class__)
        if cls.__name__ != "object"
    ]
    return " -> ".join(_class_link(name) for name in classes)


def constructor_signature(obj: object) -> str:
    signature = inspect.signature(obj.__class__)
    compact_parts: list[str] = []
    for parameter in signature.parameters.values():
        if parameter.name == "self":
            continue
        compact_parts.append(parameter.name)
    preview = ", ".join(compact_parts[:8])
    suffix = " ..." if len(compact_parts) > 8 else ""
    return f"{obj.__class__.__name__}({preview}{suffix})"


def constructor_signature_markup(obj: object) -> str:
    signature = inspect.signature(obj.__class__)
    compact_parts: list[str] = []
    for parameter in signature.parameters.values():
        if parameter.name == "self":
            continue
        compact_parts.append(parameter.name)
    preview = ", ".join(compact_parts[:8])
    suffix = " ..." if len(compact_parts) > 8 else ""
    class_link = _class_link(obj.__class__.__name__)
    return f"{class_link}({preview}{suffix})"


def subclasses_text(cls: type[object]) -> str:
    names = sorted(sub.__name__ for sub in cls.__subclasses__())
    return _linked_join(names)


def descendant_classes(cls: type[object]) -> list[type[object]]:
    descendants: list[type[object]] = []
    for sub in cls.__subclasses__():
        descendants.append(sub)
        descendants.extend(descendant_classes(sub))
    return descendants


def hierarchy_anchor_class(obj: Inspectable) -> type[object]:
    if isinstance(obj, PokemonSpecies):
        return PokemonSpecies
    if isinstance(obj, PokemonInstance):
        return PokemonInstance
    if isinstance(obj, Trainer):
        return Trainer
    return obj.__class__


def sibling_classes_text(cls: type[object]) -> str:
    if not cls.__bases__:
        return "None"
    base = cls.__bases__[0]
    names = sorted(sub.__name__ for sub in base.__subclasses__() if sub is not cls)
    return _linked_join(names)


def dataclass_fields(obj: object) -> list[str]:
    if not is_dataclass(obj):
        return []
    return [field.name for field in fields(obj)]


def detail_text(obj: Inspectable) -> str:
    payload = obj.inspect_payload()
    header_name = payload.get("display_name") or payload.get("name", "Unknown")
    header = [
        f"[#e279a1][b]{header_name}[/b][/]",
        f"[#88C0D0]Class[/]: {_class_link(obj.__class__.__name__)}",
        f"[#88C0D0]Chain[/]: {inheritance_chain_markup(obj)}",
        f"[#a97ea1]Ctor[/]: {constructor_signature_markup(obj)}",
    ]
    if isinstance(obj, PokemonSpecies):
        ability_names = (
            ", ".join(a["name"] for a in payload.get("abilities", [])) or "None"
        )
        learnset_levels = sorted(
            int(level) for level in payload.get("learnset", {}).keys()
        )
        header.extend(
            [
                f"[#e7c173]Dex[/]: #{payload.get('dex_number')} (Gen {payload.get('generation')})",
                f"[#97b67c]Types[/]: {', '.join(payload.get('types', []))}",
                f"[#e7c173]Abilities[/]: {ability_names}",
                f"[#97b67c]Learnset[/]: {len(learnset_levels)} levels",
                f"[#88C0D0]Evolves[/]: {'Yes' if payload.get('can_evolve') else 'No'}",
            ]
        )
    if isinstance(obj, PokemonInstance):
        identity = payload.get("identity", {})
        header.extend(
            [
                f"[#e7c173]Species[/]: {payload.get('species')}  [#e7c173]Lv[/]: {payload.get('level')}",
                f"[#97b67c]Ability[/]: {payload.get('chosen_ability')}  [#97b67c]Item[/]: {payload.get('held_item')}",
                f"[#97b67c]Nature[/]: {payload.get('nature')}  [#b74e58]Status[/]: {payload.get('status')}",
                f"[#a97ea1]Trainer[/]: {payload.get('owner')}",
                f"[#88C0D0]Shiny[/]: {'Yes' if identity.get('is_shiny') else 'No'} (SV={identity.get('shiny_value')})",
            ]
        )
    if isinstance(obj, Trainer):
        header.extend(
            [
                f"[#e7c173]Trainer ID[/]: {payload.get('trainer_id')} / {payload.get('secret_id')}",
                f"[#97b67c]Badges[/]: {payload.get('badges')}",
                f"[#88C0D0]Home[/]: {payload.get('home_town')}",
                f"[#a97ea1]Party[/]: {payload.get('party_size')}",
            ]
        )
    return "\n".join(header)


def relationship_text(obj: Inspectable, graph: ClassGraph | None = None) -> str:
    """Render the relationship panel using graph edges when available.

    Falls back to pure ``inspect``-driven data if no graph is supplied, which
    is useful for tests that don't want to build the package graph.
    """

    cls = obj.__class__
    anchor = hierarchy_anchor_class(obj)
    anchor_descendants = sorted(desc.__name__ for desc in descendant_classes(anchor))
    base_names = [base.__name__ for base in cls.__bases__ if base.__name__ != "object"]
    lines = [
        f"[#88C0D0][b]Class Hierarchy[/b][/]\n{inheritance_chain_markup(obj)}",
        f"\n[#88C0D0][b]Domain Anchor[/b][/]\n{_class_link(anchor.__name__)}",
        f"\n[#a97ea1][b]Extends / Inherits[/b][/]\n{_linked_join(base_names)}",
        f"\n[#a97ea1][b]Direct Subclasses (Current)[/b][/]\n{subclasses_text(cls)}",
        f"\n[#a97ea1][b]Sibling Classes[/b][/]\n{sibling_classes_text(cls)}",
        f"\n[#a97ea1][b]All Descendants ({_class_link(anchor.__name__)})[/b][/]\n"
        + _linked_join(anchor_descendants),
        "\n[#e7c173][b]Constructor Fields[/b][/]\n" + ", ".join(dataclass_fields(obj)),
    ]

    if graph is not None and cls in graph.nodes:
        composes = _edge_summary(graph, cls, RelationshipKind.COMPOSES)
        aggregates = _edge_summary(graph, cls, RelationshipKind.AGGREGATES)
        references = _edge_summary(graph, cls, RelationshipKind.REFERENCES)
        used_by = _incoming_summary(graph, cls)

        lines.append(
            "\n[#97b67c][b]Composes (introspected)[/b][/]\n" + (composes or "None")
        )
        lines.append(
            "\n[#e7c173][b]Aggregates (introspected)[/b][/]\n" + (aggregates or "None")
        )
        if references:
            lines.append("\n[#b4b4b4][b]References[/b][/]\n" + references)
        if used_by:
            lines.append("\n[#5E81AC][b]Used By[/b][/]\n" + used_by)

    return "\n".join(lines)


def _edge_summary(graph: ClassGraph, cls: type, kind: RelationshipKind) -> str:
    entries: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for edge in graph.outgoing(cls):
        if edge.kind is not kind:
            continue
        key = (edge.target.__name__, edge.label)
        if key in seen:
            continue
        seen.add(key)
        entries.append(key)
    entries.sort()
    return ", ".join(f"{_class_link(name)} ({label})" for name, label in entries)


def _incoming_summary(graph: ClassGraph, cls: type) -> str:
    entries: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for edge in graph.incoming(cls):
        if edge.kind is RelationshipKind.INHERITS:
            continue
        key = (edge.source.__name__, edge.label)
        if key in seen:
            continue
        seen.add(key)
        entries.append(key)
    entries.sort()
    return ", ".join(f"{_class_link(name)}.{label}" for name, label in entries)


def uml_text(
    obj: Inspectable | None,
    graph: ClassGraph,
    renderer: UmlRenderer | None = None,
) -> str:
    """Render the UML tab contents for the currently selected object."""

    render = renderer or AsciiUmlRenderer()
    focus = type(obj) if obj is not None else None
    return render.render(graph, focus=focus)


def tab_sections(obj: Inspectable, graph: ClassGraph | None = None) -> dict[str, str]:
    payload = obj.inspect_payload()
    if isinstance(obj, PokemonSpecies):
        moves = {
            "learnset_by_level": payload.get("learnset", {}),
            "possible_abilities": payload.get("abilities", []),
        }
        stats = payload.get("base_stats", {})
        identity = {"scope": "Species-level object", "identity": "Not applicable"}
        evolution = {
            "rules": payload.get("evolution_rules", []),
            "line": payload.get("evolution_line", []),
        }
    elif isinstance(obj, PokemonInstance):
        moves = {
            "equipped_moves": payload.get("moves", []),
            "chosen_ability": payload.get("chosen_ability"),
            "status": payload.get("status"),
            "nature": payload.get("nature"),
        }
        stats = payload.get("effective_stats", {})
        identity = payload.get("identity", {})
        evolution = {
            "can_evolve_now": payload.get("can_evolve_now"),
            "species": payload.get("species"),
            "species_evolution_rules": (
                [rule.short_description() for rule in obj.species.evolution_rules]
                if obj.species
                else []
            ),
        }
    elif isinstance(obj, Trainer):
        moves = {
            "party": payload.get("party", []),
        }
        stats = {
            "badges": payload.get("badges"),
            "party_size": payload.get("party_size"),
        }
        identity = {
            "trainer_id": payload.get("trainer_id"),
            "secret_id": payload.get("secret_id"),
            "display_name": payload.get("display_name"),
            "home_town": payload.get("home_town"),
        }
        evolution = {"scope": "Trainer aggregate", "evolution_rules": "Not applicable"}
    else:
        moves = (
            payload.get("moves")
            or payload.get("learnset")
            or payload.get("evolution_rules")
        )
        stats = payload.get("effective_stats") or payload.get("base_stats")
        identity = payload.get("identity", "N/A")
        evolution = payload.get("evolution_rules", "N/A")

    sections = {
        "moves": json.dumps(moves, indent=2, default=str),
        "stats": json.dumps(stats, indent=2, default=str),
        "identity": json.dumps(identity, indent=2, default=str),
        "evolution": json.dumps(evolution, indent=2, default=str),
    }
    if graph is not None:
        sections["uml"] = uml_text(obj, graph)
    return sections
