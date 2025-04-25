import os
from mimetypes import guess_type

import rich
from markitdown import MarkItDown
from openai import OpenAI


class ContextParser:
    def __init__(self):
        self._clients: dict[str, MarkItDown] = {
            "generic": MarkItDown(enable_plugins=True),
            "images": MarkItDown(llm_client=OpenAI(), llm_model="gpt-4o"),
            "pdfs": MarkItDown(
                docintel_endpoint=os.environ["AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"]
            ),
        }

    def parse_file_or_url(self, file_path_or_url: str) -> str:
        """
        Parse a file or URL and return its content as text.

        Args:
            file_path_or_url (str): The path or URL of the file to parse.

        Returns:
            str: The parsed text content of the file.
        """
        # Read the file content
        mime_type, _ = guess_type(file_path_or_url)
        key = "generic"
        if mime_type is None:
            key = "generic"
        elif mime_type == "application/pdf":
            key = "pdfs"
        elif mime_type.startswith("image/"):
            key = "images"

        client = self._clients[key]
        document = client.convert(file_path_or_url)
        return document.text_content


def test_context_parser():
    import json
    import pathlib

    parser = ContextParser()
    cwd = pathlib.Path(__file__).parent
    with open(cwd.parent.parent / "data/samples/info.json") as f:
        data = json.load(f)

    for file in data["files"]:
        output = parser.parse_file_or_url(file)
        rich.print(f"File Path or URL: {file}")
        rich.print(output[:100])
        print("\n")
