from actors.base import build_agent
from core.models import Context
from tools.context_parser import ContextParser

from agents import function_tool


context_parser = ContextParser()


@function_tool(name_override="ReadContents", docstring_style="google")
def read_contents(file_path_or_url: str) -> str:
    """
    Given a file path or URL, read the contents of the file
    or fetch the content from the URL.
    Args:
        file_path_or_url (str): The file path or URL to read.
    Returns:
        str: The content of the file or URL.
    """

    contents = context_parser.parse_file_or_url(file_path_or_url)
    return contents


context_builder = build_agent(
    name="Context Builder",
    instructions=(
        "You build a context for the task at hand using the provided file paths "
        "or URLs. Given each file path or URL for a context, you create a description "
        "of the context based on the contents and save the FULL contents in memory. "
        "Store the FULL content in the format: context:<plan_id>:file_path_or_url."
    ),
    model="o3",
    output_type=Context,
    extra_tools=[read_contents],
)
