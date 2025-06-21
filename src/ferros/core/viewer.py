from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Markdown, TabbedContent, TabPane


class StopwatchApp(App):  # type:ignore
    """A Textual app to manage stopwatches."""

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        with TabbedContent():
            with TabPane("Context Information", id="context"):
                yield Markdown("##### Context Information")
            with TabPane("Task Plan", id="plan"):
                yield Markdown("##### Task Plan Information")
            with TabPane("Blackboard", id="blackboard"):
                yield Markdown("##### Blackboard Information")
            with TabPane("Results", id="results"):
                yield Markdown("##### Results Information")
        yield Footer()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )


if __name__ == "__main__":
    app = StopwatchApp()
    app.run()
