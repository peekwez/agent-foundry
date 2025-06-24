import base64
import mimetypes

import httpx
from tenacity import retry, stop_after_attempt, wait_random_exponential

from ferros.core.utils import get_settings


def encode_base64(data: bytes, file_name: str) -> str:
    """
    Encode binary data to a base64 string with a data URL prefix.

    Args:
        data (bytes): The binary data to encode.
        file_name (str): The name of the file to include in the data URL.

    Returns:
        str: A base64 encoded string with a data URL prefix.
    """
    encoded_data = base64.b64encode(data).decode("utf-8")
    mime_type, _ = mimetypes.guess_type(file_name)
    if mime_type is None:
        mime_type = "application/octet-stream"
    return f"data:{mime_type};base64,{encoded_data}"


@retry(
    stop=stop_after_attempt(3),
    wait=wait_random_exponential(multiplier=1, max=15),
    reraise=True,
)
async def save_file(data: bytes, trace_id: str, file_name: str) -> dict[str, str]:
    """
    Save binary data to a file in the specified S3 bucket.

    Args:
        bucket_name (str): The name of the bucket/container to save the file to.
        data (bytes): The binary data to save.
        trace_id (str): The trace ID for the operation.
        file_name (str): The name of the file to save in the S3 bucket.
    """
    settings = get_settings()
    encode_data = encode_base64(data, file_name)
    file_path = f"{trace_id}/{file_name}"
    payload = {"file_path": file_path, "data": encode_data}
    url = f"{settings.blackboard.server}/save-file"
    headers = {"Content-Type": "application/json"}
    response = httpx.put(url, headers=headers, json=payload)
    response.raise_for_status()  # Raise an error for bad responses
    return response.json()  # Return the JSON response if needed


if __name__ == "__main__":
    # Example usage
    import asyncio
    from pathlib import Path

    from ferros.core.utils import load_settings

    env_file = Path(__file__).parents[3] / ".env.agent.local"

    if not env_file.exists():
        raise FileNotFoundError(f"Environment file not found: {env_file}")
    settings = load_settings(str(env_file))
    trace_id = "1234567890abcdef"
    file_name = "example.txt"
    data = b"Hello, world!"

    result = asyncio.run(save_file(data, trace_id, file_name))
    print(result)  # Output the result of the save operation
