import asyncio

import rich

from actors.analyzer import analyzer
from actors.editor import editor
from actors.evaluator import evaluator
from actors.extractor import extractor
from actors.researcher import researcher
from actors.writer import writer
from agents import Agent, Runner
from core.models import Plan, PlanStep, Score
from tools.redis_memory import get_memory


def get_agent_info(name, agent: Agent):
    instructions = agent.instructions.split("## Instructions")[0]
    start = instructions.find("\n")
    line = f"> Agent: {name.strip()}\n"
    line += f"> Agent Instructions: {instructions[start:].strip()}"
    return f"{line}\n---"


TASK_AGENTS_REGISTRY: dict[str, Agent] = {
    "Researcher": researcher,
    "Extractor": extractor,
    "Analyzer": analyzer,
    "Writer": writer,
    "Editor": editor,
    "Evaluator": evaluator,
}

TASK_AGENTS_LIST: str = "\n".join(
    [get_agent_info(name, agent) for name, agent in TASK_AGENTS_REGISTRY.items()]
)


class TaskManager:
    def __init__(self, plan: Plan):
        self.plan = plan
        self.dependencies = {s.id: set(s.depends_on) for s in plan.steps}
        self.completed = {s.id for s in plan.steps if s.status == "completed"}
        self.mem = get_memory()

    async def _run_step(self, step: PlanStep):
        # get the plan from memory
        key = f"plan|{self.plan.id}"
        data = self.mem.get(key)
        plan = Plan.model_validate_json(data)

        # run the step
        message = (
            f"✅ {step.agent} has completed the step: {step.id} of plan: {plan.id}"
        )
        agent = TASK_AGENTS_REGISTRY[step.agent]
        input = f"{step.prompt} \n The plan id is '{plan.id}'"
        await Runner.run(agent, input=input, max_turns=60)

        # update the plan in memory
        plan.steps[step.id - 1].status = "completed"
        self.mem.set(key, value=plan.model_dump_json())

        # update the completed steps
        self.completed.add(step.id)
        rich.print(message)
        return step.id

    async def _get_score(self):
        # After all steps are done get the evaluation scores
        # and update the plan status if needed
        key = f"plan|{self.plan.id}"
        data = self.mem.get(key)
        plan = Plan.model_validate_json(data)
        eval: PlanStep = sorted(
            filter(
                lambda x: x.agent.lower().find("evaluator") > -1,
                plan.steps,
            )
        ).pop()

        key = f"result|{self.plan.id}|{eval.agent}|{eval.id}".lower()
        value = self.mem.get(key)

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
