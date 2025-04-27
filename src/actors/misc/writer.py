from actors.base import build_agent
from actors.constants import WRITER_INSTRUCTIONS

writer = build_agent(
    name="Writer", instructions=WRITER_INSTRUCTIONS, task_agent=True, model="o3"
)
