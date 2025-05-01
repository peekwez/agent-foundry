from actors.base import build_agent
from core.models import Context

instructions = """
You create descriptions for the context items available for completing
a task.

Given a list of file paths or URLs you create a concise description
for the media based on the contents.

The following tools are available to you:
- `read_context`: Fetches the contents of the context items.
- `save_context_description`: Stores the description for each item.

You must fetch the contents of the context items using the `read_context`
tool to generate the descriptions. You should not include irrelevant
information or details that are not necessary for completing the task.

You must store the description for each item using the using the 
`save_context_description` tool.
"""

context_builder = build_agent(
    name="Context Builder",
    instructions=instructions,
    model="gpt-4o",
    output_type=Context,
)
