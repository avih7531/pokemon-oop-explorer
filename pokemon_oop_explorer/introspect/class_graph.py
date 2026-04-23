"""Class graph data structures and builder.

The graph is populated by one or more ``EdgeDetector`` strategies, so edge
classification is polymorphic rather than a hard-coded ``if`` chain.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
from types import ModuleType
from typing import TYPE_CHECKING, Iterable, Iterator

if TYPE_CHECKING:
    from .relationship_detector import EdgeDetector


class RelationshipKind(Enum):
    """Classes of edges the graph can carry."""

    INHERITS = "inherits"
    COMPOSES = "composes"
    AGGREGATES = "aggregates"
    REFERENCES = "references"

    @property
    def glyph(self) -> str:
        return {
            RelationshipKind.INHERITS: "--|>",
            RelationshipKind.COMPOSES: "*--",
            RelationshipKind.AGGREGATES: "o--",
            RelationshipKind.REFERENCES: "-->",
        }[self]


@dataclass(frozen=True, slots=True)
class FieldInfo:
    """Rendered dataclass field for the UML middle compartment."""

    name: str
    annotation: str


@dataclass(slots=True)
class ClassNode:
    """A vertex in the class graph."""

    cls: type
    fields: list[FieldInfo] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)
    inherited_methods: list[str] = field(default_factory=list)

    @property
    def name(self) -> str:
        return self.cls.__name__

    @property
    def module(self) -> str:
        return self.cls.__module__


@dataclass(frozen=True, slots=True)
class RelationshipEdge:
    """A directed typed edge between two class nodes."""

    source: type
    target: type
    kind: RelationshipKind
    label: str = ""


@dataclass(slots=True)
class ClassGraph:
    """Container for nodes and edges with simple traversal helpers."""

    nodes: dict[type, ClassNode] = field(default_factory=dict)
    edges: list[RelationshipEdge] = field(default_factory=list)

    def add_node(self, node: ClassNode) -> None:
        self.nodes[node.cls] = node

    def add_edge(self, edge: RelationshipEdge) -> None:
        if edge.source is edge.target:
            return
        if edge not in self.edges:
            self.edges.append(edge)

    def outgoing(self, cls: type) -> list[RelationshipEdge]:
        return [edge for edge in self.edges if edge.source is cls]

    def incoming(self, cls: type) -> list[RelationshipEdge]:
        return [edge for edge in self.edges if edge.target is cls]

    def neighbors(self, cls: type, depth: int = 1) -> set[type]:
        seen: set[type] = {cls}
        frontier: set[type] = {cls}
        for _ in range(max(depth, 0)):
            next_frontier: set[type] = set()
            for edge in self.edges:
                if edge.source in frontier and edge.target not in seen:
                    next_frontier.add(edge.target)
                if edge.target in frontier and edge.source not in seen:
                    next_frontier.add(edge.source)
            if not next_frontier:
                break
            seen.update(next_frontier)
            frontier = next_frontier
        return seen

    def classes(self) -> list[type]:
        return list(self.nodes.keys())


class ClassGraphBuilder:
    """Walks a Python package and assembles a ``ClassGraph``."""

    def __init__(
        self,
        root_package: str | ModuleType,
        detectors: "list[EdgeDetector] | None" = None,
    ) -> None:
        from .relationship_detector import default_detectors

        self._root_package = root_package
        self._detectors = detectors if detectors is not None else default_detectors()

    def build(self) -> ClassGraph:
        root_module = self._resolve_module()
        universe = self._collect_classes(root_module)
        graph = ClassGraph()
        for cls in universe:
            graph.add_node(_build_node(cls))
        for cls in universe:
            for detector in self._detectors:
                for edge in detector.detect(cls, universe):
                    graph.add_edge(edge)
        return graph

    def _resolve_module(self) -> ModuleType:
        if isinstance(self._root_package, ModuleType):
            return self._root_package
        return importlib.import_module(self._root_package)

    def _collect_classes(self, root_module: ModuleType) -> set[type]:
        universe: set[type] = set()
        for module in _iter_submodules(root_module):
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if not obj.__module__.startswith(root_module.__name__):
                    continue
                universe.add(obj)
                for nested in _iter_nested_classes(obj):
                    universe.add(nested)
        return universe


def _iter_submodules(root: ModuleType) -> Iterator[ModuleType]:
    yield root
    root_path = getattr(root, "__path__", None)
    if root_path is None:
        return
    for info in pkgutil.walk_packages(root_path, root.__name__ + "."):
        try:
            yield importlib.import_module(info.name)
        except Exception:
            continue


def _iter_nested_classes(cls: type) -> Iterable[type]:
    for _, member in inspect.getmembers(cls, inspect.isclass):
        if member is cls:
            continue
        if member.__qualname__.startswith(cls.__qualname__ + "."):
            yield member


def _build_node(cls: type) -> ClassNode:
    field_infos: list[FieldInfo] = []
    if is_dataclass(cls):
        for field_def in fields(cls):
            annotation = _annotation_str(field_def.type)
            field_infos.append(FieldInfo(name=field_def.name, annotation=annotation))

    own_methods: list[str] = []
    inherited_methods: list[str] = []
    domain_owners = {
        ancestor.__name__ for ancestor in cls.__mro__ if ancestor is not object
    }
    for name, member in inspect.getmembers(cls, inspect.isfunction):
        if name.startswith("_"):
            continue
        qualname = getattr(member, "__qualname__", "")
        owner_name = qualname.split(".", 1)[0] if "." in qualname else ""
        if owner_name == cls.__name__:
            own_methods.append(name)
        elif owner_name in domain_owners:
            inherited_methods.append(f"{name}()  [from {owner_name}]")

    return ClassNode(
        cls=cls,
        fields=field_infos,
        methods=sorted(own_methods),
        inherited_methods=sorted(inherited_methods),
    )


def _annotation_str(annotation: object) -> str:
    if isinstance(annotation, str):
        return annotation
    if hasattr(annotation, "__name__"):
        return str(annotation.__name__)
    return str(annotation).replace("typing.", "")
