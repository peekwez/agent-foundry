import asyncio
from datetime import datetime
from typing import Any

from agents import set_trace_processors
from agents.tracing import (
    Span,
    Trace,
    function_span,
    generation_span,
    handoff_span,
    trace,
)
from agents.tracing.processor_interface import TracingProcessor
from textual import log
from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import (
    Footer,
    Header,
    Label,
    ProgressBar,
    Static,
    TabbedContent,
    TabPane,
    Tree,
)


# Define a custom tracing processor that sends spans to the UI
class TextualTracingProcessor(TracingProcessor):  # type: ignore
    def __init__(self, app: "TraceApp"):
        self.app = app
        # Store spans by ID for later lookup
        self.spans: dict[str, Any] = {}
        # Map from span ID to TreeNode in UI
        self.node_map: dict[str, Any] = {}

    def on_trace_start(self, trace: "Trace") -> None:
        log.info(f"Trace started: {trace.trace_id}")
        # Create a root node for the trace
        tree: Tree[str] = self.app.query_one("#trace_tree", Tree)  # type: ignore
        node = tree.root.add(
            f"Trace: {trace.name or trace.trace_id}", data=trace.trace_id
        )
        self.node_map[trace.trace_id] = node

    def on_trace_end(self, trace: "Trace") -> None:
        log.info(f"Trace ended: {trace.trace_id}")

    def on_span_start(self, span: "Span[Any]") -> None:
        # Store span data
        self.spans[span.span_id] = span
        span_type = getattr(span.span_data, "type", "unknown")
        log.info(f"Span started: {span.span_id} (type: {span_type})")

    def on_span_end(self, span: "Span[Any]") -> None:
        # Update span data and schedule UI update
        self.spans[span.span_id] = span
        log.info(f"Span ended: {span.span_id}")
        # Add the node in the Textual UI
        self.app.call_later(self._add_span_node, span)

    def shutdown(self) -> None:
        pass

    def force_flush(self) -> None:
        pass

    def _add_span_node(self, span: "Span[Any]") -> None:
        """Add a node for this span to the tree in the UI."""
        tree: Tree[str] = self.app.query_one("#trace_tree", Tree)  # type: ignore
        # Determine parent node (tree root if none or not found)
        parent_node = tree.root
        if span.parent_id and span.parent_id in self.node_map:
            parent_node = self.node_map[span.parent_id]
        # Choose label based on span data type
        data = span.span_data
        label = ""
        span_type = getattr(data, "type", "span")
        if span_type == "generation":
            model = getattr(data, "model", None)
            label = f"Generate ({model})" if model else "Generate"
        elif span_type == "function":
            name = getattr(data, "name", "")
            label = f"Function: {name}"
        elif span_type == "handoff":
            fa = getattr(data, "from_agent", None)
            ta = getattr(data, "to_agent", None)
            label = f"Handoff: {fa or '?'} → {ta or '?'}"
        else:
            label = span_type.capitalize()
        # Add the node to the tree and map it
        node = parent_node.add(label, data=span.span_id)
        self.node_map[span.span_id] = node


