import asyncio

from agents.mcp import MCPServer

from ferros.core.utils import log_done
from ferros.models.agents import SDKType
from ferros.models.plan import Plan, PlanStep
from ferros.runtime.openai import run as run_openai_agent


class TaskManager:
    def __init__(self, plan: Plan, server: MCPServer):
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
                raise ValueError("Unsupported agent SDK")
        # update the completed steps
        self.plan.steps[step.id - 1].status = "completed"
        self.completed.add(step.id)
        log_done(message)
        return step.id

    async def run(self) -> None:
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
