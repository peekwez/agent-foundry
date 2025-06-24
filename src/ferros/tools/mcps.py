import json
from datetime import timedelta
from typing import Any

from agents.mcp import MCPServer, MCPServerStreamableHttpParams
from tenacity import retry, stop_after_attempt, wait_random_exponential

from ferros.core.utils import get_settings


def get_params() -> MCPServerStreamableHttpParams:
    """
    Get the parameters for the MCP server.

    Returns:
        MCPServerStreamableHttpParams: The parameters for the MCP server.
    """
    settings = get_settings()
    return MCPServerStreamableHttpParams(
        url=f"{settings.blackboard.server}/blackboard/mcp",
        headers={},
        timeout=timedelta(seconds=180),
        sse_read_timeout=timedelta(seconds=180),
    )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_random_exponential(multiplier=1, max=15),
    reraise=True,
)
async def get_result(
    plan_id: str, step_id: str, agent_name: str, server: MCPServer
) -> Any:
    """
    Get the result from the blackboard using the provided plan ID, step ID,
    and agent name.

    Args:
        plan_id (str): The unique identifier for the plan.
        step_id (int): The unique identifier for the step.
        agent_name (str): The name of the agent.

    Returns:
        str: The result read from the server.
    """
    args = {"plan_id": plan_id, "step_id": str(step_id), "agent_name": agent_name}
    data = await server.call_tool(tool_name="get_result", arguments=args)
    if not data:
        raise ValueError("No result found in memory")
    return json.loads(data.content[0].text)  # type: ignore
