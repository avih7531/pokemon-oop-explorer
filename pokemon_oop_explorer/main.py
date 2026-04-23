"""Entrypoint for running the Textual app."""

from __future__ import annotations

from pathlib import Path

from pokemon_oop_explorer.app import PokemonExplorerApp


def run() -> None:
    project_root = Path(__file__).resolve().parent.parent
    app = PokemonExplorerApp(project_root=project_root)
    app.run()


if __name__ == "__main__":
    run()
