import os
from pathlib import Path
from typing import Any

import etcd3  # type: ignore
import yaml  # type: ignore
from agents import (  # set_trace_processors,; set_tracing_disabled,
    set_default_openai_api,
    set_default_openai_client,
)
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from openai import AsyncOpenAI, Timeout
from redis import Redis
from rich.console import Console

from ferros.core.tracing import configure_tracing
from ferros.models.settings import Settings

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
redis_client: None | Redis = None
etcd_client: None | etcd3.Etcd3Client = None


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


def configure_model_client() -> None:
    """
    Configure the OpenAI client based on the settings.

    Returns:
        None
    """
    global client

    settings = get_settings()

    # Check if we're using the OpenAI API
    using_openai_api = settings.provider.base_url is None or (
        settings.provider.base_url
        and settings.provider.base_url.startswith("https://api.openai.com")
    )

    if using_openai_api:
        import os

        os.environ["OPENAI_API_KEY"] = settings.provider.api_key
        return

    client = AsyncOpenAI(
        base_url=settings.provider.base_url,
        api_key=settings.provider.api_key,
        timeout=Timeout(300),
    )
    set_default_openai_client(client, use_for_tracing=True)
    set_default_openai_api("chat_completions")
    configure_tracing(True, use_langfuse=True)


def load_yaml_j2(file_path: str) -> dict[str, Any]:
    """
    Load a YAML file with Jinja2 templating.

    Args:
        file_path (str): The path to the YAML file.

    Returns:
        dict: The loaded YAML content as a dictionary.
    """
    path = Path(file_path)
    env = Environment(loader=FileSystemLoader(str(path.parent)))
    template = env.get_template(path.name)

    rendered_yaml: str = template.render(env=os.environ)

    return yaml.safe_load(rendered_yaml)


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

    file_path = TEMPLATES_DIR / "config.yaml.j2"
    config_dict = load_yaml_j2(file_path.as_posix())
    settings = Settings.model_validate(config_dict)
    configure_model_client()


def load_task_config(file_path: str) -> Any:
    """
    Load the task configuration from a YAML file.

    Args:
        file_path (str): The path to the YAML file.

    Returns:
        dict: The loaded task configuration.
    """
    with open(file_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

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


def log_info(message: str) -> None:
    """
    Log a message to the console.

    Args:
        message (str): The message to log.
    """
    console.print({message})


def log_done(message: str) -> None:
    """
    Log a completion message to the console.

    Args:
        message (str): The message to log.
    """
    console.print(f"[green]✔[/green] {message}")


def get_redis_client() -> Redis:
    """
    Get the Redis client for shared memory.

    Returns:
        Redis: The Redis client for shared memory.
    """

    global redis_client
    if redis_client is None:
        settings = get_settings()
        if "windows.net" in settings.redis.host:
            cred = DefaultAzureCredential()
            token = cred.get_token("https://redis.azure.com/.default")
            settings.redis.password = token.token
        redis_client = Redis(**settings.redis.model_dump())
    return redis_client


def etcd_watcher(event: Any) -> None:
    print(f"Etcd event: {event}")


def get_etcd_client() -> etcd3.Etcd3Client:
    """
    Get the Etcd client for shared configuration.

    Returns:
        etcd3.Etcd3Client: The Etcd client for shared configuration.
    """
    global etcd_client
    if etcd_client is None:
        settings = get_settings()
        etcd_client = etcd3.client(  # type:ignore
            host=settings.etcd3.host,
            port=settings.etcd3.port,
            user=settings.etcd3.username,
            password=settings.etcd3.password,
        )
        etcd_client.add_watch_callback("/agents/", etcd_watcher)  # type:ignore
    return etcd_client
