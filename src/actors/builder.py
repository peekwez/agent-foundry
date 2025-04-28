from actors.base import build_agent
from core.models import Context

context_builder = build_agent(
    name="Context Builder",
    instructions=(
        "You build descriptions for the context items available for completing a task. "
        "Given a list of file paths or URLs you create a concise description of the "
        "contents of item based on the task to be completed. You must fetch the "
        "contents of the context items using the `read_context` tool to generate the "
        "descriptions. You should not include irrelevant information or details that "
        "are not necessary for completing the task. The key for the context item is "
        "of the form `context|<plan_id>|<file_path_or_url>`."
        "Store the description for each item using the `write_memory` tool. The key "
        "for the context item is of the form `context|<plan_id>|<file_path_or_url>`. "
        "description is the description of the context item and the value should just "
        "an empty string."
    ),
    model="gpt-4o",
    output_type=Context,
)
