import asyncio

import rich
from dotenv import load_dotenv

from actors.manager import TaskManager
from actors.planner import planner, re_planner
from actors.context_builder import context_builder
from agents import Agent, Runner, custom_span, gen_trace_id, trace
from core.models import Plan, PlanStep, Context
from memory.redis_memory import RedisMemory


async def build_context(guid: str, agent: Agent, input: str) -> Context:
    context_result = await Runner.run(agent, input=input, max_turns=20)
    context: Context = context_result.final_output
    rich.print(f">> CONTEXT \n {context}")
    return context


async def plan_task(guid: str, agent: Agent, input: str) -> Plan:
    plan_result = await Runner.run(agent, input=input, max_turns=8)
    plan: Plan = plan_result.final_output
    RedisMemory().set(f"plan:{guid}", plan.model_dump_json(indent=2))
    rich.print(f">> PLAN \n {plan}")
    return plan


async def fetch_output(plan: Plan):
    mem = RedisMemory()
    editor: PlanStep = sorted(
        filter(lambda x: x.agent.lower().find("editor") > -1, plan.steps)
    )[-1]
    value = mem.get(f"result:{plan.id}:{editor.agent}:{editor.id}".lower())
    if not value:
        raise ValueError("No result found in memory")
    return value


async def run_agent(input: str, context_input: str | None) -> str:
    trace_id = gen_trace_id()
    guid = trace_id.split("_")[-1]

    with trace(
        workflow_name=f"DAG Writer Agent: {guid.upper()[:8]}", trace_id=trace_id
    ):
        if context_input:
            context_input = (
                f"{context_input}\n\nUse the given UUID: {guid} for the plan id"
            )
            context = await build_context(guid, context_builder, context_input)

        input = f"{input}\n\nUse the given UUID: {guid} for the plan id"
        plan = await plan_task(guid, planner, input)

        breakpoint()

        # Execute tasks
        for i in range(3):
            with custom_span(
                name=f"Revision: {i + 1}",
                data={
                    "id": guid,
                    "name": "TaskManager",
                    "description": "Executing the plan",
                },
            ):
                tasks = TaskManager(plan)
                score = await tasks.run()

                if score.score == "pass":
                    break

            plan = plan_task(guid, re_planner, input)
            breakpoint()

        result = await fetch_output(plan)
        rich.print(result)


async def main():
    load_dotenv(".env", override=True)

    user_goal = (
        "Create a one-page executive brief on the economic impact of "
        "Canada’s 2024-2025 carbon tax changes. Cite at least three sources."
    )

    context = """
    {
        "files_paths_or_urls": [
            "/Users/kwesi/Downloads/agent_dag_demo/data/samples/us_symbols.csv",
            "/Users/kwesi/Downloads/agent_dag_demo/data/samples/org_chart.png",
            "/Users/kwesi/Downloads/agent_dag_demo/data/samples/white_paper.pdf",
            "http://goldfinger.utias.utoronto.ca/dwz/",
            "https://www.youtube.com/watch?v=yYALsys-P_w"
        ]
    }
"""

    await run_agent(user_goal, context)


if __name__ == "__main__":
    asyncio.run(main())
