# type: ignore

from collections.abc import Iterator
from typing import Any

from textual.message import Message
from textual.widget import Widget
from textual.widgets import Label


class ChatCompletionSpan(Widget):
    TEXT_COLOR = "green"
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
        model = data.get("model", "")
        self.label_text = f"{prefix}  Chat completion with '{model}' [LLM]"
        self._label: Label | None = None

    def compose(self) -> Iterator[Label]:
        self._label = Label(self.label_text)
        self._label.styles.color = self.TEXT_COLOR
        self._label.styles.text_style = self.TEXT_STYLE
        yield self._label

    def on_click(self) -> None:
        detail = (
            "Chat Completion:\n"
            f"Model: {self.data.get('model', '')}\n"
            f"Content: {self.data.get('content', '')}"
        )
        self.post_message(ChatCompletionSpan.Selected(detail))
