# type: ignore
from collections.abc import Iterator
from typing import Any

from textual.message import Message
from textual.widget import Widget
from textual.widgets import Label

from tracing.chat_completion import ChatCompletionSpan
from tracing.custom_span import CustomSpan
from tracing.function_call import FunctionCallSpan
from tracing.mcp_tool_list import MCPToolListSpan


class AgentRunSpan(Widget):
    TEXT_COLOR = "cyan"
    TEXT_STYLE = "bold"

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
        name = data.get("name", "Agent")
        self.label_text = f"Agent run: '{name}'"
        prefix = " " * (self.indent * 2)
        if self.has_children:
            self.label_text = f"{prefix}▶ {self.label_text}"
        else:
            self.label_text = f"{prefix}  {self.label_text}"
        self._label: Label | None = None
        self._children_container: Widget | None = None

    def compose(self) -> Iterator[Label | Widget]:
        self._label = Label(self.label_text)
        self._label.styles.color = self.TEXT_COLOR
        self._label.styles.text_style = self.TEXT_STYLE
        yield self._label

        if self.has_children:
            from textual.containers import Container

            self._children_container = Container()
            self._children_container.display = False
            yield self._children_container

            # Process children after the container is yielded
            children_spans: list[Any] = []
            for child in self.data.get("children", []):
                span_type = child.get("type")
                child_indent = self.indent + 1

                if span_type == "mcp":
                    children_spans.append(MCPToolListSpan(child, indent=child_indent))
                elif span_type == "chat":
                    children_spans.append(
                        ChatCompletionSpan(child, indent=child_indent)
                    )
                elif span_type == "function":
                    children_spans.append(FunctionCallSpan(child, indent=child_indent))
                elif span_type == "custom":
                    children_spans.append(CustomSpan(child, indent=child_indent))

            # At the next frame, mount all the child spans to the container
            async def mount_children() -> None:
                for span in children_spans:
                    if self._children_container:
                        self._children_container.mount(span)

            self.set_timer(0, mount_children)

    def on_click(self) -> None:
        if self.has_children and self._children_container and self._label:
            self.expanded = not self.expanded
            arrow = "▼" if self.expanded else "▶"
            name = self.data.get("name", "Agent")
            prefix = " " * (self.indent * 2)
            self._label.update(f"{prefix}{arrow} Agent run: '{name}'")
            self._label.styles.color = self.TEXT_COLOR
            self._label.styles.text_style = self.TEXT_STYLE
            self._children_container.display = self.expanded
        detail = (
            f"Agent Run: '{self.data.get('name', '')}'\n"
            f"Steps: {len(self.data.get('children', []))}"
        )
        self.post_message(AgentRunSpan.Selected(detail))
