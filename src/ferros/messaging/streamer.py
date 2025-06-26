from collections.abc import AsyncGenerator
from typing import Any

from ferros.core.logging import get_logger
from ferros.core.utils import get_redis_client
from ferros.messaging.constants import STREAM_LAST_ID, TASK_UPDATE_STREAM


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
    import time

    logger = get_logger(__name__)
    async for update in stream_task_updates(task_id):
        logger.info(f"Update for task {task_id}: {update}")
        time.sleep(2)
