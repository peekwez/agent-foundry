import pathlib
from typing import Any

from agents import Agent, RunContextWrapper
from agents.mcp import MCPServer

from ferros.core.utils import get_settings
from ferros.models.context import Context


def get_instructions(context: RunContextWrapper, agent: Agent) -> str:
    """
    Get the instructions for the context builder agent.

    Returns:
        str: The instructions for the context builder agent.
    """
    prompts_home = pathlib.Path(__file__).parent / "prompts"
    context_builder_prompt = open(prompts_home / "context-builder.md").read()
    return context_builder_prompt


def get_builder(
    tools: list[Any] | None = None,
    mcp_servers: list[MCPServer] | None = None,
) -> Agent:
    """
    Get the context builder agent with the appropriate instructions.

    Args:
        context (RunContextWrapper[AgentsConfig]): The run context.
        agent (Agent[AgentsConfig]): The agent instance.

    Returns:
        Agent[AgentsConfig]: The planner agent.
    """
    settings = get_settings()
    return Agent(
        name="Context Builder",
        model=settings.context.model,
        instructions=get_instructions,
        model_settings=settings.context.model_settings,
        tool_use_behavior="run_llm_again",
        output_type=Context,
        tools=tools or [],
        mcp_servers=mcp_servers or [],
    )
