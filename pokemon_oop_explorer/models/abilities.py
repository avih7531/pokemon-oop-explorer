"""Ability hierarchy."""

from __future__ import annotations

from dataclasses import dataclass

from .base import AbstractDomainObject


@dataclass(slots=True)
class Ability(AbstractDomainObject):
    effect_summary: str = ""


@dataclass(slots=True)
class PassiveAbility(Ability):
    pass


@dataclass(slots=True)
class TriggeredAbility(Ability):
    trigger_condition: str = ""
