import asyncio
import json
import pathlib
import rich
from dotenv import load_dotenv

from actors.builder import context_builder
from actors.manager import TaskManager
from actors.planner import planner, re_planner
from agents import Agent, Runner, custom_span, gen_trace_id, trace
from core.models import Context, Plan, PlanStep
from memory.redis_memory import RedisMemory


_memory = RedisMemory()


async def build_context(
    guid: str, agent: Agent, context_input: str | list | dict
) -> Context:

    if isinstance(context_input, str):
        context_input = context_input.strip()
    elif isinstance(context_input, dict):
        context_input = json.dumps(context_input, indent=2)
    elif isinstance(context_input, list):
        context_input = "\n".join(context_input)
    else:
        raise ValueError("Invalid context input type")

    input = f"{context_input}\n\nUse the given UUID: {guid} for the plan id"
    result = await Runner.run(agent, input=input, max_turns=20)
    context: Context = result.final_output

    blackboard = {}
    for x in context.contexts:
        blackboard.update({f"context:{guid}:{x.file_path_or_url}": x.description})

    _memory.set(f"blackboard:{guid}", json.dumps(blackboard, indent=2))
    size = len(context.contexts)

    rich.print(f">> Context for {size} items built successfully ...")
    return context


async def plan_task(guid: str, agent: Agent, user_input: str) -> Plan:
    input = f"{user_input}\n\nUse the given UUID: {guid} for the plan id"
    result = await Runner.run(agent, input=input, max_turns=8)
    plan: Plan = result.final_output

    _memory.set(f"plan:{guid}", plan.model_dump_json(indent=2))
    size = len(plan.steps)

    if agent.name == "Planner":
        rich.print(f">> Planning for task completed with {size} steps ...")
    elif agent.name == "Re-Planner":
        new_size = len([s for s in plan.steps if s.status == "pending"])
        rich.print(f">> Re-planning for task completed with {new_size} new steps ...")
    return plan


async def execute_plan(guid: str, plan: Plan, revisions: int = 3) -> Plan:
    revised_plan = plan
    for i in range(1, revisions + 1):

        with custom_span(
            name=f"Plan Executor - Rev {i}",
            data={
                "id": guid,
                "name": "Plan Executor",
                "description": "Executing the plan for the task",
            },
        ):
            tasks = TaskManager(revised_plan)
            score = await tasks.run()

            if score.score == "pass":
                break

        revised_plan = plan_task(guid, re_planner, input)

    return revised_plan


async def fetch_output(plan: Plan):
    mem = RedisMemory()
    editor: PlanStep = sorted(
        filter(lambda x: x.agent.lower().find("editor") > -1, plan.steps)
    )[-1]
    value = mem.get(f"result:{plan.id}:{editor.agent}:{editor.id}".lower())
    if not value:
        raise ValueError("No result found in memory")
    return value


async def save_result(plan: Plan):
    path = pathlib.Path(__file__).parent.parent / "results"
    path.mkdir(parents=True, exist_ok=True)
    file_path = path / f"{plan.id}.md"
    if file_path.exists():
        rich.print(f"File {file_path} already exists. Overwriting...")

    result = await fetch_output(plan)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(result)
    rich.print(f"Result saved to results/{plan.id}.md")


async def run_agent(
    user_input: str,
    context_input: str | list | dict | None,
    env_file: str = ".env",
    revisions: int = 3,
) -> str:

    load_dotenv(env_file, override=True)

    trace_id = gen_trace_id()
    guid = trace_id.split("_")[-1]

    with trace(
        workflow_name=f"DAG Writer Agent: {guid.upper()[:8]}", trace_id=trace_id
    ):
        # Build context
        if context_input:
            await build_context(guid, context_builder, context_input)

        # Plan the task
        plan = await plan_task(guid, planner, user_input)

        # Execute the plan, replan if needed and revise output
        revised_plan = await execute_plan(guid, plan, revisions)

        # Save the result to a file
        await save_result(revised_plan)


async def test_research():
    user_goal = (
        "Create a one-page executive brief on the economic impact of "
        "Canada’s 2024-2025 carbon tax changes. Cite at least three sources."
    )

    context = {
        "files_paths_or_urls": [
            "/Users/kwesi/Downloads/agent_dag_demo/data/samples/us_symbols.csv",
            "/Users/kwesi/Downloads/agent_dag_demo/data/samples/org_chart.png",
            "/Users/kwesi/Downloads/agent_dag_demo/data/samples/white_paper.pdf",
            "http://goldfinger.utias.utoronto.ca/dwz/",
            "https://www.youtube.com/watch?v=yYALsys-P_w",
        ]
    }
    await run_agent(user_goal, context)


async def test_mortgage():
    user_goal = (
        "Write a one-page memo presenting the results of the analysis of the"
        "mortgage application for a client. Review the letter of employment, "
        "pay stub and credit information. The letter of employment annual salary "
        "and pay stub amount should not have a variance of more than 5%.\n\n"
        "The credit score should not be less than 650. The client can qualify for a "
        "mortgage amount that is 5 times their annual salary. Make sure the client "
        "name matches on all documents and the employer name is the same on the "
        "letter of employment and pay stub.\n\n"
        "Include the expected down payment amount, the mortgage amount, and "
        "any recommendations for the client. Based on the prevailing interest rates "
        "across 5 Canadian banks, calculate the mortgage amount. Use the average "
        "interest rate across the banks to calculate the mortgage amount. Use "
        "The client should be able to afford the monthly payment amount. "
    )

    context = {
        "files_paths_or_urls": [
            "/Users/kwesi/Downloads/agent_dag_demo/data/mortgage/loe_bomb.png",
            "/Users/kwesi/Downloads/agent_dag_demo/data/mortgage/ps_bomb.png",
            "/Users/kwesi/Downloads/agent_dag_demo/data/mortgage/credit_report.pdf",
            "https://laws-lois.justice.gc.ca/eng/regulations/SOR-2012-281/page-1.html",
        ]
    }
    await run_agent(user_goal, context)


if __name__ == "__main__":

    asyncio.run(test_mortgage())
    # asyncio.run(test_research())
