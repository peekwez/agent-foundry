import json

from redis.typing import ResponseT
from rich.console import Console

from ferros.core.utils import get_redis_client, get_settings

STREAM_LAST_ID = "0-0"


async def get_stream(plan_id: str, stream_id: str = "0-0") -> ResponseT:
    """
    Get the stream key for a given plan ID.

    Args:
        plan_id (str): The ID of the plan.

    Returns:
        str: The stream key for the plan.
    """
    stream_key = f"task-updates:{plan_id}"
    redis_client = get_redis_client()
    # if not redis_client.exists(stream_key):
    #     raise ValueError(f"Stream with key '{stream_key}' does not exist.")
    return redis_client.xread({stream_key: stream_id}, count=10, block=5000)


async def stream_updates(plan_id: str, printer: Console | None = None) -> None:
    """
    Poll the stream for updates.

    Args:
        plan_id (str): The ID of the plan.

    Raises:
        ValueError: If the stream does not exist.
        KeyboardInterrupt: If the user interrupts the polling.
    """

    last_id: str = STREAM_LAST_ID

    try:
        while True:
            entries = await get_stream(plan_id, last_id)  # type:ignore
            for _, messages in entries:  # type:ignore
                for message_id, data in messages:  # type:ignore
                    if printer is not None and data:
                        printer.log(f"Message ID: {message_id}, Data: {data}.")

                    if isinstance(message_id, bytes):
                        message_id = message_id.decode("utf-8")

                    if isinstance(data, bytes):
                        data = data.decode("utf-8")

                    last_id = (  # type:ignore
                        message_id
                        if isinstance(message_id, str)
                        else message_id.decode("utf-8")  # type:ignore
                    )
    except KeyboardInterrupt:
        print("Stream polling stopped by user.")


if __name__ == "__main__":
    from pathlib import Path

    from core.utils import get_redis_client, get_settings, load_settings
    from rich import console as screen

    console = screen.Console()
    path = Path(__file__).parents[2] / ".env.agent"
    print("Loading settings from:", path.as_posix())
    load_settings(path.as_posix())
    settings = get_settings()
    redis_client = get_redis_client()
    import time

    stream_key = "task-updates:65710c2eccda4e9d8898c50816c5d601"
    stream_key = "task-updates:35d95ebc791f4577b868fb720d76d004"  # Example stream key
    entries = redis_client.xread({stream_key: "0-0"}, count=100, block=5000)
    console.log(f"Entries from stream '{stream_key}':")
    for stream, messages in entries:  # type:ignore
        console.log(f"Stream: {stream}")
        for pk, data in messages:  # type:ignore
            console.log(f"Message ID: {pk}, Data: {data}.")
            console.log(f"Message Data: {json.loads(data[b'data'])}")  # type:ignore
            time.sleep(2)
