import json
import pathlib
from typing import Any

from agents import Agent, RunContextWrapper, Runner, custom_span
from agents.mcp import MCPServer

from ferros.core.logging import get_logger
from ferros.core.store import send_update
from ferros.core.utils import get_settings
from ferros.models.context import Context

STEP_ID = 50000
AGENT_NAME = "context builder"


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


async def build_context(
    plan_id: str, context_input: str | list[str] | dict[str, str], server: MCPServer
) -> Context:
    """
    Build context for the task using the context builder agent.

    Args:
        plan_id (str): The unique identifier for the plan.
        agent (Agent): The context builder agent.
        context_input (str | list | dict): Input for the context builder.

    Returns:
        Context: The built context object with the descriptions of the context items.

    Raises:
        ValueError: If the context input type is invalid.
    """

    logger = get_logger(__name__)
    if isinstance(context_input, str):
        context_input = context_input.strip()
    elif isinstance(context_input, dict):
        context_input = json.dumps(context_input, indent=2)
    elif isinstance(context_input, list):  # type: ignore[unreachable]
        context_input = ",".join(context_input).strip()
    else:
        raise ValueError("Invalid context input type")

    with custom_span(
        name="Context Building",
        data={"Plan Id": plan_id, "Context Input": context_input},
    ):
        await send_update(plan_id, STEP_ID, AGENT_NAME, "running")
        logger.info(
            f"Building context for plan {plan_id} with input: {context_input[:100]}..."
        )
        input = f"{context_input}\n\nUse the UUID: {plan_id} as the plan id."
        try:
            agent = get_builder(mcp_servers=[server])
            result = await Runner.run(agent, input=input, max_turns=20)
            context: Context = result.final_output
            size = len(context.contexts)
            logger.info(f"✔ Context created with {size} items...")
            await send_update(plan_id, STEP_ID, AGENT_NAME, "completed")
            return context
        except Exception as e:
            await send_update(plan_id, STEP_ID, AGENT_NAME, "failed")
            logger.exception(f"Failed to build context for plan {plan_id}: {e}")
            raise e
