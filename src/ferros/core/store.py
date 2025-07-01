import base64
import mimetypes
from typing import Any, Literal

import httpx
from tenacity import retry, stop_after_attempt, wait_random_exponential

from ferros.core.logging import get_logger
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
    logger = get_logger(__name__)
    encode_data = encode_base64(data, file_name)
    file_path = f"{trace_id}/{file_name}"
    payload = {"file_path": file_path, "data": encode_data}
    url = f"{settings.blackboard.mcp_server}/save-file"
    headers = {"Content-Type": "application/json"}
    response = httpx.put(url, headers=headers, json=payload)
    response.raise_for_status()  # Raise an error for bad responses
    logger.info(f"File {file_name} saved successfully with trace ID {trace_id}.")
    return response.json()  # Return the JSON response if needed


@retry(
    stop=stop_after_attempt(3),
    wait=wait_random_exponential(multiplier=1, max=15),
    reraise=True,
)
async def send_update(
    plan_id: str,
    step_id: int,
    agent_name: str,
    status: Literal["running", "completed", "failed"],
    message: str | None = None,
) -> dict[str, str]:
    """
    Send an action update to the blackboard.

    Args:
        plan_id (str): The ID of the plan.
        step_id (int): The ID of the step.
        agent_name (str): The name of the agent.
        status (Literal["running", "completed", "failed"]): The status of the action

    Returns:
        dict: A confirmation message.
    """
    settings = get_settings()
    logger = get_logger(__name__)
    data: dict[str, Any] = {
        "step": step_id,
        "agent_name": agent_name,
        "status": status,
        "message": message,
    }
    payload: dict[str, Any] = {
        "plan_id": plan_id,
        "action": "update-status",
        "data": data,
    }
    url = f"{settings.blackboard.mcp_server}/send-update"
    headers = {"Content-Type": "application/json"}
    response = httpx.post(url, headers=headers, json=payload)
    response.raise_for_status()  # Raise an error for bad responses
    logger.info(f"Action update sent successfully for plan ID {plan_id}.")
    return response.json()  # Return the JSON response if needed
