import os

from agents import set_trace_processors, set_tracing_disabled


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
        scrubbing=False,
    )
    logfire.instrument_openai_agents()


def configure_mlflow_tracing() -> None:
    """
    Configure MLflow tracing for the application.

    Returns:
        None
    """
    import mlflow

    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI", "http://0.0.0.0:5000")
    mlflow.openai.autolog()  # type: ignore
    mlflow.set_tracking_uri(tracking_uri)  # type: ignore
    mlflow.set_experiment("OpenAI Agent")  # type: ignore


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
