from agents import Agent

from actors.base import build_agent
from core.constants import TASK_AGENTS_INSTRUCTIONS
from core.models import AgentName, Score
from core.utils import get_settings
from tools.web_search import web_search_tool


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
        f"---\n> **Agent**: {name.strip().capitalize()}\n> "
        f"**Agent Instructions**: {instructions.strip()}"
    )


settings = get_settings()
researcher = build_agent(
    settings=settings.researcher,
    instructions=TASK_AGENTS_INSTRUCTIONS[settings.researcher.name.value],
    extra_tools=[web_search_tool],
)


extractor = build_agent(
    settings=settings.extractor,
    instructions=TASK_AGENTS_INSTRUCTIONS[settings.extractor.name.value],
)

analyzer = build_agent(
    settings=settings.analyzer,
    instructions=TASK_AGENTS_INSTRUCTIONS[settings.analyzer.name.value],
)

writer = build_agent(
    settings=settings.writer,
    instructions=TASK_AGENTS_INSTRUCTIONS[settings.writer.name.value],
)

editor = build_agent(
    settings=settings.editor,
    instructions=TASK_AGENTS_INSTRUCTIONS[settings.editor.name.value],
)

evaluator = build_agent(
    settings=settings.evaluator,
    instructions=TASK_AGENTS_INSTRUCTIONS[settings.evaluator.name.value],
    output_type=Score,
)


TASK_AGENTS_REGISTRY: dict[str, Agent] = {
    AgentName.RESEARCHER.value: researcher,
    AgentName.EXTRACTOR.value: extractor,
    AgentName.ANALYZER.value: analyzer,
    AgentName.WRITER.value: writer,
    AgentName.EDITOR.value: editor,
    AgentName.EVALUATOR.value: evaluator,
}


TASK_AGENTS_LIST_PROMPT: str = (
    "\n".join([get_info(name, inst) for name, inst in TASK_AGENTS_INSTRUCTIONS.items()])
    + "\n---"
)
