import os

from agents.mcp import MCPServerSseParams


def get_mcp_blackboard_server_params() -> MCPServerSseParams:
    """
    Get the parameters for the MCP server.

    Returns:
        MCPServerSseParams: The parameters for the MCP server.
    """
    return MCPServerSseParams(
        url=os.getenv("MCP_BLACKBOARD_SERVER", "localhost:8000/sse"),
        headers=None,
        timeout=180,
        sse_read_timeout=180,
    )
