import json

from redis import Redis

from agents import function_tool
from core.config import REDIS_URL
from core.validate import validate_memory_key

_memory: Redis | None = None


def get_memory() -> Redis:
    """
    Get the Redis client for shared memory.

    Returns:
        Redis: The Redis client for shared memory.
    """
    global _memory
    if _memory is None:
        _memory = Redis.from_url(REDIS_URL, decode_responses=True)
    return _memory


def _read_memory(key: str) -> str | None:
    """
    Fetch a JSON-serializable value from shared Redis.

    Args:
        key (str): The key to fetch from Redis.

    Returns:
        str | None: The value associated with the key, or None if not found.

    """
    _key = key.lower()
    validate_memory_key(_key)
    mem = get_memory()

    if "blackboard" in _key:
        return json.dumps(mem.hgetall(_key))

    return mem.get(_key)


def _write_memory(key: str, description: str, value: str) -> str:
    """
    Write a JSON-serializable value to shared Redis.

    Args:
        key (str): The key to write to Redis.
        description (str): A description of the value being written.
        value (str): The value to write to Redis.

    Returns:
        str: A confirmation message.
    """

    _key = key.lower()
    plan_id, _, _ = validate_memory_key(_key)
    mem = get_memory()
    mem.hset(f"blackboard|{plan_id}", _key, description)
    mem.set(_key, value)
    return "ok"


@function_tool(name_override="read_memory", docstring_style="google")
def read_memory(key: str) -> str | None:
    """
    Fetch a JSON-serializable value from shared Redis.

    Args:
        key (str): The key to fetch from Redis.

    Returns:
        str | None: The value associated with the key, or None if not found.
    """
    return _read_memory(key)


@function_tool(name_override="write_memory", docstring_style="google")
def write_memory(key: str, description: str, value: str) -> str:
    """
    Write a JSON-serializable value to shared Redis.

    Args:
        key (str): The key to write to Redis.
        description (str): A description of the value being written.
        value (str): The value to write to Redis.

    Returns:
        str: A confirmation message.
    """
    return _write_memory(key, description, value)
