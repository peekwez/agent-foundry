from agents.mcp import MCPServerStdio


def filesystem_server(path: str):
    return MCPServerStdio(
        command=["npx", "-y", "@modelcontextprotocol/server-filesystem", path]
    )
