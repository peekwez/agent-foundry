import pathlib

from actors.base import build_agent
from actors.executors import TASK_AGENTS_LIST_PROMPT
from core.models import Plan


PROMPTS_HOME = pathlib.Path(__file__).parent / "prompts"
PLANNER_PROMPT = open(PROMPTS_HOME / "planner.md").read()
RE_PLANNER_PROMPT = open(PROMPTS_HOME / "re_planner.md").read()

planner = build_agent(
    name="Planner",
    instructions=PLANNER_PROMPT.format(agent_list=TASK_AGENTS_LIST_PROMPT),
    output_type=Plan,
)


re_planner = build_agent(
    name="Re-Planner",
    instructions=RE_PLANNER_PROMPT.format(agent_list=TASK_AGENTS_LIST_PROMPT),
    output_type=Plan,
)
