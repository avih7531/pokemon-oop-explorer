from pathlib import Path

from pokemon_oop_explorer.services.repository import DomainRepository


def test_repository_contains_all_starter_species() -> None:
    repo = DomainRepository(project_root=Path.cwd())
    assert len(repo.species_by_key) == 27
    assert "charizard" in repo.species_by_key
    assert "swampert" in repo.species_by_key


def test_repository_exposes_instances() -> None:
    repo = DomainRepository(project_root=Path.cwd())
    assert len(repo.instances) >= 4
    assert any(
        instance.species and instance.species.species_key == "charizard"
        for instance in repo.instances
    )
