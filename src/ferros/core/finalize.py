import json
from pathlib import Path

from agents.mcp import MCPServer
from rich.layout import Layout

from ferros.agents.utils import get_step
from ferros.core.logging import get_logger
from ferros.models.plan import Plan
from ferros.tools.mcps import get_result


async def fetch_output(plan: Plan, server: MCPServer) -> str:
    """
    Fetch the output from the last editor step in the plan.

    Args:
        plan (Plan): The plan object with the steps for the task.
        server (MCPServerSse): The MCP server to fetch the output from.

    Returns:
        str: The output from the last editor step in the plan.

    Raises:
        ValueError: If no result is found in memory.
    """

    step = get_step("Editor", plan.steps, is_last=True)
    if not step:
        step = get_step("Writer", plan.steps, is_last=True)
    value = await get_result(plan.id, str(step.id), step.agent_name, server)
    return value if isinstance(value, str) else json.dumps(value, indent=2)


async def save_result(plan: Plan, server: MCPServer) -> None:
    """
    Save the result of the plan to a file.

    Args:
        plan (Plan): The plan object with the steps for the task.
        server (MCPServerSse): The MCP server to fetch the output from.
    """
    logger = get_logger(__name__)
    file_path = Path(__file__).parents[3] / f"tmp/results/{plan.id}.txt"
    if file_path.exists():
        logger.info(f"File {file_path} already exists. Overwriting...")
    result = await fetch_output(plan, server)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(result)
    logger.info(f"Result saved to {file_path.name} in tmp folder")
    layout = Layout()
    layout.split_column(
        Layout(name="Task Goal", size=3), Layout(name="Result", size=10)
    )
    layout["Goal"].update(plan.goal)
    layout["Result"].update(result)
