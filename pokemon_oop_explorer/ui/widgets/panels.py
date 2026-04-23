"""Panel widgets used in the main explorer screen."""

from __future__ import annotations

from rich.text import Text
from textual.binding import Binding
from textual.events import Click, MouseScrollDown, MouseScrollUp
from textual.widgets import Static


class AutoScrollPanel(Static):
    """Focusable panel with gentle auto-scroll when unfocused."""

    can_focus = True
    BINDINGS = [
        Binding("up", "scroll_up_line", "Up", show=False),
        Binding("down", "scroll_down_line", "Down", show=False),
        Binding("pageup", "scroll_page_up", "Page Up", show=False),
        Binding("pagedown", "scroll_page_down", "Page Down", show=False),
        Binding("home", "scroll_home", "Home", show=False),
        Binding("end", "scroll_end", "End", show=False),
    ]

    _auto_scroll_step = 1
    _auto_scroll_interval_seconds = 0.35

    def on_mount(self) -> None:
        self.set_interval(self._auto_scroll_interval_seconds, self._tick_auto_scroll)

    def _tick_auto_scroll(self) -> None:
        if self.has_focus:
            return
        if self.max_scroll_y <= 0:
            return
        if self.scroll_y >= self.max_scroll_y:
            self.scroll_home(animate=False, force=True)
            return
        self.scroll_to(
            y=self.scroll_y + self._auto_scroll_step,
            animate=False,
            force=True,
            immediate=True,
        )

    def action_scroll_up_line(self) -> None:
        self.scroll_to(
            y=max(0, self.scroll_y - 1), animate=False, force=True, immediate=True
        )

    def action_scroll_down_line(self) -> None:
        self.scroll_to(
            y=min(self.max_scroll_y, self.scroll_y + 1),
            animate=False,
            force=True,
            immediate=True,
        )

    def on_click(self, event: Click) -> None:
        # Don't stop the event: Textual dispatches `[@click=...]` markup
        # actions via the normal click pipeline, so swallowing the event
        # would break click-to-zoom links inside the rendered text.
        self.focus()

    def on_mouse_scroll_up(self, event: MouseScrollUp) -> None:
        self.action_scroll_up_line()
        event.stop()

    def on_mouse_scroll_down(self, event: MouseScrollDown) -> None:
        self.action_scroll_down_line()
        event.stop()


class DetailPanel(AutoScrollPanel):
    """Center panel for selected object details."""

    DEFAULT_CSS = """
    DetailPanel {
        border: tall #5E81AC;
        padding: 0 1;
    }
    """


class RelationshipPanel(AutoScrollPanel):
    """Right panel for hierarchy and relationships."""

    DEFAULT_CSS = """
    RelationshipPanel {
        border: tall #a97ea1;
        padding: 0 1;
    }
    """


class SpritePanel(Static):
    """Renders ANSI sprites while preserving colors."""

    def show_sprite(self, sprite_text: str) -> None:
        self.update(Text.from_ansi(sprite_text))
