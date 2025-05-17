import json
import os

from agents.mcp import MCPServerSse, MCPServerSseParams


def get_mcp_blackboard_server_params() -> MCPServerSseParams:
    """
    Get the parameters for the MCP server.

    Returns:
        MCPServerSseParams: The parameters for the MCP server.
    """
    return MCPServerSseParams(
        url=os.getenv("MCP_BLACKBOARD_SERVER", "http://localhost:8000/sse"),
        headers=None,
        timeout=180,
        sse_read_timeout=180,
    )


async def get_result(
    plan_id: str, step_id: str, agent_name: str, server: MCPServerSse
) -> str | dict:
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
    data = await server.call_tool(
        tool_name="get_result",
        arguments={
            "plan_id": plan_id,
            "step_id": str(step_id),
            "agent_name": agent_name,
        },
    )
    if not data:
        raise ValueError("No result found in memory")
    return json.loads(data.content[0].text)
