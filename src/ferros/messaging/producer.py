from tenacity import retry, stop_after_attempt, wait_random_exponential

from ferros.core.utils import get_redis_client
from ferros.messaging.constants import STREAM_NAME
from ferros.models.task import TaskConfig


@retry(
    stop=stop_after_attempt(3),
    wait=wait_random_exponential(multiplier=1, max=15),
    reraise=True,
)
async def publish_task(task: TaskConfig) -> None:
    """
    Publish a task to the Redis stream for processing by agents.

    Args:
        task (TaskConfig): The task configuration to be published.

    Returns:
        None
    """

    redis = get_redis_client()
    redis.xadd(name=STREAM_NAME, fields={"data": task.model_dump_json()})
