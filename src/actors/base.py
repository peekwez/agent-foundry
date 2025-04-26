import pathlib

from agents import Agent, ModelSettings
from core.config import OPENAI_MODEL
from tools.context_parser import read_context
from tools.redis_memory import read_memory, write_memory

PROMPTS_HOME = pathlib.Path(__file__).parent / "prompts"
TASK_AGENT_TOOLS = [read_memory, write_memory, read_context]
TASK_BASE_PROMPT = open(PROMPTS_HOME / "tasks.md").read()


def build_agent(
    name: str,
    instructions: str,
    extra_tools: list | None = None,
    task_agent: bool = False,
    **kwargs,
):
    tools = extra_tools or []
    model_settings: ModelSettings = kwargs.pop("model_settings", ModelSettings())

    if task_agent:
        tools += TASK_AGENT_TOOLS
        instructions = TASK_BASE_PROMPT.format(
            name=f"{name} Agent", instructions=instructions
        )
        model_settings.tool_choice = "required"

    return Agent(
        name=name,
        model=kwargs.pop("model", OPENAI_MODEL),
        instructions=instructions,
        tools=tools,
        tool_use_behavior="run_llm_again",
        model_settings=model_settings,
        **kwargs,
    )
