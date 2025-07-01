import json
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Any

from agents.mcp import (
    MCPServer,
    MCPServerSse,
    MCPServerSseParams,
    MCPServerStreamableHttp,
    MCPServerStreamableHttpParams,
)
from tenacity import retry, stop_after_attempt, wait_random_exponential

from ferros.core.utils import get_settings

RESULT_TOOL_NAME = "GetResult"


def get_params() -> MCPServerStreamableHttpParams | MCPServerSseParams:
    """
    Get the parameters for the MCP server.

    Returns:
        MCPServerStreamableHttpParams: The parameters for the MCP server.
    """
    settings = get_settings()
    if settings.blackboard.mcp_transport == "sse":
        return MCPServerSseParams(
            url=f"{settings.blackboard.mcp_server}/sse",
            headers={},
            timeout=180,
            sse_read_timeout=180,
        )
    elif settings.blackboard.mcp_transport == "streamable-http":
        return MCPServerStreamableHttpParams(
            url=f"{settings.blackboard.mcp_server}/mcp",
            headers={},
            timeout=timedelta(seconds=180),
            sse_read_timeout=timedelta(seconds=180),
        )
    else:
        raise ValueError(f"Unknown transport: {settings.blackboard.mcp_transport}")


# Import your server classes


@asynccontextmanager
async def get_mcp_server(
    **kwargs: Any,
) -> AsyncGenerator[MCPServerSse, MCPServerStreamableHttp]:
    settings = get_settings()
    params = get_params()
    if settings.blackboard.mcp_transport == "streamable-http":
        server_cls = MCPServerStreamableHttp  # type: ignore
    elif settings.blackboard.mcp_transport == "sse":
        server_cls = MCPServerSse  # type: ignore
    else:
        raise ValueError(f"Unknown transport: {settings.blackboard.mcp_transport}")

    async with server_cls(params=params, **kwargs) as server:  # type: ignore
        yield server  # type: ignore


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
    data = await server.call_tool(tool_name=RESULT_TOOL_NAME, arguments=args)
    if not data:
        raise ValueError("No result found in memory")
    return json.loads(data.content[0].text)  # type: ignore
