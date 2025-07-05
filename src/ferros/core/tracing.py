import base64
import os

import logfire
import nest_asyncio  # type: ignore
from agents import set_trace_processors, set_tracing_disabled


def configure_langfuse() -> None:
    """
    Configure Langfuse tracing for the application.

    Returns:
        None
    """

    _host = os.environ.get("LANGFUSE_HOST")
    _public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
    _secret_key = os.environ.get("LANGFUSE_SECRET_KEY")

    _langfuse_auth = base64.b64encode(f"{_public_key}:{_secret_key}".encode()).decode(
        "utf-8"
    )

    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = f"{_host}/api/public/otel"
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {_langfuse_auth}"

    nest_asyncio.apply()  # type: ignore

    logfire.configure(
        send_to_logfire=False,
        service_name="agent-foundry",
        console=False,
        # scrubbing=ScrubbingOptions(),
    )
    logfire.instrument_openai_agents()


def configure_logfire() -> None:
    """
    Configure Logfire tracing for the application.

    Returns:
        None
    """

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


def configure_tracing(
    enable: bool = True,
    *,
    use_logfire: bool = False,
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

    if use_logfire:
        configure_logfire()

    if use_langfuse:
        configure_langfuse()
