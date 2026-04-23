from pokemon_oop_explorer.models.evolution import (
    FriendshipEvolutionRule,
    ItemEvolutionRule,
    LevelEvolutionRule,
)


def test_level_rule() -> None:
    rule = LevelEvolutionRule(
        name="Level rule", minimum_level=16, target_species_key="ivysaur"
    )
    assert not rule.is_satisfied(level=15)
    assert rule.is_satisfied(level=16)


def test_item_rule() -> None:
    rule = ItemEvolutionRule(
        name="Item rule", required_item_key="fire_stone", target_species_key="flareon"
    )
    assert not rule.is_satisfied(level=1, item_key="water_stone")
    assert rule.is_satisfied(level=1, item_key="fire_stone")


def test_friendship_rule() -> None:
    rule = FriendshipEvolutionRule(
        name="Friendship rule", minimum_friendship=220, target_species_key="espeon"
    )
    assert not rule.is_satisfied(level=20, friendship=150)
    assert rule.is_satisfied(level=20, friendship=220)
