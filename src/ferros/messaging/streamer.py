from collections.abc import AsyncGenerator
from typing import Any

from rich.console import Console

from ferros.core.logging import get_logger
from ferros.core.utils import get_redis_client
from ferros.messaging.constants import STREAM_LAST_ID, TASK_UPDATE_STREAM


async def stream_task_updates(
    task_id: str, printer: Console | None = None
) -> AsyncGenerator[dict[str, Any], None]:
    """
    Poll the stream for updates.

    Args:
        task_id (str): The ID of the task.

    Raises:
        ValueError: If the stream does not exist.
        KeyboardInterrupt: If the user interrupts the polling.
    """

    last_id: str = STREAM_LAST_ID
    redis = get_redis_client(name="blackboard")
    stream_name = f"{TASK_UPDATE_STREAM}:{task_id}"
    logger = get_logger(__name__)
    logger.info(f"Starting to poll stream: {stream_name}")

    try:
        while True:
            stream = redis.xread({stream_name: last_id}, count=10, block=5000)  # type:ignore
            for _, messages in stream:  # type:ignore
                for message_id, data in messages:  # type:ignore
                    if printer is not None and data:
                        yield data  # type:ignore
                    last_id = message_id  # type:ignore
    except KeyboardInterrupt:
        logger.info("Stream polling stopped by user.")
