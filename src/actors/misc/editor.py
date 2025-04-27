from actors.base import build_agent
from actors.constants import EDITOR_INSTRUCTIONS

editor = build_agent(
    name="Editor", instructions=EDITOR_INSTRUCTIONS, model="o3", task_agent=True
)
