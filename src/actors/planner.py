import pathlib

from agents import Agent

from actors.executors import TASK_AGENTS_LIST_PROMPT
from core.models import Plan
from core.utils import get_settings

PROMPTS_HOME = pathlib.Path(__file__).parent / "prompts"
PLANNER_PROMPT = open(PROMPTS_HOME / "planner.md").read()
RE_PLANNER_PROMPT = open(PROMPTS_HOME / "re_planner.md").read()

settings = get_settings()


planner = Agent(
    name="Planner",
    model=settings.planner.model,
    instructions=PLANNER_PROMPT.format(agent_list=TASK_AGENTS_LIST_PROMPT),
    tool_use_behavior="run_llm_again",
    model_settings=settings.planner.model_settings,
    output_type=Plan,
)


re_planner = Agent(
    name="Re-Planner",
    model=settings.planner.model,
    instructions=RE_PLANNER_PROMPT.format(agent_list=TASK_AGENTS_LIST_PROMPT),
    tool_use_behavior="run_llm_again",
    model_settings=settings.planner.model_settings,
    output_type=Plan,
)
