from actors.base import build_agent
from core.models import Context
from tools.context_parser import read_context

context_builder = build_agent(
    name="Context Builder",
    instructions=(
        "You build descriptions for the context items available for completing a task. "
        "Given a list of file paths or URLs you create a concise description of the "
        "context item based on the task to be completed."
    ),
    model="o3",
    output_type=Context,
    extra_tools=[read_context],
)
