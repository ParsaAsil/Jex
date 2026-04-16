"""jex — interactive JSON explorer TUI."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import Footer, Header, Input, Static, Tree
from textual.widgets.tree import TreeNode


def _label_for(key: Any, value: Any) -> str:
    """Render a tree node label for a given key/value pair."""
    if isinstance(value, dict):
        return f"[bold cyan]{key}[/] [dim]{{{len(value)}}}[/]"
    if isinstance(value, list):
        return f"[bold cyan]{key}[/] [dim][{len(value)}][/]"
    if value is None:
        return f"[cyan]{key}[/]: [dim italic]null[/]"
    if isinstance(value, bool):
        return f"[cyan]{key}[/]: [yellow]{str(value).lower()}[/]"
    if isinstance(value, (int, float)):
        return f"[cyan]{key}[/]: [magenta]{value}[/]"
    # strings — truncate anything too long
    text = str(value)
    if len(text) > 80:
        text = text[:77] + "..."
    return f"[cyan]{key}[/]: [green]{text!r}[/]"


def _build(node: TreeNode, data: Any) -> None:
    """Recursively populate the tree from a JSON structure."""
    if isinstance(data, dict):
        for k, v in data.items():
            child = node.add(_label_for(k, v), data={"key": k, "value": v})
            if isinstance(v, (dict, list)):
                _build(child, v)
    elif isinstance(data, list):
        for i, v in enumerate(data):
            child = node.add(_label_for(i, v), data={"key": i, "value": v})
            if isinstance(v, (dict, list)):
                _build(child, v)


class DetailPanel(Static):
    """Right-hand panel showing the full value under the cursor."""

    def show(self, payload: Any) -> None:
        if payload is None:
            self.update("[dim]Select a node to inspect[/dim]")
            return
        try:
            rendered = json.dumps(payload, indent=2, ensure_ascii=False)
        except (TypeError, ValueError):
            rendered = repr(payload)
        self.update(rendered)


class JexApp(App):
    """Interactive JSON tree explorer."""

    CSS = """
    Screen { layout: vertical; }
    #body { height: 1fr; }
    #tree-wrap { width: 60%; border: round $accent; padding: 0 1; }
    #detail-wrap { width: 40%; border: round $secondary; padding: 0 1; }
    Tree { background: transparent; }
    DetailPanel { padding: 0 1; color: $text; }
    #search { dock: top; height: 3; }
    #status { dock: bottom; height: 1; background: $panel; color: $text-muted; padding: 0 1; }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("/", "focus_search", "Search"),
        Binding("escape", "clear_search", "Clear"),
        Binding("e", "expand_all", "Expand all"),
        Binding("c", "collapse_all", "Collapse"),
        Binding("y", "copy_value", "Copy value"),
    ]

    current_path: reactive[str] = reactive("$")

    def __init__(self, data: Any, source: str) -> None:
        super().__init__()
        self.data = data
        self.source = source

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        yield Input(placeholder="Search keys... (press / to focus)", id="search")
        with Horizontal(id="body"):
            with Vertical(id="tree-wrap"):
                yield Tree("root", id="tree")
            with Vertical(id="detail-wrap"):
                yield DetailPanel(id="detail")
        yield Static(id="status")
        yield Footer()

    def on_mount(self) -> None:
        tree: Tree = self.query_one("#tree", Tree)
        tree.root.set_label(f"[bold]{self.source}[/]")
        tree.root.data = {"key": "$", "value": self.data}
        _build(tree.root, self.data)
        tree.root.expand()
        tree.focus()
        self._update_status()

    def _update_status(self) -> None:
        self.query_one("#status", Static).update(
            f" path: [bold]{self.current_path}[/]   "
            f"[dim]/ search · e expand · c collapse · y copy · q quit[/]"
        )

    def watch_current_path(self) -> None:
        self._update_status()

    # ---------- events ----------

    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        node = event.node
        path = self._path_of(node)
        self.current_path = path
        payload = node.data["value"] if node.data else None
        self.query_one("#detail", DetailPanel).show(payload)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "search":
            return
        query = event.value.strip().lower()
        tree = self.query_one("#tree", Tree)
        if not query:
            return
        match = self._find_node(tree.root, query)
        if match is not None:
            # walk up and expand ancestors so the match is visible
            parent = match.parent
            while parent is not None:
                parent.expand()
                parent = parent.parent
            tree.select_node(match)
            tree.scroll_to_node(match)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.query_one("#tree", Tree).focus()

    # ---------- actions ----------

    def action_focus_search(self) -> None:
        self.query_one("#search", Input).focus()

    def action_clear_search(self) -> None:
        search = self.query_one("#search", Input)
        search.value = ""
        self.query_one("#tree", Tree).focus()

    def action_expand_all(self) -> None:
        self.query_one("#tree", Tree).root.expand_all()

    def action_collapse_all(self) -> None:
        root = self.query_one("#tree", Tree).root
        for child in list(root.children):
            child.collapse_all()

    def action_copy_value(self) -> None:
        tree = self.query_one("#tree", Tree)
        if tree.cursor_node is None or tree.cursor_node.data is None:
            return
        value = tree.cursor_node.data["value"]
        try:
            text = json.dumps(value, indent=2, ensure_ascii=False)
        except (TypeError, ValueError):
            text = str(value)
        try:
            import pyperclip  # optional dep
            pyperclip.copy(text)
            self.notify("copied to clipboard", timeout=2)
        except Exception:
            self.notify("install pyperclip for clipboard support", severity="warning")

    # ---------- helpers ----------

    def _path_of(self, node: TreeNode) -> str:
        parts: list[str] = []
        current: TreeNode | None = node
        while current is not None and current.data is not None:
            k = current.data["key"]
            if isinstance(k, int):
                parts.append(f"[{k}]")
            elif k == "$":
                break
            else:
                parts.append(f".{k}")
            current = current.parent
        return "$" + "".join(reversed(parts))

    def _find_node(self, node: TreeNode, query: str) -> TreeNode | None:
        for child in node.children:
            if child.data is not None:
                key = str(child.data["key"]).lower()
                if query in key:
                    return child
            found = self._find_node(child, query)
            if found is not None:
                return found
        return None


def load_json(path: str | None) -> tuple[Any, str]:
    if path is None or path == "-":
        return json.load(sys.stdin), "<stdin>"
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        return json.load(f), p.name
