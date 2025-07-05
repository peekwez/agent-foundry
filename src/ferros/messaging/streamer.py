import json
import time
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rich.align import Align
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from ferros.agents.utils import get_step
from ferros.core.logging import get_logger
from ferros.core.utils import get_redis_client
from ferros.messaging.constants import STREAM_LAST_ID, TASK_UPDATE_STREAM
from ferros.models.plan import Plan


@dataclass
class TaskResult:
    plan: Plan | None = None
    results: dict[int, Any] = field(default_factory=lambda: {})
    is_completed: bool = False
    streams: list[dict[str, Any]] = field(default_factory=lambda: [])


async def stream_task_updates(task_id: str) -> AsyncGenerator[dict[str, Any], None]:
    """
    Poll the stream for updates.

    Args:
        task_id (str): The ID of the task.

    Raises:
        ValueError: If the stream does not exist.
        KeyboardInterrupt: If the user interrupts the polling.
    """

    last_id: str = STREAM_LAST_ID
    logger = get_logger(__name__)

    redis = get_redis_client(name="blackboard")
    stream_name = f"{TASK_UPDATE_STREAM}:{task_id}"
    logger.info(f"Starting to poll stream: {stream_name} @ {last_id}")

    try:
        while True:
            response = redis.xread({stream_name: last_id}, count=10, block=5000)  # type:ignore
            for _, messages in response:  # type:ignore
                for message_id, message in messages:  # type:ignore
                    try:
                        yield message
                        last_id = message_id  # type:ignore
                    except Exception as e:
                        logger.error(f"Error processing message {message_id}: {e}")
    except Exception as e:
        logger.error(f"Error while polling stream {stream_name}: {e}")
    except KeyboardInterrupt:
        logger.error("Stream polling stopped by user.")


def unwrap_stream_data(stream: dict[str, Any], result: TaskResult) -> TaskResult:
    """
    Unwrap the stream data by removing unnecessary metadata.

    Args:
        stream (dict[str, Any]): The stream data containing the action and data.
        result (TaskResult): The TaskResult object to update with the plan and results.

    Returns:
        TaskResult: The updated TaskResult object with the plan and results.
    """

    result.streams.append(stream)

    # load the raw data from the stream
    raw = stream.get("data", "{}")
    data: dict[str, Any] = json.loads(raw)

    # extract the action and other relevant fields
    action = stream.get("action")
    step_id = data.get("step_id", None)
    status = data.get("status", "")
    agent = data.get("agent_name", "").lower()

    # save the plan
    if action == "save-plan":
        result.plan = Plan.model_validate(data)

    # collect results
    elif action == "save-result" and step_id is not None:
        result.results[int(step_id)] = data.get("result", "")

    # task completed
    elif (
        action == "update-status"
        and status == "completed"
        and agent == "knowledge worker"
    ):
        result.is_completed = True
    return result


def display_task_result(result: TaskResult) -> None:
    """
    Print the task result in a readable format.

    Args:
        result (TaskResult): The TaskResult object containing the plan and results.
    """

    logger = get_logger(__name__)
    if not result.plan:
        return

    step = get_step("editor", result.plan.steps, is_last=True)
    if not step:
        step = get_step("writer", result.plan.steps, is_last=True)

    if not step:
        logger.error("No step found for the editor or writer.")
        return

    if not result.results:
        logger.error("No results found for the task.")
        return

    text = result.results.get(step.id, "")
    console = Console()
    md = Markdown(text)
    max_width = min(console.size.width - 4, 100)
    panel = Panel(
        md,
        width=max_width,
        title=f"Task Result for {result.plan.id}",
        expand=False,
        border_style="dim",
    )
    console.print(Align(panel, align="center"))


def write_streams_to_file(task_id: str, streams: list[dict[str, Any]]) -> None:
    """
    Write the stream data to a file.

    Args:
        task_id (str): The ID of the task.
        streams (list[dict[str, Any]]): The list of stream data to write.

    Raises:
        IOError: If there is an error writing to the file.
    """

    base_dir = Path(__file__).parents[3] / "files"
    if not base_dir.exists():
        base_dir.mkdir(parents=True, exist_ok=True)
    file_path = str(base_dir / f"{task_id}.json")
    with open(file_path, "w") as f:
        data = json.dumps({"task_id": task_id, "streams": streams}, indent=2)
        f.write(data)


async def stream_updates(task_id: str) -> None:
    """
    Stream updates for a specific task and call the provided callback function
    with each update.

    Args:
        task_id (str): The ID of the task.
        callback (Callable[[dict[str, Any]], None]): The callback function to
            call with each update.

    Raises:
        ValueError: If the stream does not exist.
        KeyboardInterrupt: If the user interrupts the streaming.
    """

    logger = get_logger(__name__)
    result = TaskResult()

    async for update in stream_task_updates(task_id):
        time.sleep(1)
        logger.info(f"Update for task {task_id}: {update}")
        unwrap_stream_data(update, result)
        if result.is_completed:
            logger.info(f"Task {task_id} completed.")
            break

    display_task_result(result)
    write_streams_to_file(task_id, result.streams)
