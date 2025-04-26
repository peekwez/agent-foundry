import hashlib
import os
import pathlib
from mimetypes import guess_type

from markitdown import MarkItDown
from openai import OpenAI

from agents import function_tool
from core.config import CONTEXT_STORAGE_PATH
from core.validate import validate_context_key

_parsers: dict[str, MarkItDown] | None = None


def get_parser(media_type: str):
    """
    Get the parser for the given media type.

    Args:
        media_type (str): The media type to get the parser for.

    Returns:
        MarkItDown: The parser for the given media type.
    """

    global _parsers
    if _parsers is None:
        _parsers = {
            "base": MarkItDown(enable_plugins=True),
            "imgs": MarkItDown(llm_client=OpenAI(), llm_model="gpt-4o"),
            "pdfs": MarkItDown(
                docintel_endpoint=os.environ["AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"]
            ),
        }
    return _parsers[media_type]


def get_media_type(file_path_or_url: str) -> str:
    """
    Get the media type of the given file path or URL.

    Args:
        file_path_or_url (str): The file path or URL to get the media type for.

    Returns:
        str: The media type of the given file path or URL.
    """

    mime_type, _ = guess_type(file_path_or_url)

    if mime_type is None:
        return "base"

    if mime_type == "application/pdf":
        return "pdfs"
    elif mime_type.startswith("image/"):
        return "imgs"

    return "base"


def _read_context(key: str) -> str:
    """
    Read the context data or contents from a media given they context key.

    Args:
        key (str): The context key to read the data from. The key should
            be in the format "context|{plan_id}|{file_path_or_url}".

    Returns:
        str: The contents of the context data.

    Raises:
        ValueError: If the key is not in the correct format.
    """

    _, file_path_or_url = validate_context_key(key)
    file_prefix = f"{hashlib.md5(key.strip().encode('utf-8')).hexdigest()}.md"
    file_path: pathlib.Path = CONTEXT_STORAGE_PATH / file_prefix
    if file_path.exists():
        with open(file_path) as f:
            return f.read()

    media_type = get_media_type(file_path_or_url)
    parser = get_parser(media_type)
    document = parser.convert(file_path_or_url)
    contents = document.markdown

    with open(file_path, "w") as f:
        f.write(contents)
    return contents


@function_tool(
    name_override="read_context",
    docstring_style="google",
)
def read_context(key: str) -> str:
    """
    Read the context data or contents from a media given they context key.

    Args:
        key (str): The context key to read the data from. The key should
            be in the format "context|{plan_id}|{file_path_or_url}".

    Returns:
        str: The contents of the context data.

    Raises:
        ValueError: If the key is not in the correct format.
    """
    return _read_context(key)


def test_context_parser():
    import json
    import pathlib

    import rich

    cwd = pathlib.Path(__file__).parent
    with open(cwd.parent.parent / "data/samples/info.json") as f:
        data = json.load(f)

    plan_id = "511f41e962d54268b3915577240c4aec"
    for file in data["files"]:
        key = f"context|{plan_id.strip()}|{file.strip()}"
        output = _read_context(key)
        rich.print(f"File Path or URL: {file}")
        rich.print(output[:100])
        print("\n")


if __name__ == "__main__":
    test_context_parser()
