"""ASCII / Unicode UML renderers for a :class:`ClassGraph`."""

from __future__ import annotations

from abc import ABC, abstractmethod

from rich.markup import escape as _escape_markup

from .class_graph import ClassGraph, ClassNode, RelationshipEdge, RelationshipKind


class UmlRenderer(ABC):
    """Common rendering contract for UML diagrams."""

    @abstractmethod
    def render(self, graph: ClassGraph, focus: type | None = None) -> str:
        """Render the graph; pass ``focus=None`` for the package overview."""


class AsciiUmlRenderer(UmlRenderer):
    """Unicode-box renderer tuned for a TUI panel."""

    def render(self, graph: ClassGraph, focus: type | None = None) -> str:
        if focus is None:
            return self._render_overview(graph)
        if focus not in graph.nodes:
            return f"Class {_class_name(focus)} is not in the introspected graph."
        return self._render_focus(graph, focus)

    def _render_focus(self, graph: ClassGraph, focus: type) -> str:
        node = graph.nodes[focus]
        parents = _sorted_targets(graph.outgoing(focus), RelationshipKind.INHERITS)
        children = _sorted_sources(graph.incoming(focus), RelationshipKind.INHERITS)
        compositions = [
            edge
            for edge in graph.outgoing(focus)
            if edge.kind is RelationshipKind.COMPOSES
        ]
        aggregations = [
            edge
            for edge in graph.outgoing(focus)
            if edge.kind is RelationshipKind.AGGREGATES
        ]
        references = [
            edge
            for edge in graph.outgoing(focus)
            if edge.kind is RelationshipKind.REFERENCES
        ]
        used_by = [
            edge
            for edge in graph.incoming(focus)
            if edge.kind is not RelationshipKind.INHERITS
        ]

        sections: list[str] = []
        sections.append(_render_legend())
        sections.append("")
        sections.append(f"[b #e279a1]UML: {node.name}[/]")
        sections.append(f"[#88C0D0]module[/] {node.module}")
        sections.append("[#b4b4b4]Tip: click any class name below to zoom into it.[/]")
        sections.append("")
        sections.append(_render_box(node))

        if parents:
            sections.append("")
            sections.append("[b #88C0D0]Inherits[/]")
            for parent in parents:
                sections.append(f"  [#88C0D0]--|>[/] {_class_link(parent)}")

        if children:
            sections.append("")
            sections.append("[b #a97ea1]Subclasses[/]")
            for child in children:
                sections.append(f"  [#a97ea1]<|--[/] {_class_link(child)}")

        if compositions:
            sections.append("")
            sections.append("[b #97b67c]Composes[/]")
            for edge in compositions:
                sections.append(
                    f"  [#97b67c]*--[/]  {_class_link(edge.target)}  ({edge.label})"
                )

        if aggregations:
            sections.append("")
            sections.append("[b #e7c173]Aggregates[/]")
            for edge in aggregations:
                sections.append(
                    f"  [#e7c173]o--[/]  {_class_link(edge.target)}  ({edge.label})"
                )

        if references:
            sections.append("")
            sections.append("[b #b4b4b4]References[/]")
            for edge in references:
                sections.append(
                    f"  [#b4b4b4]-->[/]  {_class_link(edge.target)}  ({edge.label})"
                )

        if used_by:
            sections.append("")
            sections.append("[b #5E81AC]Used By[/]")
            for edge in used_by:
                glyph = _incoming_glyph(edge.kind)
                sections.append(
                    f"  [#5E81AC]{glyph}[/] {_class_link(edge.source)}  ({edge.label})"
                )

        return "\n".join(sections)

    def _render_overview(self, graph: ClassGraph) -> str:
        modules: dict[str, list[ClassNode]] = {}
        for node in graph.nodes.values():
            modules.setdefault(node.module, []).append(node)
        lines: list[str] = [
            _render_legend(),
            "",
            "[b #e279a1]Domain Class Overview[/]",
            "[#88C0D0]Click any class name to zoom into its UML; "
            "or select a node in the tree.[/]",
            "",
        ]
        for module in sorted(modules):
            nodes = sorted(modules[module], key=lambda item: item.name)
            lines.append(f"[b #88C0D0]{module}[/]")
            for node in nodes:
                parents = _sorted_targets(
                    graph.outgoing(node.cls), RelationshipKind.INHERITS
                )
                parent_suffix = (
                    " [#88C0D0]--|>[/] " + ", ".join(_class_link(p) for p in parents)
                    if parents
                    else ""
                )
                lines.append(f"  {_class_link(node.cls)}{parent_suffix}")
                for edge in graph.outgoing(node.cls):
                    if edge.kind is RelationshipKind.INHERITS:
                        continue
                    glyph = edge.kind.glyph
                    color = _glyph_color(edge.kind)
                    lines.append(
                        f"    [{color}]{glyph}[/] {_class_link(edge.target)}  ({edge.label})"
                    )
            lines.append("")
        return "\n".join(lines)


