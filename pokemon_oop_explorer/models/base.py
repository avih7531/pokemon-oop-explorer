"""Base abstractions for entity inspection and domain behavior."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol
from uuid import uuid4

if TYPE_CHECKING:
    from .visitor import DomainVisitor


@dataclass(slots=True)
class Entity(ABC):
    """Base entity with a unique identity."""

    entity_id: str = field(default_factory=lambda: str(uuid4()))


class Inspectable(ABC):
    """Interface for objects that can be rendered in the inspector."""

    @abstractmethod
    def inspect_payload(self) -> dict[str, Any]:
        """Return structured inspection data."""


@dataclass(slots=True)
class AbstractDomainObject(Entity, Inspectable, ABC):
    """Base domain object carrying name and summary metadata."""

    name: str = ""
    description: str = ""

    def inspect_payload(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "class_name": self.__class__.__name__,
        }

    def accept(self, visitor: "DomainVisitor") -> None:
        """Double-dispatch entry point for :class:`DomainVisitor`.

        Default dispatch routes to ``visit_other``; species, instances, and
        trainers override this with their specific visitor method.
        """
        visitor.visit_other(self)


class Evolvable(Protocol):
    """Protocol-style behavior for species or instances that can evolve."""

    def can_evolve(self) -> bool:
        """Whether object can evolve under any known rule."""
