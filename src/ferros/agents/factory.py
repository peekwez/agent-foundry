from ferros.agents.registry import get_registry
from ferros.models.agents import SDK_CLASS_MAP, AgentsConfig, AgentSDKConfig, SDKType


def get_agent_config(name: str, sdk: SDKType, version: str) -> AgentSDKConfig:
    """
    Create a new agent with the specified version.

    Args:
        version (str): The version of the agent to be created.

    Returns:
        OpenAISDKConfig: An instance of OpenAISDKConfig with the specified version.
    """
    registry = get_registry()
    return registry.get(name, sdk, version)


def register_agent(sdk: SDKType, file_path: str) -> None:
    """
    Register a new agent in the system.

    Args:
        agent (TaskAgent): The agent to be registered.

    Returns:
        None
    """
    registry = get_registry()
    cls: type[AgentSDKConfig] = SDK_CLASS_MAP.get(sdk, AgentSDKConfig)
    config: AgentSDKConfig = cls.from_yaml(file_path)
    registry.add(config)
    print(f"Registered {config.name} agent for {sdk} SDK and version {config.version}.")


def get_agent_configs() -> AgentsConfig:
    """
    Get all registered agents.

    Returns:
        AgentsConfig: A list of all registered agents.
    """
    registry = get_registry()
    return registry.list()
