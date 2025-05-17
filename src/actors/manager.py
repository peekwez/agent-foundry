import asyncio

from agents import Runner
from agents.mcp import MCPServerSse

from actors.base import get_last_agent_step
from actors.executors import TASK_AGENTS_REGISTRY
from core.models import Plan, PlanStep, Score
from core.utils import log_done
from mcps import get_result


class TaskManager:
    def __init__(self, plan: Plan, server: MCPServerSse):
        self.plan = plan
        self.server = server
        self.dependencies = {s.id: set(s.depends_on) for s in plan.steps}
        self.completed = {s.id for s in plan.steps if s.status == "completed"}

    async def _run_step(self, step: PlanStep):
        # run the step
        message = (
            f"{step.agent} has completed the step {step.id}/{len(self.plan.steps)}"
            f" for plan {self.plan.id[:8]:8s}..."
        )
        agent = TASK_AGENTS_REGISTRY[step.agent]
        input = f"{step.prompt} \n The plan id is '{self.plan.id}'"
        await Runner.run(agent, input=input, max_turns=60)

        # update the completed steps
        self.plan.steps[step.id - 1].status = "completed"
        self.completed.add(step.id)
        log_done(message)
        return step.id

    async def _get_score(self):
        # After all steps are done get the evaluation scores
        # and update the plan status if needed
        step: PlanStep = get_last_agent_step(
            agent_name="Evaluator", steps=self.plan.steps
        )
        data = await get_result(self.plan.id, str(step.id), step.agent, self.server)
        score = None
        if isinstance(data, str):
            score = Score.model_validate_json(data)
        elif isinstance(data, dict):
            score = Score.model_validate(data)

        if score is None:
            raise ValueError("No score found in memory")
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
