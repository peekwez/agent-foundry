from actors.base import build_agent
from actors.constants import EXTRACTOR_INSTRUCTIONS

extractor = build_agent(
    name="Extractor", instructions=EXTRACTOR_INSTRUCTIONS, model="o3", task_agent=True
)
