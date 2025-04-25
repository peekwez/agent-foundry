import json
import asyncio
from typing import Dict
from agents import Runner

from core.models import Plan, PlanStep, Score
from memory.redis_memory import RedisMemory
from actors.researcher import researcher
from actors.extractor import extractor
from actors.writer import writer
from actors.editor import editor
from actors.evaluator import evaluator
from actors.analyzer import analyzer

AGENT_REGISTRY: Dict[str, object] = {
    "Researcher": researcher,
    "Extractor": extractor,
    "Writer": writer,
    "Editor": editor,
    "Evaluator": evaluator,
    "Analyzer": analyzer,
}


class TaskManager:
    def __init__(self, plan: Plan):
        self.plan = plan
        self.dependencies = {s.id: set(s.depends_on) for s in plan.steps}
        self.completed = set()
        self.mem = RedisMemory()

    async def _run_step(self, step: PlanStep):
        agent = AGENT_REGISTRY[step.agent]
        input = f"{step.prompt} \n The plan id is '{self.plan.id}'"
        result = await Runner.run(agent, input=input, max_turns=10)
        print(f"Step {step.id} complete: {result.final_output}")
        self.completed.add(step.id)
        return step.id

    async def run(self):
        pending = {s.id: s for s in self.plan.steps}
        while pending:
            ready = [
                s for s in pending.values() if self.dependencies[s.id] <= self.completed
            ]
            if not ready:
                raise RuntimeError("Circular dependency detected!")
            done = await asyncio.gather(*(self._run_step(s) for s in ready))
            for sid in done:
                pending.pop(sid, None)

        eval: PlanStep = list(
            sorted(
                (
                    filter(
                        lambda x: x.agent.lower().find("evaluator") > -1,
                        self.plan.steps,
                    )
                )
            )
        )[-1]
        value = self.mem.get(f"result:{eval.agent}:{eval.id}")
        if not value:
            raise ValueError("No evaluation scores exists")
        return Score(**json.loads(value))
