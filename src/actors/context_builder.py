from actors.base import build_agent
from core.models import Context
from tools.context_parser import ContextParser
from memory.redis_memory import RedisMemory

from agents import function_tool


_context_parser = ContextParser()
_memory = RedisMemory()


@function_tool(name_override="ReadContents", docstring_style="google")
def read_contents(plan_id: str, file_path_or_url: str) -> str:
    """
    Given a file path or URL, read the contents of the file,
    or fetch the content from the URL, save it in memory,
    and return the content.

    Args:
        plan_id (str): The plan ID to associate with the content.
        file_path_or_url (str): The file path or URL to read.

    Returns:
        str: The content of the file or URL.
    """
    key = f"context:{plan_id}:{file_path_or_url}"
    contents = _context_parser.parse_file_or_url(file_path_or_url)
    if contents:
        _memory.set(key, contents)
    return contents


context_builder = build_agent(
    name="Context Builder",
    instructions=(
        "You build descriptions for the context items to be used for the task "
        "given the file paths or URLs. Given each file path or URL for a context, "
        "you create a concise description of the context based on the contents to "
        "other agents to understand how to use the context."
    ),
    model="o3",
    output_type=Context,
    extra_tools=[read_contents],
)
