# type: ignore
from collections.abc import Iterator
from typing import Any

from textual.message import Message
from textual.widget import Widget
from textual.widgets import Label


class FunctionCallSpan(Widget):
    TEXT_COLOR = "yellow"
    TEXT_STYLE = "bold"

    class Selected(Message):
        def __init__(self, detail: str) -> None:
            self.detail = detail
            super().__init__()

    def __init__(self, data: dict[str, Any], indent: int = 0) -> None:
        super().__init__()
        self.data = data
        self.indent = indent
        prefix = " " * (indent * 2)
        func_name = self.data.get("name", "")
        self.label_text = f"{prefix}  Function: {func_name}"
        self._label: Label | None = None

    def compose(self) -> Iterator[Label]:
        self._label = Label(self.label_text)
        self._label.styles.color = self.TEXT_COLOR
        self._label.styles.text_style = self.TEXT_STYLE
        yield self._label

    def on_click(self) -> None:
        detail = (
            "Function Call:\n"
            f"Name: {self.data.get('name', '')}\n"
            f"Result: {self.data.get('result', '')}"
        )
        self.post_message(FunctionCallSpan.Selected(detail))