def _render_box(node: ClassNode) -> str:
    header = node.name
    field_rows = [f"{field.name}: {field.annotation.strip()}" for field in node.fields]
    method_rows = [f"{name}()" for name in node.methods]
    inherited_rows = list(node.inherited_methods)

    width = max(
        [len(header)]
        + [len(row) for row in field_rows]
        + [len(row) for row in method_rows]
        + [len(row) for row in inherited_rows]
        + [20]
    )
    inner_width = width + 2

    top = "\u250c" + "\u2500" * inner_width + "\u2510"
    mid = "\u251c" + "\u2500" * inner_width + "\u2524"
    bot = "\u2514" + "\u2500" * inner_width + "\u2518"

    def pad(row: str) -> str:
        # Rich would otherwise try to parse brackets in e.g. ``list[MoveSlot]``
        # or ``[from PokemonInstance]`` as markup tags, eating them and
        # mangling the box alignment. Escape at render time but pad from the
        # visible (unescaped) length so borders line up.
        visible_len = len(row)
        padding = " " * max(0, width - visible_len)
        return "\u2502 " + _escape_markup(row) + padding + " \u2502"

    rows: list[str] = [top, pad(header), mid]
    if field_rows:
        rows.extend(pad(row) for row in field_rows)
    else:
        rows.append(pad("(no fields)"))
    rows.append(mid)
    if method_rows:
        rows.extend(pad(row) for row in method_rows)
    else:
        rows.append(pad("(no own methods)"))
    if inherited_rows:
        rows.append(mid)
        rows.append(pad("inherited:"))
        rows.extend(pad(row) for row in inherited_rows)
    rows.append(bot)
    return "\n".join(rows)


def _render_legend() -> str:
    return (
        "[b #b4b4b4]Legend[/]  "
        "[#88C0D0]--|>[/] inherits  "
        "[#a97ea1]<|--[/] subclass-of  "
        "[#97b67c]*--[/] composes  "
        "[#e7c173]o--[/] aggregates  "
        "[#b4b4b4]-->[/] references"
    )


def _sorted_targets(
    edges: list[RelationshipEdge], kind: RelationshipKind
) -> list[type]:
    return sorted(
        {edge.target for edge in edges if edge.kind is kind},
        key=_class_name,
    )


def _sorted_sources(
    edges: list[RelationshipEdge], kind: RelationshipKind
) -> list[type]:
    return sorted(
        {edge.source for edge in edges if edge.kind is kind},
        key=_class_name,
    )


def _incoming_glyph(kind: RelationshipKind) -> str:
    if kind is RelationshipKind.COMPOSES:
        return "--*"
    if kind is RelationshipKind.AGGREGATES:
        return "--o"
    if kind is RelationshipKind.REFERENCES:
        return "<--"
    return kind.glyph


def _class_name(cls: type) -> str:
    return cls.__name__


def _class_link(cls: type) -> str:
    """Render a class name as a Textual markup action link for click-to-zoom."""
    name = cls.__name__
    return f"[@click=app.zoom_class('{name}')]{name}[/]"


def _glyph_color(kind: RelationshipKind) -> str:
    return {
        RelationshipKind.INHERITS: "#88C0D0",
        RelationshipKind.COMPOSES: "#97b67c",
        RelationshipKind.AGGREGATES: "#e7c173",
        RelationshipKind.REFERENCES: "#b4b4b4",
    }[kind]
