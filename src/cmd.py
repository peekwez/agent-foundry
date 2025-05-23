import asyncio

import click

from main import run


@click.group()
def cli():
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
def run_task(task_config_file, env_file, revisions):
    """
    Run the agent with the provided task configuration.

    Args:
        task_config_file (str): The path to the task configuration file.
        env_file (str): The path to the environment file.
        revisions (int): The number of revisions to perform if needed.
    """
    asyncio.run(run(task_config_file, env_file, revisions))


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
def test_task(option, env_file):
    """
    Run the specified test task.

    Args:
        option (str): The test to run ('mortgage' or 'research').
        env_file (str): The path to the environment file.
    """
    from pathlib import Path

    task_config_file = Path(__file__).parent.parent / f"samples/{option}/_task.yaml"
    asyncio.run(run(task_config_file, env_file=".env", revisions=3))


if __name__ == "__main__":
    cli()
