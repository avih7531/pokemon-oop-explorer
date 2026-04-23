"""Tests for the move-effect hierarchy."""

from __future__ import annotations

from pokemon_oop_explorer.models.effects import (
    DamageEffect,
    EffectContext,
    HealEffect,
    StatStageEffect,
    StatusEffect,
)
from pokemon_oop_explorer.models.enums import StatKind
from pokemon_oop_explorer.models.pokemon import PokemonInstance
from pokemon_oop_explorer.models.status import BurnStatus, PoisonStatus


def _make_instance(name: str = "Dummy", hp: int = 50) -> PokemonInstance:
    return PokemonInstance(name=name, nickname=name, level=10, current_hp=hp)


def test_damage_effect_reduces_current_hp() -> None:
    source = _make_instance("Attacker", hp=100)
    target = _make_instance("Victim", hp=100)
    effect = DamageEffect(name="Test Damage", base_damage=15)
    result = effect.apply(EffectContext(source=source, target=target))
    assert target.current_hp == 85
    assert "lost 15 HP" in result.message


def test_damage_effect_crit_doubles_damage() -> None:
    source = _make_instance("Attacker", hp=100)
    target = _make_instance("Victim", hp=100)
    effect = DamageEffect(name="Crit", base_damage=10)
    effect.apply(EffectContext(source=source, target=target, crit=True))
    assert target.current_hp == 80


def test_heal_effect_restores_self() -> None:
    source = _make_instance("Healer", hp=30)
    target = _make_instance("Other", hp=30)
    effect = HealEffect(name="Rest", heal_amount=20, target_self=True)
    effect.apply(EffectContext(source=source, target=target))
    assert source.current_hp == 50
    assert target.current_hp == 30


def test_status_effect_sets_condition() -> None:
    source = _make_instance("Caster")
    target = _make_instance("Victim")
    assert target.status is None
    effect = StatusEffect(name="Will-O-Wisp", condition_factory=BurnStatus)
    effect.apply(EffectContext(source=source, target=target))
    assert isinstance(target.status, BurnStatus)


def test_status_effect_uses_provided_factory() -> None:
    target = _make_instance("Victim")
    effect = StatusEffect(name="Toxic", condition_factory=PoisonStatus)
    effect.apply(EffectContext(source=_make_instance("A"), target=target))
    assert isinstance(target.status, PoisonStatus)


def test_stat_stage_effect_tracks_delta() -> None:
    source = _make_instance("Buffer")
    effect = StatStageEffect(
        name="Swords Dance", stat=StatKind.ATTACK, delta=2, target_self=True
    )
    effect.apply(EffectContext(source=source, target=_make_instance("Other")))
    assert source.stat_stages[StatKind.ATTACK.value] == 2


def test_burn_status_tick_damages_hp() -> None:
    instance = _make_instance("Burnt", hp=50)
    burn = BurnStatus()
    message = burn.tick(instance)
    assert instance.current_hp == 50 - burn.damage_per_turn
    assert "burn" in message.lower()
