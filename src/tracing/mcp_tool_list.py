# type: ignore
from collections.abc import Iterator
from typing import Any

from textual.message import Message
from textual.widget import Widget
from textual.widgets import Label


class MCPToolListSpan(Widget):
    TEXT_STYLE = "bold"
    TEXT_COLOR = "magenta"

    class Selected(Message):
        def __init__(self, detail: str) -> None:
            self.detail = detail
            super().__init__()

    def __init__(self, data: dict[str, Any], indent: int = 0) -> None:
        super().__init__()
        self.data = data
        self.indent = indent
        prefix = " " * (indent * 2)
        self.label_text = f"{prefix}  MCP: {data.get('description', '')}"
        self._label: Label | None = None

    def compose(self) -> Iterator[Label]:
        self._label = Label(self.label_text)
        self._label.styles.color = self.TEXT_COLOR
        self._label.styles.text_style = self.TEXT_STYLE
        yield self._label

    def on_click(self) -> None:
        detail = f"MCP Tool:\n{self.data.get('description', '')}"
        self.post_message(MCPToolListSpan.Selected(detail))
