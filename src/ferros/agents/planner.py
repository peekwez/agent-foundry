import pathlib
from typing import Any

from agents import Agent, RunContextWrapper
from agents.mcp import MCPServer

from ferros.core.utils import get_settings
from ferros.models.agents import AgentsConfig
from ferros.models.plan import Plan


def get_instructions(
    replanner: bool,
    context: RunContextWrapper[AgentsConfig],
    agent: Agent[AgentsConfig],
) -> str:
    """
    Get the instructions for the planner agent.

    Returns:
        str: The instructions for the planner agent.
    """
    text: list[str] = []
    for agent_config in context.context.agents:
        name = agent_config.name.strip().capitalize()
        instructions = agent_config.instructions.strip()
        string = (
            f"--\n> "
            f">**Agent Name**: {name}\n"
            f">**Agent SDK**: {agent_config.sdk}\n"
            f">**Agent Version**: {agent_config.version}\n"
            f">**Agent Instruction**: {instructions}\n"
        )
        text.append(string)
    prompt_file = "re-planner.md" if replanner else "planner.md"
    prompts_home = pathlib.Path(__file__).parent / "prompts"
    planner_prompt = open(prompts_home / prompt_file).read()
    return planner_prompt.format(agent_list="\n".join(text))


def get_planner(
    tools: list[Any] | None = None,
    mcp_servers: list[MCPServer] | None = None,
    replanner: bool = False,
) -> Agent[AgentsConfig]:
    """
    Get the planner agent with the appropriate instructions.

    Args:
        context (RunContextWrapper[AgentsConfig]): The run context.
        agent (Agent[AgentsConfig]): The agent instance.

    Returns:
        Agent[AgentsConfig]: The planner agent.
    """
    settings = get_settings()
    return Agent(
        name="Planner" if not replanner else "Re-Planner",
        instructions=lambda context, agent: get_instructions(replanner, context, agent),
        model=settings.planner.model,
        tool_use_behavior="run_llm_again",
        model_settings=settings.planner.model_settings,
        output_type=Plan,
        tools=tools or [],
        mcp_servers=mcp_servers or [],
    )
