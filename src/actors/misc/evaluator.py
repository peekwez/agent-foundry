from actors.base import build_agent
from actors.constants import EVALUATOR_INSTRUCTIONS
from core.models import Score

evaluator = build_agent(
    name="Evaluator",
    instructions=EVALUATOR_INSTRUCTIONS,
    model="o3",
    task_agent=True,
    output_type=Score,
)
