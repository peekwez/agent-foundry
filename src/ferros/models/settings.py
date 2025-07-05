from typing import Literal

from agents import ModelSettings
from pydantic import BaseModel, ConfigDict, Field

from ferros.core.parsers import load_config_file

MB_100 = 104857600  # 100 MB


class BaseSettings(BaseModel):
    @classmethod
    def from_yaml(cls, file_path: str) -> "BaseSettings":
        """
        Load settings from a YAML file.

        Args:
            file_path (str): The path to the YAML file.

        Returns:
            BaseSettings: An instance of the settings class.
        """
        config_dict = load_config_file(file_path)
        return cls.model_validate(config_dict)


class ProviderSettings(BaseSettings):
    api_key: str = Field(..., description="API key for the model provider.")
    base_url: str | None = Field(
        default=None, description="Base URL for the model provider."
    )


class FilesSettings(BaseSettings):
    base_dir: str = Field(
        default="files", description="Base directory for file storage."
    )
    max_size: int = Field(
        default=MB_100, description="Maximum size for uploaded files."
    )
    allowed_extensions: list[str] = Field(
        default=["txt", "csv", "json", "md"],
        description="List of allowed file extensions.",
    )


class RedisSettings(BaseSettings):
    redis_host: str = Field(
        default="127.0.0.1", description="Host for the Redis server."
    )
    redis_port: int = Field(default=6379, description="Port for the Redis server.")
    redis_db: int = Field(default=0, description="Database number for Redis.")
    redis_username: str | None = Field(
        default=None, description="Username for the Redis server."
    )
    redis_password: str | None = Field(
        default=None, description="Password for the Redis server."
    )
    redis_decode_responses: bool = Field(
        default=True, description="Whether to decode Redis responses as strings."
    )


class BlackboardSettings(RedisSettings):
    mcp_server: str = Field(
        default="http://localhost:8000", description="MCP server URL."
    )
    mcp_transport: Literal["sse", "streamable-http"] = Field(
        default="sse",
        description="Transport protocol for the MCP server.",
    )


class RegistrySettings(RedisSettings):
    pass


class AgentSettings(BaseSettings):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    model: str = Field(..., description="The model to be used by the agent.")
    model_settings: ModelSettings = Field(
        default=ModelSettings(
            temperature=None,
            max_tokens=8192,
            tool_choice="required",
        ),
        description="Settings for the model.",
    )


class LoggingSettings(BaseSettings):
    enabled: bool = Field(default=True, description="Enable or disable logging.")
    level: Literal["debug", "info", "warning", "error", "critical"] = Field(
        default="info", description="Logging level."
    )
    root_dir: str = Field(
        default="logs/agent-foundry", description="Root directory for log files."
    )
    rotation: str = Field(default="100 MB", description="Log file rotation size.")
    retention: str = Field(default="30 days", description="Log file retention period.")
    compression: str = Field(default="zip", description="Log file compression format.")


class Settings(BaseSettings):
    provider: ProviderSettings = Field(
        ..., description="Configuration for the model provider."
    )
    files: FilesSettings = Field(
        default=FilesSettings(),
        description="Configuration for file handling and storage.",
    )
    logging: LoggingSettings = Field(
        default=LoggingSettings(),
        description="Configuration for logging settings.",
    )
    blackboard: BlackboardSettings = Field(
        default=BlackboardSettings(),
        description="Configuration for the blackboard service.",
    )
    registry: RegistrySettings = Field(
        default=RegistrySettings(),
        description="Configuration for the registry service.",
    )
    context: AgentSettings = Field(
        ..., description="Configuration for the context builder agent."
    )
    planner: AgentSettings = Field(
        ..., description="Configuration for the planner agent."
    )
    evaluator: AgentSettings = Field(
        ..., description="Configuration for the evaluator agent."
    )
