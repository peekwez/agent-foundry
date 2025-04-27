from actors.base import build_agent
from actors.constants import ANALYZER_INSTRUCTIONS

analyzer = build_agent(
    name="Analyzer", instructions=ANALYZER_INSTRUCTIONS, model="o3", task_agent=True
)
