from agents import ModelSettings
from pydantic import BaseModel, ConfigDict, Field

from ferros.core.utils import load_yaml_j2


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
        config_dict = load_yaml_j2(file_path)
        return cls.model_validate(config_dict)


class ProviderSettings(BaseSettings):
    api_key: str = Field(..., description="API key for the model provider.")
    base_url: str | None = Field(
        default=None, description="Base URL for the model provider."
    )


class RedisSettings(BaseSettings):
    host: str = Field(default="127.0.0.1", description="Host for the Redis server.")
    port: int = Field(default=6381, description="Port for the Redis server.")
    db: int = Field(default=0, description="Database number for Redis.")
    password: str | None = Field(
        default=None, description="Password for the Redis server."
    )


class Etcd3Settings(BaseSettings):
    host: str = Field(default="127.0.0.1", description="Host for the etcd server.")
    port: int = Field(default=2380, description="Port for the etcd server.")
    username: str | None = Field(
        default=None, description="Username for the etcd server."
    )
    password: str | None = Field(
        default=None, description="Password for the etcd server."
    )


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


class Settings(BaseSettings):
    provider: ProviderSettings = Field(
        ..., description="Configuration for the model provider."
    )
    redis: RedisSettings = Field(
        default=RedisSettings(),
        description="Configuration for the Redis server.",
    )
    etcd3: Etcd3Settings = Field(
        default=Etcd3Settings(),
        description="Configuration for the etcd3 server.",
    )
    context: AgentSettings = Field(
        ..., description="Configuration for the context builder agent."
    )
    planner: AgentSettings = Field(
        ..., description="Configuration for the planner agent."
    )
