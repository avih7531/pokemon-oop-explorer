"""Tests for the Trainer aggregate and related domain wiring."""

from __future__ import annotations

from pathlib import Path

from pokemon_oop_explorer.models.pokemon import PokemonInstance
from pokemon_oop_explorer.models.trainer import Trainer, TrainerIdentity
from pokemon_oop_explorer.models.visitor import ClassUsageVisitor, SummaryVisitor
from pokemon_oop_explorer.services.repository import DomainRepository


def test_trainer_add_and_remove_updates_owner() -> None:
    trainer = Trainer(
        name="Tester",
        identity=TrainerIdentity(trainer_id=1, secret_id=2, display_name="Tester"),
    )
    pikachu = PokemonInstance(name="Pikachu", level=10)
    assert pikachu.owner is None

    trainer.add_to_party(pikachu)
    assert pikachu.owner is trainer
    assert trainer.party_size == 1
    assert trainer.active_pokemon() is pikachu

    trainer.remove_from_party(pikachu)
    assert pikachu.owner is None
    assert trainer.party_size == 0


def test_seeded_repository_has_trainers_with_owners() -> None:
    repo = DomainRepository(project_root=Path.cwd())
    assert len(repo.trainers) >= 1
    for trainer in repo.trainers:
        for instance in trainer.party:
            assert instance.owner is trainer


def test_class_usage_visitor_walks_trainer_graph() -> None:
    repo = DomainRepository(project_root=Path.cwd())
    visitor = ClassUsageVisitor()
    for trainer in repo.trainers:
        trainer.accept(visitor)
    seen_names = {cls.__name__ for cls in visitor.seen_classes}
    assert "Trainer" in seen_names
    assert (
        any(name.endswith("Pokemon") for name in seen_names)
        or "PokemonInstance" in seen_names
    )


def test_summary_visitor_counts_objects() -> None:
    repo = DomainRepository(project_root=Path.cwd())
    visitor = SummaryVisitor()
    for trainer in repo.trainers:
        trainer.accept(visitor)
    for instance in repo.instances:
        instance.accept(visitor)
    assert visitor.trainer_count == len(repo.trainers)
    assert visitor.instance_count == len(repo.instances)
