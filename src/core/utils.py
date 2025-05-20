import os
from pathlib import Path
from typing import Any

import yaml  # type: ignore
from agents import (
    set_default_openai_api,
    set_default_openai_client,
    set_trace_processors,
    set_tracing_disabled,
)
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


def configure_langfuse_tracing() -> None:
    """
    Configure Langfuse tracing for the application.

    Returns:
        None
    """
    import base64
    import os

    _host = os.environ.get("LANGFUSE_HOST")
    _public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
    _secret_key = os.environ.get("LANGFUSE_SECRET_KEY")

    _langfuse_auth = base64.b64encode(f"{_public_key}:{_secret_key}".encode()).decode(
        "utf-8"
    )

    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = f"{_host}/api/public/otel"
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {_langfuse_auth}"

    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor

    # Create a TracerProvider for OpenTelemetry
    trace_provider = TracerProvider()

    # Add a SimpleSpanProcessor with the OTLPSpanExporter to send traces
    trace_provider.add_span_processor(SimpleSpanProcessor(OTLPSpanExporter()))

    # Set the global default tracer provider
    from opentelemetry import trace

    trace.set_tracer_provider(trace_provider)
    tracer = trace.get_tracer(__name__)  # type: ignore  # noqa: F841

    import nest_asyncio  # type: ignore

    nest_asyncio.apply()  # type: ignore

    import logfire

    logfire.configure(
        send_to_logfire=False,
        service_name="agent-foundry",
        console=False,
        scrubbing=logfire.ScrubbingOptions(),
    )
    logfire.instrument_openai_agents()


def configure_mlflow_tracing() -> None:
    """
    Configure MLflow tracing for the application.

    Returns:
        None
    """
    import mlflow

    mlflow.openai.autolog()  # type: ignore
    mlflow.set_tracking_uri("http://localhost:8080")
    mlflow.set_experiment("OpenAI Agent")


def configure_logfire_tracing() -> None:
    """
    Configure Logfire tracing for the application.

    Returns:
        None
    """
    import logfire

    logfire.configure(
        service_name="agent-foundry",
        service_version="0.1.0",
        environment="sandbox",
        scrubbing=False,
        console=logfire.ConsoleOptions(verbose=False),
        send_to_logfire=False,  # Disable sending to Logfire
        distributed_tracing=False,  # Enable distributed tracing
        token=os.environ.get("LOGFIRE_WRITE_KEY"),
    )
    logfire.instrument_openai_agents()


def configure_custom_tracing() -> None:
    """
    Configure custom tracing for the application.

    Returns:
        None
    """
    pass


def configure_tracing(
    enable: bool = True,
    use_logfire: bool = False,
    use_mlflow: bool = False,
    use_custom: bool = False,
    use_langfuse: bool = False,
) -> None:
    """
    Configure tracing for the application.

    Args:
        enable (bool): Whether to enable tracing.
        use_logfire (bool): Whether to use Logfire for tracing.
        use_mlflow (bool): Whether to use MLflow for tracing.
        use_custom (bool): Whether to use custom tracing.

    Returns:
        None
    """
    if not enable:
        set_tracing_disabled(True)
        return

    set_trace_processors([])
    set_tracing_disabled(False)

    if use_mlflow:
        configure_mlflow_tracing()

    if use_logfire:
        configure_logfire_tracing()

    if use_custom:
        configure_custom_tracing()

    if use_langfuse:
        configure_langfuse_tracing()


def configure_model_client(settings: Settings) -> None:
    """
    Configure the OpenAI client based on the settings.

    Args:
        settings (Settings): The application settings object.

    Returns:
        None
    """
    global client

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
    set_default_openai_client(client, use_for_tracing=False)
    set_default_openai_api("chat_completions")
    configure_tracing(True, use_langfuse=True)


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
