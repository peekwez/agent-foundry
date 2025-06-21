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

    load_settings(env_file)

    from main import run

    asyncio.run(run(task_config_file, revisions))


@cli.command()
@click.option(
    "-o",
    "--option",
    type=click.Choice(["mortgage", "research"], case_sensitive=False),
    required=True,
    help="Specify the test to run: 'mortgage' or 'research'.",
)
@click.option(
    "-e",
    "--env-file",
    type=click.Path(exists=True),
    default="../.env",
    help="Path to the environment file.",
)
def test_task(option: str, env_file: str) -> None:
    """
    Run the specified test task.

    Args:
        option (str): The test to run ('mortgage' or 'research').
        env_file (str): The path to the environment file.

    Raises:
        FileNotFoundError: If the task configuration file does not exist.

    Returns:
        None
    """
    from pathlib import Path

    from ferros.core.utils import load_settings

    load_settings(env_file)
    from main import run

    task_config_file = Path(__file__).parent.parent / f"samples/{option}/_task.yaml"
    asyncio.run(run(task_config_file.as_posix(), revisions=3))


@click.command()
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
    type=str,
    required=True,
    path=click.Path(exists=True),
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
    from core.utils import load_settings
    from models.agent import SDKType

    load_settings(env_file)

    from agents.factory import register_agent

    register_agent(SDKType(sdk), config_file)


if __name__ == "__main__":
    cli()
