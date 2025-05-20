# type: ignore
from typing import Any

from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Label, Static

# Import span components
from tracing.agent_run import AgentRunSpan
from tracing.chat_completion import ChatCompletionSpan
from tracing.custom_span import CustomSpan
from tracing.function_call import FunctionCallSpan
from tracing.mcp_tool_list import MCPToolListSpan


def get_trace_data(use_live: bool = False) -> dict[str, Any]:
    """
    Retrieve trace data. If use_live is True, fetch from OpenAI Agents SDK
    (not implemented here), otherwise return simulated trace data for demonstration.
    """
    if use_live:
        # TODO: integrate with OpenAI Agents SDK for real traces
        return {}
    # Simulated trace for demo
    return {
        "task": "Knowledge Worker: DB6B3DB9",
        "agent_runs": [
            {
                "type": "agent_run",
                "name": "Context Builder",
                "children": [
                    {
                        "type": "mcp",
                        "description": "list tools from server MCP Blackboard Server",
                    },
                    {
                        "type": "chat",
                        "model": "openai.o3-2025-04-16",
                        "role": "LLM",
                        "content": "Chat completion request for context building",
                    },
                    {
                        "type": "function",
                        "name": "get_context",
                        "result": "Sample context data retrieved",
                    },
                    {
                        "type": "custom",
                        "name": "Plan Executor",
                        "plan": "Summarize Context",
                        "steps_completed": 2,
                        "steps_total": 5,
                        "children": [
                            {
                                "type": "chat",
                                "model": "openai.o3-2025-04-16",
                                "role": "LLM",
                                "content": "Plan step: analyze context",
                            },
                            {
                                "type": "function",
                                "name": "analyze_context",
                                "result": "Analyzed context result",
                            },
                        ],
                    },
                    {
                        "type": "chat",
                        "model": "openai.o3-2025-04-16",
                        "role": "LLM",
                        "content": "Second phase of completion",
                    },
                    {
                        "type": "function",
                        "name": "save_context_description",
                        "result": "Context description saved",
                    },
                ],
            }
        ],
    }


class TraceApp(App):  # type: ignore[no-redef]
    """Main Textual Application for OpenAI Agents Trace UI."""

    def __init__(self, use_live: bool = False):
        super().__init__()
        self.trace_data = get_trace_data(use_live)
        self.log_content: Static | None = None

    def compose(self) -> ComposeResult:
        with Horizontal():
            with VerticalScroll(id="left_panel"):
                task_label = self.trace_data.get("task", "OpenAI Agents trace")
                label = Label(
                    f"OpenAI Agents trace: {task_label}",
                    id="trace-title",
                )
                label.styles.text_style = "bold"
                label.styles.color = "white"
                yield label
                for run in self.trace_data.get("agent_runs", []):
                    yield AgentRunSpan(run, indent=1)
            with VerticalScroll(id="right_panel"):
                self.log_content = Static(
                    "Select a span to see details here.",
                    id="log_content",
                )
                self.log_content.styles.text_style = "bold"
                self.log_content.styles.color = "white"
                yield self.log_content

    # Selection event handlers
    def on_agent_run_span_selected(self, message: AgentRunSpan.Selected) -> None:
        if self.log_content:
            self.log_content.update(message.detail)

    def on_mcp_tool_span_selected(self, message: MCPToolListSpan.Selected) -> None:
        if self.log_content:
            self.log_content.update(message.detail)

    def on_chat_completion_span_selected(
        self, message: ChatCompletionSpan.Selected
    ) -> None:
        if self.log_content:
            self.log_content.update(message.detail)

    def on_function_call_span_selected(
        self, message: FunctionCallSpan.Selected
    ) -> None:
        if self.log_content:
            self.log_content.update(message.detail)

    def on_custom_span_selected(self, message: CustomSpan.Selected) -> None:
        if self.log_content:
            self.log_content.update(message.detail)


if __name__ == "__main__":
    TraceApp(use_live=False).run()
