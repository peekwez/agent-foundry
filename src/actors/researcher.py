from actors.base import build_agent
from agents import WebSearchTool

researcher = build_agent(
    name="Researcher",
    instructions=(
        "You search the web or fetch any relevant data from context "
        "and synthesize concise notes."
    ),
    extra_tools=[WebSearchTool()],
    model="gpt-4o",
)
