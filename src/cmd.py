import click

from main import run, test_mortgage, test_research


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
    default="../samples/mortgage/_task.yaml",
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
    default=0,
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
    run(task_config_file, env_file, revisions)


@cli.command()
@click.option(
    "-o",
    "--option",
    type=click.Choice(["mortgage", "research"], case_sensitive=False),
    required=True,
    help="Specify the test to run: 'mortgage' or 'research'.",
)
def test_task(option):
    """
    Run the specified test task.

    Args:
        option (str): The test to run ('mortgage' or 'research').
    """
    if option == "mortgage":
        test_mortgage()
    elif option == "research":
        test_research()
