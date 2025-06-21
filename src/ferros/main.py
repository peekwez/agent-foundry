import json
from pathlib import Path
from typing import Any

from agents import Agent, Runner, custom_span, gen_trace_id, trace
from agents.mcp import MCPServerSse

from ferros.agents.builder import context_builder
from ferros.agents.manager import TaskManager
from ferros.agents.planner import planner, re_planner
from ferros.agents.utils import get_step
from ferros.core.utils import load_task_config, log_done, log_info
from ferros.models.context import Context
from ferros.models.plan import Plan
from ferros.tools.mcps import get_mcp_blackboard_server_params, get_result

RESULTS_STORAGE_PATH = Path(__file__).parents[1] / "tmp/results"
print(RESULTS_STORAGE_PATH)


async def add_mcp_server(agent: Agent, server: MCPServerSse) -> None:
    """
    Add a MCP server to the agent.

    Args:
        agent (Agent): The agent to which the server will be added.
        server (MCPServerSse): The MCP server to be added.
    """
    if not agent.mcp_servers:
        agent.mcp_servers = []
    agent.mcp_servers.append(server)


async def add_mcp_server_to_all_agents(server: MCPServerSse) -> None:
    """
    Add a MCP server to all agents in the TASK_AGENTS_REGISTRY.

    Args:
        server (MCPServerSse): The MCP server to be added.
    """

    await add_mcp_server(planner, server)
    await add_mcp_server(re_planner, server)
    await add_mcp_server(context_builder, server)
    # for _, agent in TASK_AGENTS_REGISTRY.items():
    #     await add_mcp_server(agent, server)
    log_done("Agents updated with MCP server for blackboard...")


async def build_context(
    plan_id: str, agent: Agent, context_input: str | list[str] | dict[str, str]
) -> Context:
    """
    Build context for the task using the context builder agent.

    Args:
        plan_id (str): The unique identifier for the plan.
        agent (Agent): The context builder agent.
        context_input (str | list | dict): Input for the context builder.

    Returns:
        Context: The built context object with the descriptions of the context items.

    Raises:
        ValueError: If the context input type is invalid.
    """
    if isinstance(context_input, str):
        context_input = context_input.strip()
    elif isinstance(context_input, dict):
        context_input = json.dumps(context_input, indent=2)
    elif isinstance(context_input, list):  # type: ignore[unreachable]
        context_input = "\n".join(context_input)
    else:
        raise ValueError("Invalid context input type")

    input = f"{context_input}\n\nUse the UUID: {plan_id} as the plan id."
    result = await Runner.run(agent, input=input, max_turns=20)
    context: Context = result.final_output

    size = len(context.contexts)
    log_done(f"Context created with {size} items...")
    return context


async def plan_task(plan_id: str, agent: Agent, user_input: str) -> Plan:
    """
    Plan the task using the planner agent.

    Args:
        plan_id (str): The unique identifier for the plan.
        agent (Agent): The planner agent.
        user_input (str): The user input for the task.

    Returns:
        Plan: The generated plan object with the steps for the task.
    """
    input = f"{user_input}\n\nUse the UUID: {plan_id} as the plan id."
    result = await Runner.run(agent, input=input, max_turns=20)
    plan: Plan = result.final_output

    size = len(plan.steps)
    if agent.name == "Planner":
        log_done(f"Task plan created with {size} steps...")
    elif agent.name == "Re-Planner":
        new_size = len([s for s in plan.steps if s.status == "pending"])
        log_done(f"Task re-planning created with {new_size} steps...")
    return plan


async def execute_plan(
    plan_id: str, plan: Plan, server: MCPServerSse, revisions: int = 3
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

    revised_plan = plan
    user_input = plan.goal
    for rev in range(1, revisions + 1):
        name = f"Plan Executor - Rev {rev}"
        data: dict[str, Any] = {"Revision": rev, "Plan ID": plan_id}
        with custom_span(name=name, data=data):
            tasks = TaskManager(revised_plan, server=server)
            eval = await tasks.run()
            if eval.score >= 0.8:
                break
        revised_plan = await plan_task(plan_id, re_planner, user_input)
    return revised_plan


async def fetch_output(plan: Plan, server: MCPServerSse) -> str:
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
    value = await get_result(plan.id, str(step.id), step.agent_name, server)
    return value if isinstance(value, str) else json.dumps(value, indent=2)


async def save_result(plan: Plan, server: MCPServerSse) -> None:
    """
    Save the result of the plan to a file.

    Args:
        plan (Plan): The plan object with the steps for the task.
        server (MCPServerSse): The MCP server to fetch the output from.
    """
    file_path = Path(__file__).parents[1] / f"tmp/results/{plan.id}.txt"
    if file_path.exists():
        log_info(f"File {file_path} already exists. Overwriting...")

    result = await fetch_output(plan, server)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(result)
    log_done(f"Result saved to {file_path.name} in tmp folder")


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
    """

    trace_id = gen_trace_id() if trace_id is None else trace_id
    guid = trace_id.split("_")[-1]
    server_params = get_mcp_blackboard_server_params()

    async with MCPServerSse(
        params=server_params,
        cache_tools_list=True,
        name="MCP Blackboard Server",
        client_session_timeout_seconds=180,
    ) as server:
        # Add the MCP server to all agents
        await add_mcp_server_to_all_agents(server)

        with trace(
            workflow_name=f"Knowledge Worker: {guid.upper()[:8]}", trace_id=trace_id
        ):
            # Build context
            if context_input:
                await build_context(guid, context_builder, context_input)

            # Plan the task
            plan = await plan_task(guid, planner, user_input)

            # Execute the plan, replan if needed and revise output
            revised_plan = await execute_plan(guid, plan, server, revisions)

            # Save the result to a file
            await save_result(revised_plan, server)


async def run(
    task_config_file: str, revisions: int = 3, trace_id: str | None = None
) -> None:
    """
    Main function to run the agent with the provided task configuration.

    Args:
        task_config_file (str): The path to the task configuration file.
        revisions (int): The number of revisions to perform if needed.
        trace_id (str | None): The trace ID for the run. If None, a new
        trace ID will be generated.
    """
    config = load_task_config(task_config_file)
    user_input = config["goal"]
    context_input = config["context"]
    await run_agent(user_input, context_input, revisions, trace_id)
    log_done("Task completed successfully.")
