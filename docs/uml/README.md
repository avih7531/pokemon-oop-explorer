# UML diagrams

PlantUML sources and rendered PNGs for the Pokemon OOP Explorer use cases. All
diagrams include [`_theme.iuml`](_theme.iuml) which applies the app's color
palette (same one used by the Textual TUI and the ASCII UML tab).

## Layout

- [`use_cases/images/`](use_cases/images/) — rendered PNGs.
  - [`overview.png`](use_cases/images/overview.png): `Student / Reviewer`
    actor with all eight use cases and their `<<include>>` / `<<extend>>`
    relationships.
  - `uc-1_browse_catalog.png` … `uc-8_preview_sprites.png`: one activity
    diagram per use case showing the `|Student|` / `|System|` flow.
- [`use_cases/sources/`](use_cases/sources/) — PlantUML `.puml` sources that
  produced the images above.
- [`_theme.iuml`](_theme.iuml) — shared `skinparam` block loaded by every
  diagram via `!include ../../_theme.iuml`.
