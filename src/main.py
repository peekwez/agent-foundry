import asyncio
import json

from dotenv import load_dotenv

from actors.manager import TaskManager
from actors.planner import planner, re_planner
from agents import Agent, Runner, custom_span, gen_trace_id, trace
from core.models import Plan, PlanStep
from memory.redis_memory import RedisMemory


async def plan_task(guid: str, agent: Agent, input: str) -> Plan:
    plan_result = await Runner.run(agent, input=input, max_turns=8)
    plan: Plan = plan_result.final_output
    value = json.dumps(plan, default=lambda o: o.__dict__, indent=2)
    RedisMemory().set(f"plan:{guid}", value)
    print("PLAN JSON:", value)
    return plan


async def fetch_output(plan: Plan):
    mem = RedisMemory()
    editor: PlanStep = sorted(
        filter(lambda x: x.agent.lower().find("editor") > -1, plan.steps)
    )[-1]
    value = mem.get(f"result:{plan.id}:{editor.agent}:{editor.id}")
    if not value:
        raise ValueError("No evaluation scores exists")
    return value


async def run_agent(input: str) -> str:
    trace_id = gen_trace_id()
    guid = trace_id.split("_")[-1]

    with trace(
        workflow_name=f"DAG Writer Agent: {guid.upper()[:8]}", trace_id=trace_id
    ):
        input = f"{input}\n\nUse the given UUID: {guid} for the plan id"
        plan = await plan_task(guid, planner, input)

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
        print(result)


async def main():
    load_dotenv(".env", override=True)

    user_goal = (
        "Create a one-page executive brief on the economic impact of "
        "Canada’s 2024-2025 carbon tax changes. Cite at least three sources."
    )

    await run_agent(user_goal)


if __name__ == "__main__":
    asyncio.run(main())
