"""Shared enums for the domain."""

from __future__ import annotations

from enum import Enum, IntEnum


class Generation(IntEnum):
    """Pokemon generation index."""

    GEN_1 = 1
    GEN_2 = 2
    GEN_3 = 3


class ElementType(str, Enum):
    """Element typing."""

    NORMAL = "Normal"
    GRASS = "Grass"
    FIRE = "Fire"
    WATER = "Water"
    ELECTRIC = "Electric"
    ICE = "Ice"
    FIGHTING = "Fighting"
    POISON = "Poison"
    GROUND = "Ground"
    FLYING = "Flying"
    PSYCHIC = "Psychic"
    BUG = "Bug"
    ROCK = "Rock"
    GHOST = "Ghost"
    DRAGON = "Dragon"
    DARK = "Dark"
    STEEL = "Steel"


class MoveCategory(str, Enum):
    """Move category."""

    PHYSICAL = "Physical"
    SPECIAL = "Special"
    STATUS = "Status"


class ItemCategory(str, Enum):
    """Item category."""

    HELD = "Held"
    CONSUMABLE = "Consumable"
    EVOLUTION = "Evolution"


class StatKind(str, Enum):
    """Kinds of battle stats."""

    HP = "HP"
    ATTACK = "Attack"
    DEFENSE = "Defense"
    SPECIAL_ATTACK = "Sp. Attack"
    SPECIAL_DEFENSE = "Sp. Defense"
    SPEED = "Speed"
