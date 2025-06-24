from typing import Any

from agents.mcp import MCPServer

from ferros.agents.factory import get_agent_config
from ferros.core.logging import get_logger
from ferros.models.plan import PlanStep
from ferros.tools.web_search import web_search_tool


async def run(plan_id: str, step: PlanStep, mcp_servers: list[MCPServer]) -> None:
    """
    Run an OpenAI agent for a given plan step.

    Args:
        plan_id (str): The ID of the plan.
        step (PlanStep): The step to run.
        mcp_servers (list[MCPServer]): List of MCP servers to use.

    Returns:
        None
    """
    logger = get_logger(__name__)
    logger.info(f"Running OpenAI agent for step: {step.agent_name}")
    config = get_agent_config(step.agent_name, step.agent_sdk, step.agent_version)
    tools: list[Any] = []
    if step.agent_name.lower().find("researcher") > -1:
        tools = [web_search_tool]
    agent = config.create_agent(tools=tools, mcp_servers=mcp_servers)
    input = f"{step.prompt} \n\n The plan id is '{plan_id}'"
    await config.run_agent(agent, input=input, max_turns=60)
    logger.info(f"Completed running OpenAI agent for step: {step.agent_name}")
