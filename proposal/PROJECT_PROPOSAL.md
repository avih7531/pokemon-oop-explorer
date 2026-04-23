# Project Proposal: Pokemon OOP Explorer

## Overview

This project is a terminal-based Python application built with Textual to explore Pokemon starter families (Gen 1-3) through object-oriented design.  
The focus is on software engineering concepts like inheritance, composition, encapsulation, and polymorphism rather than building a full Pokedex.

## Goals

- Build a clean, modular OOP domain model for species, instances, moves, abilities, items, and evolution.
- Provide an interactive TUI for browsing relationships, stats, learnsets, and identity mechanics.
- Use cached PokeAPI data (Gen 3 standard) for accurate stats, moves, and evolution details.
- Demonstrate professional project structure, testing, and maintainable code organization.

## Scope

- Included: Gen 1-3 starter lines and their evolutions.
- Included: Species-level and instance-level inspection, shiny calculation, and local sprite rendering.
- Not included: Full national dex and full battle simulator mechanics.

## Use Cases

**Actor:** a student or reviewer running the app in a terminal to study the object model and starter-line data.


| ID   | Use case                   | Summary                                                                                                                                           |
| ---- | -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| UC-1 | Browse the catalog         | Open the app and navigate the tree by generation, starter family, and domain object (e.g., species vs. instance) to locate a Pokémon of interest. |
| UC-2 | Inspect domain objects     | Select an object and read structured detail in the center pane (fields, types, and how the class represents the concept).                         |
| UC-3 | View class relationships   | See inheritance and composition or associations for the current selection so design choices (interfaces, hierarchies) are visible while browsing. |
| UC-4 | Review moves and abilities | Use the Moves/Abilities tab to inspect learnsets and ability bindings tied to the species or instance model.                                      |
| UC-5 | Analyze stats              | Use the Stats tab to examine base or computed stats and how stat objects fit the domain layer.                                                    |
| UC-6 | Explore identity mechanics | Use the Identity tab to inspect identifiers and shiny-related logic (e.g., Gen 3-style computation) at the value-object level.                    |
| UC-7 | Trace evolution            | Use the Evolution tab to follow evolution rules and stages for a starter line without simulating full battles.                                    |
| UC-8 | Preview sprites            | View locally cached regular and shiny sprite output alongside textual detail for visual confirmation of species or instance context.              |


**Out of scope for these use cases:** competitive battle simulation, network live PokeAPI calls during normal use (data is expected to be cached/seeded), and coverage of Pokémon outside the Gen 1–3 starter families listed in scope.

## Deliverables

- Textual-based multi-pane TUI explorer.
- Structured Python package with tests.
- Seeded/cached data pipeline from PokeAPI.

## Reference Image

Project Preview