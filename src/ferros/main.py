from pathlib import Path

from ferros.agents.runner import run_agent
from ferros.core.logging import get_logger
from ferros.core.utils import load_task_config


async def run(
    task_config_file: str, revisions: int = 3, trace_id: str | None = None
) -> None:
    """
    Main function to run the agent with the provided task configuration.

    Args:
        task_config_file (str): The path to the task configuration file.
        revisions (int): The number of revisions to perform if needed.
        trace_id (str | None): The trace ID for the run. If None, a new
            trace ID will be generated.
    """
    logger = get_logger(__name__)
    _file = Path(task_config_file)
    if not _file.exists():
        logger.error(f"Task configuration file '{task_config_file}' does not exist.")
        raise FileNotFoundError(
            f"Task configuration file '{task_config_file}' does not exist."
        )

    config = load_task_config(task_config_file)
    logger.info(f"Config loaded from {_file.name}.")
    config.revisions = revisions
    config.trace_id = trace_id or config.trace_id
    logger.info(f"Running agent with trace Id: {config.trace_id}.")
    try:
        await run_agent(
            config.goal, config.context_strings, config.revisions, config.trace_id
        )
    except Exception as e:
        logger.exception(f"An error occurred while running the agent: {e}")
    else:
        logger.info("✔ Task completed successfully.")
