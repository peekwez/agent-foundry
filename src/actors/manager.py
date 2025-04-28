import asyncio

import rich

from actors.base import get_last_agent_step
from actors.executors import TASK_AGENTS_REGISTRY
from agents import Runner
from agents.mcp import MCPServerSse
from core.models import Plan, PlanStep, Score


class TaskManager:
    def __init__(self, plan: Plan, server: MCPServerSse):
        self.plan = plan
        self.server = server
        self.dependencies = {s.id: set(s.depends_on) for s in plan.steps}
        self.completed = {s.id for s in plan.steps if s.status == "completed"}

    async def _get_plan(self) -> Plan:
        # get the plan from memory
        key = f"plan|{self.plan.id}"
        data = await self.server.call_tool("read_memory", arguments={"key": key})
        plan = Plan.model_validate_json(data.content[0].text)
        return plan

    async def _update_plan(self, plan: Plan):
        # update the plan in memory
        key = f"plan|{self.plan.id}"
        await self.server.call_tool(
            "write_memory",
            arguments={"key": key, "description": "", "value": plan.model_dump_json()},
        )

    async def _run_step(self, step: PlanStep):
        # get the plan from memory
        plan = await self._get_plan()

        # run the step
        message = (
            f"✅ {step.agent} has completed the step: {step.id} of plan: {plan.id}"
        )
        agent = TASK_AGENTS_REGISTRY[step.agent]
        input = f"{step.prompt} \n The plan id is '{plan.id}'"
        await Runner.run(agent, input=input, max_turns=60)

        # update the plan in memory
        plan.steps[step.id - 1].status = "completed"
        await self._update_plan(plan)

        # update the completed steps
        self.completed.add(step.id)
        rich.print(message)
        return step.id

    async def _get_score(self):
        # After all steps are done get the evaluation scores
        # and update the plan status if needed
        plan = await self._get_plan()
        step: PlanStep = get_last_agent_step(agent_name="Evaluator", steps=plan.steps)

        key = f"result|{self.plan.id}|{step.agent}|{step.id}".lower()
        data = await self.server.call_tool(
            tool_name="read_memory", arguments={"key": key}
        )
        value = data.content[0].text

        if not value:
            raise ValueError("No evaluation scores exists")

        score = Score.model_validate_json(value)
        return score

    async def run(self):
        pending = {s.id: s for s in self.plan.steps if s.status == "pending"}
        while pending:
            ready = [
                s for s in pending.values() if self.dependencies[s.id] <= self.completed
            ]
            if not ready:
                raise RuntimeError("Circular dependency detected!")

            done = await asyncio.gather(*(self._run_step(s) for s in ready))
            for sid in done:
                pending.pop(sid, None)

        # Get the evaluation score
        score = await self._get_score()
        return score
