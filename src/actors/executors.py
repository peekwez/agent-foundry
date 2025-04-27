from actors.base import build_agent
from actors.constants import TASK_AGENTS_INSTRUCTIONS
from agents import Agent, WebSearchTool
from core.models import Score


def get_info(name: str, instructions: str) -> str:
    """
    Get the agent info in a formatted string

    Args:
        name (str): The name of the agent
        instructions (str): The instructions for the agent

    Returns:
        str: The formatted string with agent info
    """
    return (
        f"---\n> **Agent**: {name.strip()}\n> "
        f"**Agent Instructions**: {instructions.strip()}"
    )


researcher = build_agent(
    name="Researcher",
    instructions=TASK_AGENTS_INSTRUCTIONS["Researcher"],
    extra_tools=[WebSearchTool()],
    task_agent=True,
    model="gpt-4o",
)


extractor = build_agent(
    name="Extractor",
    instructions=TASK_AGENTS_INSTRUCTIONS["Extractor"],
    model="o3",
    task_agent=True,
)

analyzer = build_agent(
    name="Analyzer",
    instructions=TASK_AGENTS_INSTRUCTIONS["Analyzer"],
    model="o3",
    task_agent=True,
)

writer = build_agent(
    name="Writer",
    instructions=TASK_AGENTS_INSTRUCTIONS["Writer"],
    task_agent=True,
    model="o3",
)

editor = build_agent(
    name="Editor",
    instructions=TASK_AGENTS_INSTRUCTIONS["Editor"],
    model="o3",
    task_agent=True,
)

evaluator = build_agent(
    name="Evaluator",
    instructions=TASK_AGENTS_INSTRUCTIONS["Evaluator"],
    model="o3",
    task_agent=True,
    output_type=Score,
)

TASK_AGENTS_REGISTRY: dict[str, Agent] = {
    "Researcher": researcher,
    "Extractor": extractor,
    "Analyzer": analyzer,
    "Writer": writer,
    "Editor": editor,
    "Evaluator": evaluator,
}


TASK_AGENTS_LIST_PROMPT: str = (
    "\n".join([get_info(name, inst) for name, inst in TASK_AGENTS_INSTRUCTIONS.items()])
    + "\n---"
)
