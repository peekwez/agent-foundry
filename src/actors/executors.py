from agents import Agent

from actors.base import build_agent
from core.constants import TASK_AGENTS_INSTRUCTIONS
from core.models import Score
from core.utils import get_settings
from tools.web_search import tool as web_search_tool


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


settings = get_settings()
researcher = build_agent(
    settings=settings.researcher,
    instructions=TASK_AGENTS_INSTRUCTIONS[settings.researcher.name],
    extra_tools=[web_search_tool],
)


extractor = build_agent(
    settings=settings.extractor,
    instructions=TASK_AGENTS_INSTRUCTIONS[settings.extractor.name],
)

analyzer = build_agent(
    settings=settings.analyzer,
    instructions=TASK_AGENTS_INSTRUCTIONS[settings.analyzer.name],
)

writer = build_agent(
    settings=settings.writer,
    instructions=TASK_AGENTS_INSTRUCTIONS[settings.writer.name],
)

editor = build_agent(
    settings=settings.editor,
    instructions=TASK_AGENTS_INSTRUCTIONS[settings.editor.name],
)

evaluator = build_agent(
    settings=settings.evaluator,
    instructions=TASK_AGENTS_INSTRUCTIONS[settings.evaluator.name],
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