class TraceApp(App[None]):  # type: ignore
    CSS = """
   TabbedContent {
       background: #1e1e1e;
   }
   #trace_tree {
       height: 100%;
       width: 40%;
       border: round gray;
   }
   #properties_view {
       height: 100%;
       width: 60%;
       border: round gray;
   }
   #properties_content {
       padding: 1 2;
   }
   .task-name {
       color: ansi_bright_cyan;
       padding: 0 1;
   }
   Header {
       background: #333333;
   }
   Footer {
       background: #333333;
   }
   """

    def __init__(self) -> None:
        super().__init__()
        # Initialize and set our custom tracing processor
        self.processor = TextualTracingProcessor(self)
        set_trace_processors([self.processor])

    def compose(self) -> ComposeResult:
        # Header at the top
        yield Header()
        # Tabbed content for switching views
        with TabbedContent():
            # Tracing view
            with TabPane("Tracing", id="trace"):
                with Horizontal():
                    yield Tree("Trace", id="trace_tree")
                    with VerticalScroll(id="properties_view"):
                        yield Static("", id="properties_content")

            # Task progress view
            with TabPane("Tasks", id="tasks"):
                yield Label("Agent Task Progress", classes="task-name")
                task_names = [
                    "context builder",
                    "planner",
                    "researcher",
                    "extractor",
                    "analyzer",
                    "writer",
                    "editor",
                    "evaluator",
                ]
                for task in task_names:
                    # Task title
                    yield Label(task.replace("_", " ").title(), classes="task-name")
                    with Horizontal():
                        yield ProgressBar(total=100, id=f"{task}_progress")
                        yield Label("Running...", id=f"{task}_status")
                    yield Label("Output: In Progress...", id=f"{task}_output")
                yield Footer()

    async def on_mount(self) -> None:
        # Run the demo trace and task simulations as background workers
        self.run_worker(self.run_dummy_trace(), exclusive=True)
        self.run_worker(self.simulate_tasks(), exclusive=True)

    async def run_dummy_trace(self) -> None:
        """Simulate an example trace with spans."""
        t = trace("Demo Workflow")
        t.start(mark_as_current=True)
        # Generation span
        gen1 = generation_span(
            input=[{"role": "user", "content": "What is the weather?"}],
            output=[{"role": "assistant", "content": "It is sunny and 25°C."}],
            model="gpt-4",
        )
        gen1.start(mark_as_current=True)
        await asyncio.sleep(0.6)
        gen1.finish(reset_current=True)
        # Function (tool) span
        func = function_span(
            name="get_weather", input="Location: London", output="25°C, Clear"
        )
        func.start(mark_as_current=True)
        await asyncio.sleep(0.4)
        func.finish(reset_current=True)
        # Handoff span
        hand = handoff_span(from_agent="Triage Agent", to_agent="Analyzer Agent")
        hand.start(mark_as_current=True)
        await asyncio.sleep(0.3)
        hand.finish(reset_current=True)
        # Another generation span
        gen2 = generation_span(
            input=[{"role": "assistant", "content": "It is sunny."}],
            output=[{"role": "assistant", "content": "No analysis needed."}],
            model="gpt-4",
        )
        gen2.start(mark_as_current=True)
        await asyncio.sleep(0.5)
        gen2.finish(reset_current=True)
        t.finish(reset_current=True)

    async def simulate_tasks(self) -> None:
        """Simulate updating progress bars for agent tasks."""
        task_names = [
            "context builder",
            "planner",
            "researcher",
            "extractor",
            "analyzer",
            "writer",
            "editor",
            "evaluator",
        ]
        progress = dict.fromkeys(task_names, 0)
        while True:
            all_done = True
            for task in task_names:
                if progress[task] < 100:
                    progress[task] += 7
                    if progress[task] > 100:
                        progress[task] = 100
                    all_done = False
                # Update progress bar
                pb = self.query_one(f"#{task}_progress", ProgressBar)
                pb.update(progress=progress[task])
                # Update status and output
                status_lbl = self.query_one(f"#{task}_status", Label)
                out_lbl = self.query_one(f"#{task}_output", Label)
                if progress[task] >= 100:
                    status_lbl.update("Done")
                    out_lbl.update("Output: Completed successfully.")
                else:
                    status_lbl.update(f"Running... {progress[task]}%")
                    out_lbl.update(f"Output: {progress[task]}% done.")
            if all_done:
                break
            await asyncio.sleep(1)

    async def on_tree_node_selected(self, event: Tree.NodeSelected[str]) -> None:
        """Display details of the selected span in the properties panel."""
        span_id = event.node.data
        if not span_id or span_id not in self.processor.spans:
            return
        span = self.processor.spans[span_id]
        data = span.span_data
        # Format times and compute duration
        started = span.started_at or ""
        ended = span.ended_at or ""
        try:
            dt_start = datetime.fromisoformat(started.replace("Z", "+00:00"))
            dt_end = datetime.fromisoformat(ended.replace("Z", "+00:00"))
            duration = f"{(dt_end - dt_start).total_seconds() * 1000:.0f} ms"
        except Exception:
            duration = ""
        # Build properties text
        props = [
            f"**ID:** {span.span_id}",
            f"**Parent ID:** {span.parent_id or 'None'}",
            f"**Type:** {data.type}",
            f"**Started:** {started}",
            f"**Ended:** {ended}",
        ]
        if duration:
            props.append(f"**Duration:** {duration}")
        # Include data-specific fields

        details: list[str] = []
        for attr in ("name", "input", "output", "model", "from_agent", "to_agent"):
            if hasattr(data, attr):
                val = getattr(data, attr)
                if val is not None:
                    details.append(f"{attr.capitalize()}: {val}")
        if details:
            props.append(
                "\n".join(
                    [
                        f"**{line.split(':', 1)[0]}:**{line.split(':', 1)[1]}"
                        for line in details
                    ]
                )
            )
        text = "\n\n".join(props)
        self.query_one("#properties_content", Static).update(text)


if __name__ == "__main__":
    app = TraceApp()
    app.run()
