"""Main Textual application for Pokemon OOP Explorer."""

from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.events import Key
from textual.reactive import reactive
from textual.widgets import Footer, Header, TabbedContent, TabPane, Tree

from pokemon_oop_explorer.introspect import (
    AsciiUmlRenderer,
    ClassGraph,
    ClassGraphBuilder,
    UmlRenderer,
)
from pokemon_oop_explorer.models.base import Inspectable
from pokemon_oop_explorer.models.pokemon import PokemonInstance, PokemonSpecies
from pokemon_oop_explorer.models.trainer import Trainer
from pokemon_oop_explorer.models.visitor import ClassUsageVisitor
from pokemon_oop_explorer.services.repository import DomainRepository
from pokemon_oop_explorer.services.sprite_service import SpriteService
from pokemon_oop_explorer.ui.presenters import (
    detail_text,
    relationship_text,
    tab_sections,
    uml_text,
)
from pokemon_oop_explorer.ui.widgets.panels import (
    AutoScrollPanel,
    DetailPanel,
    RelationshipPanel,
    SpritePanel,
)


class PokemonExplorerApp(App[None]):
    """Interactive object-oriented Pokemon domain explorer."""

    TAB_ORDER = ["uml", "moves", "stats", "identity", "evolution"]

    DETAIL_PLACEHOLDER = "Select any species or instance."
    RELATIONSHIP_PLACEHOLDER = "Class relationships appear here."
    SPRITE_PLACEHOLDER = "Sprite preview appears here."
    DATA_TAB_PLACEHOLDER = "Select an object in the tree to populate this tab."

    CSS_PATH = "theme/explorer.tcss"
    TITLE = "Pokemon OOP Explorer"
    SUB_TITLE = "Gen 1-3 Starter Families"
    BINDINGS = [
        ("1", "focus_nav", "Focus Nav"),
        ("2", "focus_detail", "Focus Details"),
        ("3", "focus_rel", "Focus Relations"),
        ("4", "focus_tabs", "Focus Tabs"),
        ("u", "focus_uml", "Focus UML"),
        ("[", "prev_subtab", "Prev Sub-Tab"),
        ("]", "next_subtab", "Next Sub-Tab"),
        Binding("escape", "unselect", "Unselect", show=False),
        ("x", "unselect", "Unselect"),
        ("q", "quit", "Quit"),
    ]

    current_object: reactive[Inspectable | None] = reactive(None)

    def __init__(self, project_root: Path) -> None:
        super().__init__()
        self._repository = DomainRepository(project_root=project_root)
        self._sprite_service = SpriteService()
        self._class_graph: ClassGraph = ClassGraphBuilder(
            "pokemon_oop_explorer"
        ).build()
        self._uml_renderer: UmlRenderer = AsciiUmlRenderer()

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="main-layout"):
            with Horizontal(id="top-layout"):
                with Vertical(id="left-layout"):
                    yield Tree("Generations / Families / Objects", id="navigation")
                    yield RelationshipPanel(
                        self.RELATIONSHIP_PLACEHOLDER, id="relationship-panel"
                    )
                with Vertical(id="center-layout"):
                    yield DetailPanel(self.DETAIL_PLACEHOLDER, id="detail-panel")
                    yield SpritePanel(self.SPRITE_PLACEHOLDER, id="sprite-panel")
                with Vertical(id="right-layout"):
                    with TabbedContent(initial="uml", id="lower-tabs"):
                        with TabPane("UML", id="uml"):
                            yield AutoScrollPanel(id="tab-uml")
                        with TabPane("Moves/Abilities", id="moves"):
                            yield AutoScrollPanel(id="tab-moves")
                        with TabPane("Stats", id="stats"):
                            yield AutoScrollPanel(id="tab-stats")
                        with TabPane("Identity", id="identity"):
                            yield AutoScrollPanel(id="tab-identity")
                        with TabPane("Evolution", id="evolution"):
                            yield AutoScrollPanel(id="tab-evolution")
        yield Footer()

    def on_mount(self) -> None:
        self._build_navigation_tree()
        self._reset_panels_to_overview()
        self.action_focus_uml()

    def _reset_panels_to_overview(self) -> None:
        """Reset every panel to the initial, nothing-selected state."""
        self.query_one("#detail-panel", DetailPanel).update(self.DETAIL_PLACEHOLDER)
        self.query_one("#relationship-panel", RelationshipPanel).update(
            self.RELATIONSHIP_PLACEHOLDER
        )
        self.query_one("#sprite-panel", SpritePanel).show_sprite(
            self.SPRITE_PLACEHOLDER
        )
        for tab_id in ("tab-moves", "tab-stats", "tab-identity", "tab-evolution"):
            self.query_one(f"#{tab_id}", AutoScrollPanel).update(
                self.DATA_TAB_PLACEHOLDER
            )
        self._render_overview_uml()

    def _build_navigation_tree(self) -> None:
        tree = self.query_one(Tree)
        root = tree.root
        root.expand()

        generation_buckets: dict[int, list[str]] = {}
        for family_name, species_list in self._repository.families.items():
            if not species_list:
                continue
            generation = int(species_list[0].generation)
            generation_buckets.setdefault(generation, []).append(family_name)

        for generation in sorted(generation_buckets):
            generation_name = f"Gen {generation}"
            gen_node = root.add(generation_name)
            for family_name in sorted(generation_buckets[generation]):
                family_node = gen_node.add(family_name)
                for species in self._repository.families[family_name]:
                    family_node.add_leaf(
                        f"[{species.__class__.__name__}] {species.name}",
                        data=species,
                    )

        instance_root = root.add("Pokemon Instances")
        for instance in self._repository.instances:
            instance_root.add_leaf(
                f"[{instance.__class__.__name__}] {instance.display_name}",
                data=instance,
            )

        trainer_root = root.add("Trainers")
        for trainer in self._repository.trainers:
            trainer_root.add_leaf(
                f"[{trainer.__class__.__name__}] {trainer.name}",
                data=trainer,
            )

    def _render_overview_uml(self) -> None:
        visitor = ClassUsageVisitor()
        for trainer in self._repository.trainers:
            trainer.accept(visitor)
        for instance in self._repository.instances:
            instance.accept(visitor)
        for species in self._repository.species_by_key.values():
            species.accept(visitor)
        overview = self._uml_renderer.render(self._class_graph, focus=None)
        header = (
            "[b #e279a1]Domain UML[/]\n"
            f"[#88C0D0]Reachable classes via ClassUsageVisitor: {len(visitor.seen_classes)}[/]\n\n"
        )
        self.query_one("#tab-uml", AutoScrollPanel).update(header + overview)

    def on_tree_node_selected(self, event: Tree.NodeSelected[Inspectable]) -> None:
        obj = event.node.data
        if isinstance(obj, Inspectable):
            self.current_object = obj
            self._render_object(obj)

    def _render_object(self, obj: Inspectable) -> None:
        detail = self.query_one("#detail-panel", DetailPanel)
        relation = self.query_one("#relationship-panel", RelationshipPanel)
        sprite_panel = self.query_one("#sprite-panel", SpritePanel)

        detail.update(detail_text(obj))
        relation.update(relationship_text(obj, graph=self._class_graph))

        sections = tab_sections(obj, graph=self._class_graph)
        self.query_one("#tab-moves", AutoScrollPanel).update(sections["moves"])
        self.query_one("#tab-stats", AutoScrollPanel).update(sections["stats"])
        self.query_one("#tab-identity", AutoScrollPanel).update(sections["identity"])
        self.query_one("#tab-evolution", AutoScrollPanel).update(sections["evolution"])
        self.query_one("#tab-uml", AutoScrollPanel).update(
            sections.get("uml", uml_text(obj, self._class_graph, self._uml_renderer))
        )

        sprite_text = "No sprite available."
        if isinstance(obj, PokemonSpecies):
            sprite_text = self._sprite_service.load_for_species(obj, shiny=False)
        elif isinstance(obj, PokemonInstance):
            sprite_text = self._sprite_service.load_for_instance(obj)
        elif isinstance(obj, Trainer):
            sprite_text = self._sprite_service.load_for_trainer(obj)
        sprite_panel.show_sprite(sprite_text)

    def action_zoom_class(self, class_name: str) -> None:
        """Focus the UML tab on the class with the given name.

        Called from ``[@click=app.zoom_class('Name')]`` markup embedded in the
        UML renderer's output so every class name is clickable.
        """
        target: type | None = next(
            (cls for cls in self._class_graph.nodes if cls.__name__ == class_name),
            None,
        )
        if target is None:
            self.notify(f"Class '{class_name}' not found in graph.", severity="warning")
            return

        uml_panel = self.query_one("#tab-uml", AutoScrollPanel)
        uml_panel.update(self._uml_renderer.render(self._class_graph, focus=target))
        tabs = self.query_one("#lower-tabs", TabbedContent)
        tabs.active = "uml"
        uml_panel.scroll_home(animate=False, force=True)
        uml_panel.focus()

    def action_unselect(self) -> None:
        """Clear the current selection and restore the initial overview."""
        self.current_object = None
        tree = self.query_one("#navigation", Tree)
        try:
            tree.cursor_line = 0
        except Exception:
            pass
        self._reset_panels_to_overview()
        tree.focus()

    def action_focus_nav(self) -> None:
        self.query_one("#navigation", Tree).focus()

    def action_focus_detail(self) -> None:
        self.query_one("#detail-panel", DetailPanel).focus()

    def action_focus_rel(self) -> None:
        self.query_one("#relationship-panel", RelationshipPanel).focus()

    def action_focus_tabs(self) -> None:
        tabs = self.query_one("#lower-tabs", TabbedContent)
        active = tabs.active
        self.query_one(f"#tab-{active}", AutoScrollPanel).focus()

    def action_focus_uml(self) -> None:
        tabs = self.query_one("#lower-tabs", TabbedContent)
        tabs.active = "uml"
        self.query_one("#tab-uml", AutoScrollPanel).focus()

    def _switch_subtab(self, direction: int) -> None:
        tabs = self.query_one("#lower-tabs", TabbedContent)
        active = tabs.active
        if active not in self.TAB_ORDER:
            tabs.active = self.TAB_ORDER[0]
            self.query_one("#tab-moves", AutoScrollPanel).focus()
            return
        index = self.TAB_ORDER.index(active)
        next_index = (index + direction) % len(self.TAB_ORDER)
        next_tab = self.TAB_ORDER[next_index]
        tabs.active = next_tab
        self.query_one(f"#tab-{next_tab}", AutoScrollPanel).focus()

    def action_next_subtab(self) -> None:
        self._switch_subtab(1)

    def action_prev_subtab(self) -> None:
        self._switch_subtab(-1)

    def on_key(self, event: Key) -> None:
        """Route key scrolling to the focused scrollable panel."""
        key_to_action = {
            "up": "action_scroll_up_line",
            "down": "action_scroll_down_line",
            "pageup": "action_scroll_page_up",
            "pagedown": "action_scroll_page_down",
            "home": "action_scroll_home",
            "end": "action_scroll_end",
        }
        action_name = key_to_action.get(event.key)
        if not action_name:
            return

        focused = self.focused
        if isinstance(focused, AutoScrollPanel):
            getattr(focused, action_name)()
            event.stop()
            return

        tabs = self.query_one("#lower-tabs", TabbedContent)
        active = tabs.active
        if not tabs.has_focus or active not in self.TAB_ORDER:
            return

        active_panel = self.query_one(f"#tab-{active}", AutoScrollPanel)
        getattr(active_panel, action_name)()
        event.stop()
