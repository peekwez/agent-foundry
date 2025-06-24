from typing import Any

from agents import custom_span
from agents.mcp import MCPServer

from ferros.agents.evaluator import evaluate_result
from ferros.agents.manager import TaskManager
from ferros.agents.planner import plan_task
from ferros.core.logging import get_logger
from ferros.models.plan import Plan


async def execute_plan(
    plan_id: str, plan: Plan, server: MCPServer, revisions: int = 3
) -> Plan:
    """
    Execute the plan using the task manager and replan if needed.
    If the score is not "pass", it will replan the task and execute it again.
    The number of revisions is limited by the `revisions` parameter.

    Args:
        plan_id (str): The unique identifier for the plan.
        plan (Plan): The plan object with the steps for the task.
        server (MCPServerSse): The MCP server to fetch the output from.
        revisions (int): The number of revisions to perform if needed.
        defaults to 3.


    Returns:
        Plan: The revised plan object after executing the task.
    """

    _plan = plan
    user_input = plan.goal
    revision_prefix = (
        "The evaluation did not pass. Please revise the "
        "plan based on the feedback: \n\n"
    )
    logger = get_logger(__name__)
    logger.info(f"Executing plan {plan_id} with goal: {plan.goal}")
    for revision in range(1, revisions + 1):
        name = f"Plan Executor - Rev {revision}"
        data: dict[str, Any] = {"Revision": revision, "Plan Id": plan_id}
        with custom_span(name=name, data=data):
            manager = TaskManager(_plan, server=server)
            await manager.run()
            evals = await evaluate_result(_plan, revision, server)
            if evals.passed:
                break
            user_input = f"Plan goal:\n{plan.goal}\n\n{revision_prefix}{evals.feedback}"
        logger.info(f"Revision {revision} of plan {plan_id} completed.")
        _plan = await plan_task(plan_id, revision, user_input, server)
    return _plan
