from actors.base import build_agent
from core.models import Score

evaluator = build_agent(
    name="Evaluator",
    instructions=(
        "You critically assess outputs against requirements. "
        "Your final output should meet the provided output SCHEMA. "
        "The output saved to the memory should also be in the SCHEMA format."
    ),
    model="o3",
    output_type=Score,
)
