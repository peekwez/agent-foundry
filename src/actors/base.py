import json
import uuid
import warnings

from agents import Agent, ModelSettings, function_tool
from core.config import OPENAI_MODEL
from memory.redis_memory import RedisMemory

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
        plan_id = key.lower().split(":")[1]

        # Validate that plan_id is a valid UUID
        try:
            uuid.UUID(plan_id)
        except ValueError:
            message = (
                f"Invalid plan ID: {plan_id}. Must be a valid UUID."
                "Every value in memory must be stored with a plan id."
            )
            warnings.warn(message, UserWarning, stacklevel=2)
            return message

        board = _memory.get(f"blackboard:{plan_id}")
        if board is None:
            board = "{}"
        board = json.loads(board)
        board.update({key: description})
        _memory.set(f"blackboard:{plan_id}", json.dumps(board, indent=2))

    update_blackboard(key.lower(), description)
    _memory.set(key.lower(), value)
    return "ok"


DEFAULT_TOOLS = [read_memory, write_memory]

PROMPT_SUFFIX = (
    "\n\nYou have access to the following default tools:\n\n"
    "1. ReadMemory: Fetch a JSON-serializable value from shared memory.\n"
    "2. WriteMemory: Write a JSON-serializable value to shared memory.\n\n"
    "Use these tools to store and retrieve results related to your tasks.\n\n"
    "First fetch the plan (i.e., use 'plan:<plan id>' key) from memory \n"
    "to know what steps are available and what dependencies exist. You \n"
    "can use the plan to further understand your role in the task.\n\n"
    "Next fetch the memory metadata (i.e. use key 'blackboard:<plan id>') \n"
    "from memory to know what data exists in memory based on work done by \n"
    "other agents. The blackboard contains the keys and description of the \n"
    "data stored. This will help you decide which data to use for your task.\n\n"
    "Fetch the relevant data from memory to use as input for your task. \n"
    "The relevant data can be the results from other agents or a static context \n"
    "from a file store in memory (i.e. use key 'context:<plan id>:<file name>'). \n"
    "You can use the 'ReadMemory' tool to fetch the data. The key format is \n"
    "'result:<plan id>:<agent name>:<step id>' or 'context:<plan id>:<file name>'.\n\n"
    "When you have completed your task, use the 'WriteMemory' tool to store the \n"
    "result. Always write the result of your task to memory using the key format \n"
    "'result:<plan id>:<agent name>:<step id>' based on the plan.\n\n"
    "Respond with 'Agent has updated the blackboard and memory for plan: <plan id> \n"
    "and step: <step id>'.\n\n"
    "Do not use any other plan id or step id other than the one provided in the \n"
    "input and stored in context fetched from memory.\n\n"
)


def get_default_tools(name: str, extra_tools: list | None = None):
    """
    Get the tools for the agent based on its name.
    """
    is_planner = "Planner" in name
    is_builder = "Context Builder" in name
    if is_planner:
        return [read_memory] + (extra_tools or [])
    elif is_builder:
        return extra_tools or []
    else:
        return DEFAULT_TOOLS + (extra_tools or [])


def get_instructions(name: str, instructions: str):
    is_planner = "Planner" in name
    is_builder = "Context Builder" in name
    return instructions if (is_planner or is_builder) else instructions + PROMPT_SUFFIX


def build_agent(
    name: str,
    instructions: str,
    extra_tools: list | None = None,
    **kwargs,
):

    return Agent(
        name=name,
        model=kwargs.pop("model", OPENAI_MODEL),
        instructions=get_instructions(name, instructions),
        tools=get_default_tools(name, extra_tools),
        tool_use_behavior="run_llm_again",
        model_settings=ModelSettings(tool_choice="required"),
        **kwargs,
    )
