import asyncio

from agents import custom_span
from agents.mcp import MCPServer

from ferros.core.logging import get_logger
from ferros.models.agents import SDKType
from ferros.models.plan import Plan, PlanStep
from ferros.runtime.openai import run as run_openai_agent


class TaskManager:
    def __init__(self, server: MCPServer):
        self.server = server
        self.dependencies: dict[str, set[str]] = {}
        self.completed: set[int] = set()
        self.logger = get_logger(__name__)
        self.logger.info("Task Manager initialized.")

    def set_plan(self, plan: Plan) -> None:
        """Set a new plan for the task manager."""
        self.plan = plan
        self.dependencies = {s.id: set(s.depends_on) for s in plan.steps}
        self.completed = {s.id for s in plan.steps if s.status == "completed"}

    async def run_step(self, step: PlanStep) -> int:
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
        self.logger.info(message)
        return step.id

    async def run(self, plan: Plan, revision: int) -> None:
        self.set_plan(plan)
        pending = {s.id: s for s in self.plan.steps if s.status == "pending"}
        with custom_span("Execution", data={"Plan Id": self.plan.id}):
            self.logger.info(
                f"Executing plan {self.plan.id} with goal: {self.plan.goal[:30]}..."
            )
            while pending:
                ready = [
                    s
                    for s in pending.values()
                    if self.dependencies[s.id] <= self.completed
                ]
                if not ready:
                    self.logger.error(
                        "No steps are ready to run. Circular dependency detected!"
                    )
                    raise RuntimeError("Circular dependency detected!")

                done = await asyncio.gather(*(self.run_step(s) for s in ready))
                for sid in done:
                    pending.pop(sid, None)

            self.logger.info(
                f"Execution of revision {revision} of plan {self.plan.id} completed."
            )
