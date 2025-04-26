import pathlib

from actors.base import build_agent
from actors.manager import TASK_AGENTS_LIST
from core.models import Plan
from tools.context_parser import read_context
from tools.redis_memory import read_memory

PROMPTS_HOME = pathlib.Path(__file__).parent / "prompts"
PLANNER_PROMPT = open(PROMPTS_HOME / "planner.md").read()
RE_PLANNER_PROMPT = open(PROMPTS_HOME / "re_planner.md").read()

planner = build_agent(
    name="Planner",
    instructions=PLANNER_PROMPT.format(agent_list=TASK_AGENTS_LIST),
    output_type=Plan,
    extra_tools=[read_memory, read_context],
)


re_planner = build_agent(
    name="Re-Planner",
    instructions=RE_PLANNER_PROMPT.format(agent_list=TASK_AGENTS_LIST),
    output_type=Plan,
    extra_tools=[read_memory, read_context],
)
