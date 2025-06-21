import asyncio

from agents.mcp import MCPServerSse

from ferros.agents.utils import get_step
from ferros.core.utils import log_done
from ferros.models.agent import SDKType
from ferros.models.evaluate import Evaluations
from ferros.models.plan import Plan, PlanStep
from ferros.runtime.openai import run as run_openai_agent
from ferros.tools.mcps import get_result


class TaskManager:
    def __init__(self, plan: Plan, server: MCPServerSse):
        self.plan = plan
        self.server = server
        self.dependencies = {s.id: set(s.depends_on) for s in plan.steps}
        self.completed = {s.id for s in plan.steps if s.status == "completed"}

    async def _run_step(self, step: PlanStep) -> int:
        # run the step
        message = (
            f"{step.agent_name.capitalize()} has completed the step "
            f"{step.id}/{len(self.plan.steps)} "
            f"for plan {self.plan.id[:8]:8s}..."
        )
        match step.agent_sdk:
            case SDKType.OPENAI:
                await run_openai_agent(
                    plan_id=self.plan.id, step=step, mcp_servers=[self.server]
                )
            case SDKType.GOOGLE:
                raise NotImplementedError(
                    "Google SDK is not implemented yet for TaskManager"
                )
            case SDKType.PYDANTIC:
                raise NotImplementedError(
                    "PyDantic SDK is not implemented yet for TaskManager"
                )
            case SDKType.LANGGRAPH:
                raise NotImplementedError(
                    "LangGraph SDK is not implemented yet for TaskManager"
                )
            case _:
                raise ValueError(f"Unsupported agent SDK: {step.agent_sdk}")
        # update the completed steps
        self.plan.steps[step.id - 1].status = "completed"
        self.completed.add(step.id)
        log_done(message)
        return step.id

    async def _get_evals(self) -> Evaluations:
        # After all steps are done get the evaluation scores
        # and update the plan status if needed
        # sleep for a while to ensure the score is available
        await asyncio.sleep(5)
        step: PlanStep = get_step(agent_name="Evaluator", steps=self.plan.steps)
        data = await get_result(
            self.plan.id, str(step.id), step.agent_name, self.server
        )
        score = None
        if isinstance(data, str):
            score = Evaluations.model_validate_json(data)
        elif isinstance(data, dict):
            score = Evaluations.model_validate(data)

        if score is None:
            raise ValueError("No score found in memory")
        return score

    async def run(self) -> Evaluations:
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

        # Get the evaluations
        return await self._get_evals()
