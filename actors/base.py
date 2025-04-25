import json
from typing import List, Optional
from agents import Agent, function_tool, ModelSettings

from memory.redis_memory import RedisMemory
from core.config import OPENAI_MODEL

_memory = RedisMemory()


# shared tools
@function_tool(name_override="ReadMemory", docstring_style="google")
def read_memory(key: str) -> str | None:
    """
    Fetch a JSON-serializable value from shared Redis.

    Args:
        key (str): The key to fetch from Redis.

    Returns:
        str | None: The value associated with the key, or None if not found.

    """

    return _memory.get(key.lower())


@function_tool(name_override="WriteMemory", docstring_style="google")
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

    def update_blackboard(key: str, description: str):
        """
        Update the blackboard with a new key and description.

        Args:
            key (str): The key to add to the blackboard.
            description (str): A description of the value being written.
        """
        board = _memory.get("blackboard")
        if board is None:
            board = "{}"
        value = {key: description}
        board = json.loads(board)
        board.update(value)
        _memory.set("blackboard", json.dumps(board))

    update_blackboard(key.lower(), description)
    _memory.set(key.lower(), value)
    return "ok"


DEFAULT_TOOLS = [read_memory, write_memory]

PROMPT_SUFFIX = """
\nYou have access to the following default tools:

1. ReadMemory: Fetch a JSON-serializable value from shared memory.
2. WriteMemory: Write a JSON-serializable value to shared memory.

Use these tools to store and retrieve results related to your tasks.

First fetch the plan (i.e., use 'plan:<plan id>' key) from memory to know what steps are 
available and what dependencies exist. You can use the plan to further understand
your role in the task.

Next fetch the memory metadata (i.e. use key 'blackboard:<plan id>') from memory to 
know what data exists in memory based on work done by other agents. The blackboard 
contains the keys and description of the data stored. This will help you 
decide which data to use for your task.

Fetch the relevant data from memory to use as input for your task. You can use the
'ReadMemory' tool to do this. The key format is 'result:<plan id>:<agent name>:<step id>'.

When you have completed your task, use the 'WriteMemory' tool to store the 
result. Always write the result of your task to memory using the key format 
'result:<plan id>:<agent name>:<step id>' based on the plan.

Respond with 'Agent has updated the blackboard and memory for plan: <plan id> 
and step: <step id>'.

Do not use any other plan id or step id other than the one provided in the input
and stored in context fetched from memory.


"""


def build_agent(
    name: str,
    instructions: str,
    extra_tools: Optional[List] = None,
    **kwargs,
):
    tools = (
        DEFAULT_TOOLS + (extra_tools or []) if "Planner" not in name else [read_memory]
    )

    model_name = kwargs.pop("model", OPENAI_MODEL)
    instructions = (
        instructions + PROMPT_SUFFIX if "Planner" not in name else instructions
    )
    return Agent(
        name=name,
        model=model_name,
        instructions=instructions,
        tools=tools,
        tool_use_behavior="run_llm_again",
        model_settings=ModelSettings(tool_choice="required"),
        **kwargs,
    )
