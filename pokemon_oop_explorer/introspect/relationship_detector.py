"""Strategy classes that classify edges between domain classes.

Each detector is a pluggable ``EdgeDetector`` the ``ClassGraphBuilder`` calls
on every collected class. Adding an edge kind is a matter of writing one more
detector, keeping classification polymorphic rather than an ``if`` chain.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import fields, is_dataclass
from typing import Iterable

from .class_graph import RelationshipEdge, RelationshipKind

_CONTAINER_NAMES = {
    "list",
    "set",
    "tuple",
    "dict",
    "frozenset",
    "Sequence",
    "Iterable",
    "Mapping",
    "Iterator",
    "List",
    "Set",
    "Tuple",
    "Dict",
    "FrozenSet",
}
_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z_0-9]*")


class EdgeDetector(ABC):
    """Polymorphic edge classifier."""

    @abstractmethod
    def detect(self, cls: type, universe: set[type]) -> Iterable[RelationshipEdge]:
        """Yield zero or more edges originating at ``cls``."""


class InheritanceDetector(EdgeDetector):
    """Emits ``INHERITS`` edges for every non-``object`` base class."""

    def detect(self, cls: type, universe: set[type]) -> Iterable[RelationshipEdge]:
        for base in cls.__bases__:
            if base is object:
                continue
            if base in universe:
                yield RelationshipEdge(
                    source=cls,
                    target=base,
                    kind=RelationshipKind.INHERITS,
                    label="extends",
                )


class _DataclassFieldDetector(EdgeDetector, ABC):
    """Shared traversal over dataclass field annotations."""

    def detect(self, cls: type, universe: set[type]) -> Iterable[RelationshipEdge]:
        if not is_dataclass(cls):
            return
        universe_by_name = {candidate.__name__: candidate for candidate in universe}
        for field_def in fields(cls):
            annotation = _as_string(field_def.type)
            for target, inside_container in _iter_type_refs(
                annotation, universe_by_name
            ):
                if target is cls:
                    continue
                yield from self._emit(cls, field_def.name, target, inside_container)

    @abstractmethod
    def _emit(
        self,
        cls: type,
        attr_name: str,
        target: type,
        inside_container: bool,
    ) -> Iterable[RelationshipEdge]:
        """Decide whether this detector owns this particular reference."""


class CompositionDetector(_DataclassFieldDetector):
    """Direct type references (including ``Optional[T]``) become composition edges."""

    def _emit(
        self,
        cls: type,
        attr_name: str,
        target: type,
        inside_container: bool,
    ) -> Iterable[RelationshipEdge]:
        if inside_container:
            return
        yield RelationshipEdge(
            source=cls,
            target=target,
            kind=RelationshipKind.COMPOSES,
            label=attr_name,
        )


class AggregationDetector(_DataclassFieldDetector):
    """Container-wrapped references become aggregation edges."""

    def _emit(
        self,
        cls: type,
        attr_name: str,
        target: type,
        inside_container: bool,
    ) -> Iterable[RelationshipEdge]:
        if not inside_container:
            return
        yield RelationshipEdge(
            source=cls,
            target=target,
            kind=RelationshipKind.AGGREGATES,
            label=attr_name,
        )


def default_detectors() -> list[EdgeDetector]:
    """The standard set used by the TUI."""

    return [
        InheritanceDetector(),
        CompositionDetector(),
        AggregationDetector(),
    ]


def _as_string(annotation: object) -> str:
    if isinstance(annotation, str):
        return annotation
    if hasattr(annotation, "__name__"):
        return str(annotation.__name__)
    return str(annotation)


def _iter_type_refs(
    annotation: str,
    universe_by_name: dict[str, type],
) -> Iterable[tuple[type, bool]]:
    """Yield ``(cls, inside_container)`` for every known class in ``annotation``.

    The traversal uses simple bracket accounting to detect whether each name
    appears within a known container (``list[...]``, ``dict[..., ...]`` etc.).
    """

    container_ranges = _collect_container_ranges(annotation)

    def _inside_container(position: int) -> bool:
        return any(start < position < end for start, end in container_ranges)

    seen: set[tuple[str, bool]] = set()
    for match in _IDENT_RE.finditer(annotation):
        name = match.group(0)
        target = universe_by_name.get(name)
        if target is None:
            continue
        inside = _inside_container(match.start())
        key = (name, inside)
        if key in seen:
            continue
        seen.add(key)
        yield target, inside


def _collect_container_ranges(annotation: str) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    length = len(annotation)
    for match in _IDENT_RE.finditer(annotation):
        name = match.group(0)
        if name not in _CONTAINER_NAMES:
            continue
        cursor = match.end()
        while cursor < length and annotation[cursor] == " ":
            cursor += 1
        if cursor >= length or annotation[cursor] != "[":
            continue
        open_idx = cursor
        depth = 1
        idx = open_idx + 1
        while idx < length and depth > 0:
            if annotation[idx] == "[":
                depth += 1
            elif annotation[idx] == "]":
                depth -= 1
            idx += 1
        ranges.append((open_idx, idx))
    return ranges
