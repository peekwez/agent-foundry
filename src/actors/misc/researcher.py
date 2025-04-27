from actors.base import build_agent
from actors.constants import RESEARCHER_INSTRUCTIONS
from agents import WebSearchTool

researcher = build_agent(
    name="Researcher",
    instructions=RESEARCHER_INSTRUCTIONS,
    extra_tools=[WebSearchTool()],
    task_agent=True,
    model="gpt-4o",
)
