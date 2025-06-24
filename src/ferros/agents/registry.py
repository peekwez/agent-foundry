import json
import threading
from collections.abc import Callable

from redis import Redis
from redis.typing import ChannelT

from ferros.core.utils import get_redis_client
from ferros.models.agents import (
    REGISTRY_PREFIX,
    SDK_CLASS_MAP,
    AgentsConfig,
    AgentSDKConfig,
    SDKType,
    config_key,
)


class RedisAgentRegistry:
    def __init__(self) -> None:
        self.redis: Redis = get_redis_client(name="registry")

    def add(self, config: AgentSDKConfig) -> None:
        """
        Add a new agent configuration to the registry.

        Args:
            config (AgentSDKConfig): The agent configuration to add.

        Raises:
            ValueError: If the agent configuration is invalid.
        """
        data = config.model_dump_json()
        self.redis.set(config.key, data)

        # index for fast lookups
        self.redis.sadd(f"{REGISTRY_PREFIX}:names:{config.name.lower()}", config.key)
        self.redis.sadd(f"{REGISTRY_PREFIX}:sdks:{config.sdk}", config.key)

        # latest version
        self.redis.set(
            f"{REGISTRY_PREFIX}:latest:{config.name.lower()}:{config.sdk.lower()}",
            config.key,
        )
        channel: ChannelT = f"{REGISTRY_PREFIX}:updated".encode()
        message = json.dumps({"key": config.key, "action": "registered"})
        self.redis.publish(channel, message)  # type:ignore

    def get(self, name: str, sdk: SDKType, version: str) -> AgentSDKConfig:
        """
        Get an agent configuration by name, SDK, and version.

        Args:
            name (str): The name of the agent.
            sdk (SDKType): The SDK type of the agent.
            version (str): The version of the agent.

        Returns:
            AgentSDKConfig: The agent configuration.

        Raises:
            KeyError: If the agent configuration is not found.
        """
        key = config_key(name, sdk, version)
        raw: bytes = self.redis.get(key)  # type:ignore
        if not raw:
            raise KeyError(f"Agent config not found: {key}")

        cls: type[AgentSDKConfig] = SDK_CLASS_MAP.get(sdk, AgentSDKConfig)
        return cls.model_validate_json(raw)

    def latest(self, name: str, sdk: SDKType) -> AgentSDKConfig:
        """
        Get the latest agent configuration by name and SDK.

        Args:
            name (str): The name of the agent.
            sdk (SDKType): The SDK type of the agent.

        Returns:
            AgentSDKConfig: The latest agent configuration.

        Raises:
            KeyError: If the latest agent configuration is not found.
        """
        key = f"{REGISTRY_PREFIX}:latest:{name.lower()}:{sdk.lower()}"
        raw: bytes = self.redis.get(key)  # type:ignore
        if not raw:
            raise KeyError(f"Latest agent config not found for {name} with SDK {sdk}")
        cls: type[AgentSDKConfig] = SDK_CLASS_MAP.get(sdk, AgentSDKConfig)
        return cls.model_validate_json(raw)

    def list(
        self, name: str | None = "*", sdk: str | None = "*", version: str | None = "*"
    ) -> AgentsConfig:
        """
        List all agent configurations matching the given name, SDK, and version.

        Args:
            name (str | None): The name of the agent. Defaults to '*' (all names).
            sdk (str | None): The SDK type of the agent. Defaults to '*' (all SDKs).
            version (str | None): The version of the agent. Defaults to '*'
                (all versions).

        Returns:
            AgentsConfig: A collection of agent configurations matching the criteria.
        """
        name = name.lower() if isinstance(name, str) else name
        sdk = sdk.lower() if isinstance(sdk, str) else sdk
        pattern = f"{REGISTRY_PREFIX}:{name or '*'}:{sdk or '*'}:{version or '*'}"
        keys: list[str] = self.redis.scan_iter(pattern, count=100)  # type:ignore
        results: list[AgentSDKConfig] = []
        for key in keys:
            _, _, name, _sdk, version = key.split(":")
            if name == "latest":
                continue
            config = self.get(name, SDKType(_sdk), version)
            results.append(config)
        return AgentsConfig(agents=results)

    def update(self, config: AgentSDKConfig) -> None:
        """
        Update an existing agent configuration in the registry.

        Args:
            config (AgentSDKConfig): The agent configuration to update.

        Raises:
            KeyError: If the agent configuration does not exist.
        """
        self.redis.set(config.key, config.model_dump_json())
        channel: ChannelT = f"{REGISTRY_PREFIX}:updated".encode()
        message = json.dumps({"key": config.key, "action": "updated"})
        self.redis.publish(channel, message)  # type:ignore

    def watch(self, callback: Callable[[AgentSDKConfig], None]) -> None:
        """
        Watch for updates to the agent registry and call the provided callback
        when an agent configuration is added or updated.

        Args:
            callback (Callable[[AgentSDKConfig], None]): The callback function to call
                when an agent configuration is added or updated.

        """

        channel: ChannelT = f"{REGISTRY_PREFIX}:updated".encode()

        def _watch() -> None:
            pubsub = self.redis.pubsub()  # type:ignore
            pubsub.subscribe(channel)  # type:ignore

            for msg in pubsub.listen():  # type:ignore
                if msg["type"] == "message":
                    callback(msg["data"])  # type:ignore

        threading.Thread(target=_watch, daemon=True).start()


registry: None | RedisAgentRegistry = None


def get_registry() -> RedisAgentRegistry:
    """
    Get the global agent registry instance, creating it if it doesn't exist.

    Returns:

        RedisAgentRegistry: The global agent registry instance.
    """
    global registry
    if registry is None:
        registry = RedisAgentRegistry()
    return registry


__all__ = ["get_registry"]
