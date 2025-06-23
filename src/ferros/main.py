from ferros.agents.runner import run_agent
from ferros.core.utils import load_task_config, log_done


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
    config = load_task_config(task_config_file)
    config.revisions = revisions
    config.trace_id = trace_id or config.trace_id
    await run_agent(
        config.goal, config.context_strings, config.revisions, config.trace_id
    )
    log_done("Task completed successfully.")
