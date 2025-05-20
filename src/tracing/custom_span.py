# type: ignore

from collections.abc import Iterator
from typing import Any

from textual.message import Message
from textual.widget import Widget
from textual.widgets import Label

from tracing.chat_completion import ChatCompletionSpan
from tracing.function_call import FunctionCallSpan
from tracing.mcp_tool_list import MCPToolListSpan


class CustomSpan(Widget):
    TEXT_STYLE = "bold"
    TEXT_COLOR = "blue"

    class Selected(Message):
        def __init__(self, detail: str) -> None:
            self.detail = detail
            super().__init__()

    def __init__(self, data: dict[str, Any], indent: int = 0) -> None:
        super().__init__()
        self.data = data
        self.indent = indent
        self.has_children = bool(data.get("children"))
        self.expanded = False
        self.steps_completed = data.get("steps_completed", 0)
        self.steps_total = data.get("steps_total", 0)
        name = data.get("name", "Custom")
        plan = data.get("plan", "")
        main = f"{name}: {plan}" if plan else name
        progress = ""
        if self.steps_total:
            filled = int((self.steps_completed / self.steps_total) * 10)
            bar = "#" * filled + "-" * (10 - filled)
            progress = f" [{bar}] {self.steps_completed}/{self.steps_total}"
        prefix = " " * (indent * 2)
        if self.has_children:
            self.label_text = f"{prefix}▶ {main}{progress}"
        else:
            self.label_text = f"{prefix}  {main}{progress}"
        self._label: Label | None = None
        self._children_container: Widget | None = None

    def compose(self) -> Iterator[Label | Widget]:
        self._label = Label(self.label_text)
        self._label.styles.color = self.TEXT_COLOR
        self._label.styles.text_style = self.TEXT_STYLE
        yield self._label
        if self.has_children:
            from textual.widget import Widget as _W

            self._children_container = _W()
            self._children_container.display = False
            for child in self.data.get("children", []):
                t = child.get("type")
                ind = self.indent + 1
                if t == "mcp":
                    self._children_container.mount(MCPToolListSpan(child, indent=ind))
                elif t == "chat":
                    self._children_container.mount(
                        ChatCompletionSpan(child, indent=ind)
                    )
                elif t == "function":
                    self._children_container.mount(FunctionCallSpan(child, indent=ind))
            yield self._children_container

    def on_click(self) -> None:
        if self.has_children and self._children_container and self._label:
            self.expanded = not self.expanded
            arrow = "▼" if self.expanded else "▶"
            name = self.data.get("name", "Custom")
            plan = self.data.get("plan", "")
            main = f"{name}: {plan}" if plan else name
            progress = ""
            if self.steps_total:
                filled = int((self.steps_completed / self.steps_total) * 10)
                bar = "#" * filled + "-" * (10 - filled)
                progress = f" [{bar}] {self.steps_completed}/{self.steps_total}"
            prefix = " " * (self.indent * 2)
            self._label.update(f"{prefix}{arrow} {main}{progress}")
            self._label.styles.color = self.TEXT_COLOR
            self._label.styles.text_style = self.TEXT_STYLE
            self._children_container.display = self.expanded
        detail = (
            f"{self.data.get('name', 'Custom')}\n"
            f"Plan: {self.data.get('plan', '')}\n"
            f"Progress: {self.steps_completed}/{self.steps_total}"
        )
        self.post_message(CustomSpan.Selected(detail))
