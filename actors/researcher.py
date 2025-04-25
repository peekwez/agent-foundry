from agents import WebSearchTool

from actors.base import build_agent

researcher = build_agent(
    name="Researcher",
    instructions="You search the web and synthesize concise notes.",
    extra_tools=[WebSearchTool()],
    model="gpt-4o",
)
