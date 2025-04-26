from actors.base import build_agent
from core.models import Score

evaluator = build_agent(
    name="Evaluator",
    instructions=(
        "You critically assess outputs against requirements. "
        "Save the valid JSON output that meets the output SCHEMA to memory. "
        "The output should have a score 'pass' or 'fail' and a 'feedback' field "
        "explaining the reasoning behind the score. "
    ),
    model="o3",
    task_agent=True,
    output_type=Score,
)
