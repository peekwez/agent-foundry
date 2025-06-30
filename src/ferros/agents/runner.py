from agents import gen_trace_id, trace

from ferros.agents.builder import build_context
from ferros.agents.executor import execute_plan
from ferros.agents.planner import plan_task
from ferros.core.finalize import save_result
from ferros.tools.mcps import get_mcp_server


async def run_agent(
    user_input: str,
    context_input: str | list[str] | dict[str, str] | None,
    revisions: int = 3,
    trace_id: str | None = None,
) -> None:
    """
    Run the agent to perform a task based on user input and context.

    Args:
        user_input (str): The user input for the task.
        context_input (str | list | dict | None): The context input for the task.
        revisions (int): The number of revisions to perform if needed.
        trace_id (str | None): The trace ID for the run. If None, a new trace ID
            will be generated.
    """

    trace_id = gen_trace_id() if trace_id is None else trace_id
    guid = trace_id.split("_")[-1]

    async with get_mcp_server(
        cache_tools_list=True,
        name="Blackboard MCP Server",
        client_session_timeout_seconds=180,
    ) as server:
        with trace(
            workflow_name=f"Knowledge Worker: {guid.upper()[:8]}", trace_id=trace_id
        ):
            # build context
            if context_input:
                await build_context(guid, context_input, server)

            # plan the task
            plan = await plan_task(guid, 1, user_input, server)

            # execute the plan, replan, and revise output if required
            revised_plan = await execute_plan(guid, plan, server, revisions)

            # save the result to a file
            await save_result(revised_plan, server)
