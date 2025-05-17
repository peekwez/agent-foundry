import json

from agents import Agent, Runner, custom_span, gen_trace_id, trace
from agents.mcp import MCPServerSse
from dotenv import load_dotenv

from actors.base import get_last_agent_step
from actors.builder import context_builder
from actors.executors import TASK_AGENTS_REGISTRY
from actors.manager import TaskManager
from actors.planner import planner, re_planner
from core.config import RESULTS_STORAGE_PATH
from core.models import Context, Plan
from core.utils import load_task_config, log_done, log_info
from mcps import get_mcp_blackboard_server_params, get_result


async def add_mcp_server(agent: Agent, server: MCPServerSse):
    """
    Add a MCP server to the agent.

    Args:
        agent (Agent): The agent to which the server will be added.
        server (MCPServerSse): The MCP server to be added.
    """
    if not agent.mcp_servers:
        agent.mcp_servers = []
    agent.mcp_servers.append(server)


async def add_mcp_server_to_all_agents(server: MCPServerSse):
    """
    Add a MCP server to all agents in the TASK_AGENTS_REGISTRY.

    Args:
        server (MCPServerSse): The MCP server to be added.
    """

    await add_mcp_server(planner, server)
    await add_mcp_server(re_planner, server)
    await add_mcp_server(context_builder, server)
    for _, agent in TASK_AGENTS_REGISTRY.items():
        await add_mcp_server(agent, server)
    log_done("Agents updated with MCP server for blackboard...")


async def build_context(
    plan_id: str, agent: Agent, context_input: str | list | dict
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
    elif isinstance(context_input, list):
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
    plan_id: str, plan: Plan, revisions: int = 3, server: MCPServerSse | None = None
) -> Plan:
    """
    Execute the plan using the task manager and replan if needed.

    Args:
        plan_id (str): The unique identifier for the plan.
        plan (Plan): The plan object with the steps for the task.
        revisions (int): The number of revisions to perform if needed.
        server (MCPServerSse | None): The MCP server to fetch the output from.
            Defaults to None.

    Returns:
        Plan: The revised plan object after executing the task.
    """

    revised_plan = plan
    for rev in range(1, revisions + 1):
        name = f"Plan Executor - Rev {rev}"
        data = {"Revision": rev, "Plan ID": plan_id}
        with custom_span(name=name, data=data):
            tasks = TaskManager(revised_plan, server=server)
            score = await tasks.run()
            if score.score == "pass":
                break
        revised_plan = await plan_task(plan_id, re_planner, input)
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

    step = get_last_agent_step("Editor", plan.steps)
    value = await get_result(plan.id, str(step.id), step.agent, server)
    return value


async def save_result(plan: Plan, server: MCPServerSse):
    """
    Save the result of the plan to a file.

    Args:
        plan (Plan): The plan object with the steps for the task.
        server (MCPServerSse): The MCP server to fetch the output from.
    """

    RESULTS_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
    file_path = RESULTS_STORAGE_PATH / f"{plan.id}.txt"
    if file_path.exists():
        log_info(f"File {file_path} already exists. Overwriting...")

    result = await fetch_output(plan, server)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(result)
    log_done(f"Result saved to {file_path}")


async def run_agent(
    user_input: str,
    context_input: str | list | dict | None,
    env_file: str = ".env",
    revisions: int = 3,
) -> str:
    """
    Run the agent to perform a task based on user input and context.

    Args:
        user_input (str): The user input for the task.
        context_input (str | list | dict | None): The context input for the task.
        env_file (str): The path to the environment file.
        revisions (int): The number of revisions to perform if needed.
    """

    load_dotenv(env_file, override=True)

    trace_id = gen_trace_id()
    guid = trace_id.split("_")[-1]
    server_params = get_mcp_blackboard_server_params()

    async with MCPServerSse(
        params=server_params,
        cache_tools_list=True,
        name="MCP Blackboard Server",
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
            revised_plan = await execute_plan(guid, plan, revisions, server)

            # Save the result to a file
            await save_result(revised_plan, server)


async def run(task_config_file: str, env_file: str = ".env", revisions: int = 3):
    """
    Main function to run the agent with the provided task configuration.

    Args:
        task_config_file (str): The path to the task configuration file.
        env_file (str): The path to the environment file.
        revisions (int): The number of revisions to perform if needed.
    """
    config = load_task_config(task_config_file)
    user_input = config["goal"]
    context_input = config["context"]
    await run_agent(user_input, context_input, env_file, revisions)
    log_done("Task completed successfully.")
