import pathlib

from agents import Agent, ModelSettings
from core.config import OPENAI_MODEL
from core.models import PlanStep
from tools.context_parser import read_context
from tools.redis_memory import read_memory, write_memory

PROMPTS_HOME = pathlib.Path(__file__).parent / "prompts"
TASK_AGENTS_TOOLS = [read_memory, write_memory, read_context]
TASK_AGENTS_EXTRA_PROMPT = open(PROMPTS_HOME / "tasks.md").read()


def build_agent(
    name: str,
    instructions: str,
    extra_tools: list | None = None,
    task_agent: bool = False,
    **kwargs,
):
    """
    Build an agent with the given name and instructions.

    Args:
        name (str): The name of the agent.
        instructions (str): The instructions for the agent.
        extra_tools (list, optional): Additional tools for the agent.
            Defaults to None.
        task_agent (bool, optional): Whether the agent is a task agent.
            Defaults to False.
        **kwargs: Additional keyword arguments.
    """
    tools = extra_tools or []
    model_settings: ModelSettings = kwargs.pop("model_settings", ModelSettings())

    if task_agent:
        tools += TASK_AGENTS_TOOLS
        instructions = TASK_AGENTS_EXTRA_PROMPT.format(
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


def get_last_agent_step(agent_name: str, steps: list[PlanStep]) -> PlanStep:
    """
    Get the last agent from a list of agents.

    Args:
        agent_name (str): The name of the agent.
        steps (list[PlanStep]): The list of agent steps.

    Returns:
        PlanStep: The latest agent step.
    """

    def fn(x: PlanStep) -> bool:
        return x.agent.lower() == agent_name.lower()

    return sorted(filter(fn, steps), key=lambda x: x.id)[-1]
