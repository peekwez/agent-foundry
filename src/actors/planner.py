import pathlib

from actors.base import build_agent
from actors.executors import TASK_AGENTS_LIST_PROMPT
from core.models import Plan
from core.utils import get_settings

PROMPTS_HOME = pathlib.Path(__file__).parent / "prompts"
PLANNER_PROMPT = open(PROMPTS_HOME / "planner.md").read()
RE_PLANNER_PROMPT = open(PROMPTS_HOME / "re_planner.md").read()

settings = get_settings()
replanner_agent_settings = settings.planner.model_copy(deep=True)
replanner_agent_settings.name = "Re-Planner"

planner = build_agent(
    settings=settings.planner,
    instructions=PLANNER_PROMPT.format(agent_list=TASK_AGENTS_LIST_PROMPT),
    output_type=Plan,
)


re_planner = build_agent(
    settings=replanner_agent_settings,
    instructions=RE_PLANNER_PROMPT.format(agent_list=TASK_AGENTS_LIST_PROMPT),
    output_type=Plan,
)
