# type: ignore
import asyncio

import click


@click.group()
def cli() -> None:
    """
    Command-line interface for running the agent with the provided task configuration.
    """
    pass


@cli.command()
@click.option(
    "-c",
    "--task-config-file",
    type=click.Path(exists=True),
    required=True,
    help="Path to the task configuration file.",
)
@click.option(
    "-e",
    "--env-file",
    type=click.Path(exists=True),
    default=".env",
    help="Path to the environment file.",
)
@click.option(
    "-r",
    "--revisions",
    type=int,
    default=3,
    help="Number of revisions to perform if needed.",
)
def run_task(task_config_file: str, env_file: str, revisions: int) -> None:
    """
    Run the agent with the provided task configuration.

    Args:
        task_config_file (str): The path to the task configuration file.
        env_file (str): The path to the environment file.
        revisions (int): The number of revisions to perform if needed.

    Raises:
        FileNotFoundError: If the task configuration file does not exist.

    Returns:
        None
    """
    from ferros.core.utils import load_settings
    from ferros.main import run

    load_settings(env_file)

    asyncio.run(run(task_config_file, revisions))


@cli.command()
@click.option(
    "-s",
    "--sdk",
    type=click.Choice(
        ["openai", "google", "pydantic", "langgraph"], case_sensitive=False
    ),
    required=True,
    help="Name of the agent SDK to add.",
)
@click.option(
    "-c",
    "--config-file",
    type=click.Path(exists=True),
    required=True,
    help="Path to the agent configuration file.",
)
@click.option(
    "-e",
    "--env-file",
    type=click.Path(exists=True),
    default="../.env",
    help="Path to the environment file.",
)
def add_agent(sdk: str, config_file: str, env_file: str) -> None:
    """
    Add a new agent configuration.

    Args:
        sdk (str): The name of the agent SDK to add
            (openai, google, pydantic, langgraph).
        config_file (str): The path to the agent configuration file.
        env_file (str): The path to the environment file.

    Raises:
        FileNotFoundError: If the configuration file does not exist.

    Returns:
        None
    """
    from ferros.agents.factory import register_agent
    from ferros.core.utils import load_settings
    from ferros.models.agents import SDKType

    load_settings(env_file)

    register_agent(SDKType(sdk), config_file)


@cli.command()
@click.option(
    "-e",
    "--env-file",
    type=click.Path(exists=True),
    default="../.env",
    help="Path to the environment file.",
)
def list_agents(env_file: str) -> None:
    """
    List all registered agents.

    Returns:
        None
    """
    from ferros.agents.registry import get_registry
    from ferros.core.utils import load_settings

    load_settings(env_file)

    registry = get_registry()
    configs = registry.list()
    for config in configs.agents:
        print(f"Name: {config.name}, SDK: {config.sdk}, Version: {config.version}")


if __name__ == "__main__":
    cli()
