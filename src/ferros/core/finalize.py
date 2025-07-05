import json
from pathlib import Path

from agents.mcp import MCPServer

from ferros.agents.utils import get_step
from ferros.core.logging import get_logger
from ferros.core.utils import get_settings
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

    if not step:
        raise ValueError(
            "No result found in memory. Please run the plan first to generate results."
        )

    value = await get_result(plan.id, str(step.id), step.agent_name, server)
    return value if isinstance(value, str) else json.dumps(value, indent=2)


async def save_result(plan: Plan, server: MCPServer) -> None:
    """
    Save the result of the plan to a file.

    Args:
        plan (Plan): The plan object with the steps for the task.
        server (MCPServerSse): The MCP server to fetch the output from.
    """
    settings = get_settings()
    logger = get_logger(__name__)
    file_path = Path(settings.files.base_dir) / f"{plan.id}.txt"

    if not file_path.suffix.endswith(tuple(settings.files.allowed_extensions)):
        raise ValueError(
            f"File extension not allowed. Allowed "
            f"extensions are: {settings.files.allowed_extensions}"
        )

    file_path.parent.mkdir(parents=True, exist_ok=True)
    if file_path.exists():
        logger.info(f"File {file_path} already exists. Overwriting...")
    result = await fetch_output(plan, server)
    logger.info(f"Fetched last step result for plan {plan.id}")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(result)

    if settings.files.max_size and file_path.stat().st_size > settings.files.max_size:
        file_path.unlink(missing_ok=True)
        raise ValueError(
            f"File size exceeds the maximum allowed size of "
            f"{settings.files.max_size} bytes."
        )

    logger.info(f"Result saved to {file_path.name} in tmp folder")
    # layout = Layout()
    # layout.split_column(Layout(name="Goal", size=3), Layout(name="Result", size=10))
    # layout["Goal"].update(plan.goal)
    # layout["Result"].update(result)


# if __name__ == "__main__":
#     # This block is for testing purposes only
#     import asyncio
#     import sys

#     from dotenv import load_dotenv

#     from ferros.core.utils import load_settings
#     from ferros.models.agents import SDKType
#     from ferros.models.plan import PlanStep

#     load_dotenv()

#     # Accept environment args
#     if len(sys.argv) > 1:
#         env_file = sys.argv[1]
#         load_settings(env_file)

#     async def main():
#         # Example usage
#         plan = Plan(
#             id="23a775fdcd9e4e7daed9dced21f8a294",
#             goal="Example task goal",
#             steps=[
#                 PlanStep(
#                     id=1,
#                     agent_name="Editor",
#                     agent_sdk=SDKType.OPENAI,
#                     agent_version="78c1799755604df4b481861418638f9c",
#                     prompt="SSDFSS",
#                     revision=1,
#                     status="pending",
#                     depends_on=[],
#                 )
#             ],
#         )
#         # async with get_mcp_server(
#         #     cache_tools_list=True,
#         #     name="Blackboard MCP Server",
#         #     client_session_timeout_seconds=180,
#         # ) as server:
#         await save_result(plan, None)

#     asyncio.run(main())
