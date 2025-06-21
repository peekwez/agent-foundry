from ferros.core.utils import get_etcd_client
from ferros.models.agent import (
    GoogleADKConfig,
    LangGraphConfig,
    OpenAISDKConfig,
    PydanticAIConfig,
    SDKType,
)

# def validate_sdk(sdk: SD) -> None:
#     """
#     Validate the SDK configuration.

#     Args:
#         sdk (AgentSDK): The SDK configuration to validate.

#     Raises:
#         ValueError: If the SDK configuration is invalid.
#     """
#     if sdk not in (
#         "openai-sdk",
#         "google-adk",
#         "pydantic-ai",
#         "langchain",
#     ):
#         raise ValueError(
#             f"Invalid SDK: {sdk}. Supported SDKs are: "
#             "openai-sdk, google-adk, pydantic-ai, langchain."
#         )


def get_agent_config(
    name: str, sdk: SDKType, version: str
) -> OpenAISDKConfig | GoogleADKConfig | PydanticAIConfig | LangGraphConfig:
    """
    Create a new agent with the specified version.

    Args:
        version (str): The version of the agent to be created.

    Returns:
        OpenAISDKConfig: An instance of OpenAISDKConfig with the specified version.
    """
    key = f"/agents/{name.lower()}/{sdk.lower()}/{version.lower()}"
    etcd_client = get_etcd_client()  # type: ignore
    data = etcd_client.get(key)  # type: ignore
    match sdk:
        case SDKType.OPENAI:
            return OpenAISDKConfig.model_validate_json(data)  # type: ignore
        case SDKType.GOOGLE:
            return GoogleADKConfig.model_validate_json(data)  # type: ignore
        case SDKType.PYDANTIC:
            return PydanticAIConfig.model_validate_json(data)  # type: ignore
        case SDKType.LANGGRAPH:
            return LangGraphConfig.model_validate_json(data)  # type: ignore
        case _:
            raise ValueError(f"Unsupported SDK: {sdk}")


def register_agent(sdk: SDKType, file_path: str) -> None:
    """
    Register a new agent in the system.

    Args:
        agent (TaskAgent): The agent to be registered.

    Returns:
        None
    """

    match sdk:
        case SDKType.OPENAI:
            # Load the OpenAI SDK configuration from the YAML file
            agent = OpenAISDKConfig.from_yaml(file_path)
        case SDKType.GOOGLE:
            # Load the Google ADK configuration from the YAML file
            agent = GoogleADKConfig.from_yaml(file_path)
        case SDKType.PYDANTIC:
            # Load the Pydantic AI configuration from the YAML file
            agent = PydanticAIConfig.from_yaml(file_path)
        case SDKType.LANGGRAPH:
            # Load the LangGraph configuration from the YAML file
            agent = LangGraphConfig.from_yaml(file_path)
        case _:
            raise ValueError(f"Unsupported SDK: {sdk}")

    if sdk != agent.sdk:
        raise ValueError(
            f"SDK mismatch: expected {sdk}, got {agent.sdk}. "
            "Please check the agent configuration."
        )
    data = agent.model_dump_json()
    etcd_client = get_etcd_client()
    etcd_client.put(agent.etcd_key, data)  # type: ignore
    print(f"Registered agent {agent.name} with SDK {sdk} and version {agent.version}.")
