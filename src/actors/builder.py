from agents import Agent

from core.models import Context
from core.utils import get_settings

instructions = """
You create descriptions for the context items available for completing
a task.

Given a list of file paths or URLs you create a concise description
for the media based on the contents.

Fetch each context item using the `read_context` tool and generate a
description based on the contents. You should not include irrelevant
information or details that are not necessary for completing the task.
Then save the description for each item using the `save_context_description`
tool.
"""

settings = get_settings()

context_builder = Agent(
    name="Context Builder",
    model=settings.context_builder.model,
    instructions=instructions,
    model_settings=settings.context_builder.model_settings,
    tool_use_behavior="run_llm_again",
    output_type=Context,
)
