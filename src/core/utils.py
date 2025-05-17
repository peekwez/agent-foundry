import os
from pathlib import Path
from typing import Any

import yaml  # type: ignore
from agents import set_default_openai_api, set_default_openai_client
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from openai import AsyncOpenAI, Timeout
from rich.console import Console

from core.models import Settings

FILE_SCHEMES = (
    "file://",
    "s3://",
    "gcs://",
    "abfs://",
    "abfs[s]://",
    "wasb://",
    "blob://",
    "data:",
    "ftp://",
    "ftps://",
    "sftp://",
    "smb://",
    "github://",
)

URL_SCHEMES = (
    "http://",
    "https://",
)


SCHEMES = FILE_SCHEMES + URL_SCHEMES

TEMPLATES_DIR = Path(__file__).parent

console = Console()
settings: None | Settings = None
client: None | AsyncOpenAI = None


def get_settings() -> Settings:
    """
    Get the application settings.

    Returns:
        Settings: The application settings object.
    """
    global settings
    if settings is None:
        raise ValueError("Settings have not been loaded. Call load_settings first.")
    return settings


def configure_model_client(settings: Settings) -> None:
    global client
    client = AsyncOpenAI(
        base_url=settings.provider.base_url,
        api_key=settings.provider.api_key,
        timeout=Timeout(300),
    )
    set_default_openai_client(client, use_for_tracing=True)
    set_default_openai_api("chat_completions")


def load_settings(env_file: str) -> None:
    """
    Load the application settings from a .env file and render the configuration.

    Args:
        env_file (str): The path to the .env file.

    Returns:
        None
    """
    global settings
    load_dotenv(env_file, override=True)

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("config.yaml.j2")

    rendered_yaml: str = template.render(env=os.environ)

    config_dict: dict[str, Any] = yaml.safe_load(rendered_yaml)

    settings = Settings.model_validate(config_dict)
    configure_model_client(settings)


def load_task_config(file_path: str) -> Any:
    """
    Load the task configuration from a YAML file.

    Args:
        file_path (str): The path to the YAML file.

    Returns:
        dict: The loaded task configuration.
    """
    with open(file_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)  # type: ignore

    # Validate the presence of 'goal' field
    if "goal" not in config or not isinstance(config["goal"], str):
        raise ValueError(
            "The configuration must contain a 'goal' field with a literal value."
        )

    # Validate the 'context' field
    if "context" not in config or not isinstance(config["context"], list):
        raise ValueError("The configuration must contain a 'context' field as a list.")

    # Validate each item in the 'context' list
    for item in config["context"]:
        if not any(item.startswith(scheme) for scheme in SCHEMES):
            raise ValueError(
                f"Invalid context item: {item}. Must start with one of {SCHEMES}."
            )

    return config


def log_info(message: str):
    """
    Log a message to the console.

    Args:
        message (str): The message to log.
    """
    console.print({message})


def log_done(message: str):
    """
    Load a completion message to the console.

    Args:
        message (str): The message to log.
    """
    console.print(f"[green]✔[/green] {message}")
