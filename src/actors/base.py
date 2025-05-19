import pathlib
from typing import Any

from agents import Agent, ModelSettings

from core.models import AgentSettings, PlanStep

PROMPTS_HOME = pathlib.Path(__file__).parent / "prompts"
TASK_AGENTS_EXTRA_PROMPT = open(PROMPTS_HOME / "tasks.md").read()


def build_agent(
    settings: AgentSettings,
    instructions: str,
    extra_tools: list[Any] | None = None,
    **kwargs: Any,
) -> Agent:
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
    settings.model_settings.tool_choice = "required"

    full_instructions = instructions
    if settings.is_task_agent:
        full_instructions = TASK_AGENTS_EXTRA_PROMPT.format(
            name=f"{settings.name.value} Agent", instructions=instructions
        )

    return Agent(
        name=settings.name.value,
        model=settings.model,
        instructions=full_instructions,
        tools=tools,
        tool_use_behavior="run_llm_again",
        model_settings=ModelSettings(
            max_tokens=settings.model_settings.max_tokens,
            tool_choice=settings.model_settings.tool_choice,
        ),
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
