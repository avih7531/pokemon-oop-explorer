"""Class-graph introspection for automatic UML rendering."""

from .class_graph import (
    ClassGraph,
    ClassGraphBuilder,
    ClassNode,
    FieldInfo,
    RelationshipEdge,
    RelationshipKind,
)
from .ascii_renderer import AsciiUmlRenderer, UmlRenderer
from .relationship_detector import (
    AggregationDetector,
    CompositionDetector,
    EdgeDetector,
    InheritanceDetector,
    default_detectors,
)

__all__ = [
    "AggregationDetector",
    "AsciiUmlRenderer",
    "ClassGraph",
    "ClassGraphBuilder",
    "ClassNode",
    "CompositionDetector",
    "EdgeDetector",
    "FieldInfo",
    "InheritanceDetector",
    "RelationshipEdge",
    "RelationshipKind",
    "UmlRenderer",
    "default_detectors",
]
