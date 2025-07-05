from agents import custom_span, gen_trace_id, trace

from ferros.agents.builder import build_context
from ferros.agents.evaluator import evaluate_result
from ferros.agents.manager import TaskManager
from ferros.agents.planner import plan_task
from ferros.core.finalize import save_result
from ferros.core.logging import get_logger
from ferros.core.store import send_update
from ferros.models.evaluation import EvaluationResults
from ferros.models.plan import Plan
from ferros.tools.mcps import get_mcp_server

STEP_ID = 10000
AGENT_NAME = "knowledge worker"


async def run_agent(
    user_input: str,
    context_input: str | list[str] | dict[str, str] | None,
    revisions: int = 3,
    trace_id: str | None = None,
    session_id: str | None = None,
) -> None:
    """
    Run the agent to perform a task based on user input and context.

    Args:
        user_input (str): The user input for the task.
        context_input (str | list | dict | None): The context input for the task.
        revisions (int): The number of revisions to perform if needed.
        trace_id (str | None): The trace ID for the run. If None, a new trace ID
            will be generated.
        session_id (str | None): The session ID for the run. If None, a new session
            ID will be generated.
    """

    trace_id = gen_trace_id() if trace_id is None else trace_id
    guid = trace_id.split("_")[-1]
    revision_prefix = (
        "The evaluation did not pass. Please revise the "
        "plan based on the feedback: \n\n"
    )
    logger = get_logger(__name__)

    plan: Plan | None = None
    evals: EvaluationResults | None = None

    async with get_mcp_server(
        cache_tools_list=True,
        name="Blackboard MCP Server",
        client_session_timeout_seconds=180,
    ) as server:
        metadata = {"Plan Id": guid, "User Input": user_input}
        short_id = guid.upper()[:8]
        with trace(
            workflow_name=f"Knowledge Worker: {short_id}",
            trace_id=trace_id,
            group_id=session_id,
            metadata=metadata,
        ):
            logger.info(f"Starting new task execution id: {guid}")
            await send_update(guid, STEP_ID, AGENT_NAME, "running")

            # initialize manager
            manager = TaskManager(server=server)

            # build context
            if context_input:
                _ = await build_context(guid, context_input, server)

            for revision in range(1, revisions + 1):
                name = f"Task Pass {revision} of {revisions}"
                data = {"Plan Id": guid, "User Input": user_input}

                with custom_span(name=name, data=data):
                    # plan the task
                    plan = await plan_task(guid, revision, user_input, server)

                    # run the plan steps
                    await manager.run(plan, revision)

                    # evaluate the results from the last step
                    evals = await evaluate_result(plan, revision, server, checks=3)

                if evals.passed:
                    # if the evaluation passed, break the loop
                    break

                # prepare the user input for the next iteration or final output
                user_input = (
                    f"Plan goal:\n{plan.goal}\n\n{revision_prefix}{evals.feedback}"
                )

            # save results
            if plan:
                await save_result(plan, server)

            if evals and not evals.passed:
                await send_update(
                    guid,
                    STEP_ID,
                    AGENT_NAME,
                    "completed",
                    message="Task did not pass all evaluations.",
                )
                logger.warning(
                    f"Task execution did not pass all evaluations: {guid}. "
                    "Please check the feedback and revise the plan."
                )
                return

            await send_update(guid, STEP_ID, AGENT_NAME, "completed")
            logger.info(f"Task execution completed successfully: {guid}")
