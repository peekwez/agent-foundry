import hashlib
import re
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from agents import Agent, AgentOutputSchemaBase, ModelSettings, Runner
from agents.mcp import MCPServer
from pydantic import BaseModel, ConfigDict, Field

from ferros.core.logging import get_logger
from ferros.core.parsers import load_config_file

REGISTRY_PREFIX = "agents:config"


class SDKType(StrEnum):
    OPENAI = "openai"
    GOOGLE = "google"
    PYDANTIC = "pydantic"
    LANGGRAPH = "langgraph"

    @classmethod
    def _missing_(cls, value: object) -> "SDKType | None":
        """
        Find the corresponding SDKType for a given value.

        Args:
            value (object): The value to match against SDKType members.

        Returns:
            SDKType | None: The matching SDKType member or None.
        """
        if isinstance(value, str):
            value_lower = value.lower()
            for member in cls:
                if member.value == value_lower:
                    return member
        return None


def config_key(name: str, sdk: SDKType, version: str) -> str:
    """
    Generate a unique configuration key for the agent.

    Args:
        name (str): The name of the agent.
        sdk (SDKType): The SDK being used.
        version (str): The version of the agent.

    Returns:
        str: The generated configuration key.
    """
    name = re.sub(r"\s+", "-", name).replace("--", "-").lower()
    _sdk = sdk.lower()
    version = version.lower()
    return f"{REGISTRY_PREFIX}:{name}:{_sdk}:{version}"


class AgentSDKConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    sdk: SDKType = Field(
        default=SDKType.OPENAI,
        description="The SDK to be used by the agent.",
    )
    version: str = Field(
        ...,
        description="The version hash (SHA256) of the agent configuration.",
    )
    file_name: str = Field(
        ...,
        description="The name of the file containing the agent configuration.",
    )

    created_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="The timestamp when the agent was created.",
    )

    # base parameters for all SDKs
    name: str = Field(default="gpt-4o", description="The name of the agent.")
    model: str = Field("gpt-4o", description="The large language model to be used.")
    instructions: str = Field(
        default="You are a helpful assistant.",
        description="Instructions for the OpenAI model.",
    )
    output_type: AgentOutputSchemaBase | None = Field(
        default=None,
        description="The output type for the agent.",
    )

    @property
    def key(self) -> str:
        """
        Generate the etcd key for the agent configuration.

        Returns:
            str: The etcd key for the agent configuration.
        """
        return config_key(self.name, self.sdk, self.version)

    @classmethod
    def from_yaml(cls, file_path: str) -> "AgentSDKConfig":
        """
        Create an instance from YAML content.

        Args:
            yaml_content (str): The YAML configuration content.

        Returns:
            AgentSDKConfig: An instance of AgentSDKConfig.
        """
        contents = Path(file_path).read_bytes()
        h = hashlib.sha256()
        h.update(contents)
        data = load_config_file(file_path)
        data["version"] = h.hexdigest()
        data["file_name"] = Path(file_path).name
        data["created_at"] = datetime.now().isoformat()
        return cls.model_validate(data)

    def create_agent(
        self,
        output_type: str | Any = None,
        tools: list[Any] | None = None,
        mcp_servers: list[Any] | None = None,
    ) -> Agent:
        """
        Create an Agent instance from the AgentSDKConfig.

        Returns:
            Agent: An instance of the Agent class configured with this SDK settings.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")

    async def run_agent(
        self, agent: Any | Agent, input: str, max_turns: int = 60
    ) -> None:
        """
        Run the agent using the provided runner.

        Args:
            agent (Agent): The agent to be run.
            input (str): The input to be provided to the agent.
            max_turns (int): The maximum number of turns to run the agent.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")


# openai-sdk specific settings
class OpenAISDKConfig(AgentSDKConfig):
    model_settings: ModelSettings = Field(
        default=ModelSettings(),
        description="Settings for the model.",
    )

    def create_agent(
        self,
        output_type: Any | AgentOutputSchemaBase | None = None,
        tools: list[Any] | None = None,
        mcp_servers: list[MCPServer] | None = None,
    ) -> Agent:
        """
        Create an Agent instance from the OpenAISDKConfig.

        Returns:
            Agent: An instance of the Agent class configured with this SDK settings.
        """

        path = Path(__file__).parents[1] / "agents" / "prompts" / "tasks.md"
        template = path.read_text()
        instructions = template.format(
            name=f"{self.name.capitalize()} Agent", instructions=self.instructions
        )
        return Agent(
            name=self.name.capitalize(),
            model=self.model,
            instructions=instructions,
            tools=tools or [],
            mcp_servers=mcp_servers or [],
            tool_use_behavior="run_llm_again",
            model_settings=self.model_settings,
            output_type=output_type,
        )

    async def run_agent(
        self, agent: Agent, input: str, max_turns: int = 60, retry: int = 3
    ) -> None:
        """
        Run the agent using the provided runner.

        Args:
            agent (Agent): The agent to be run.
            input (str): The input to be provided to the agent.
            max_turns (int): The maximum number of turns to run the agent.
        """
        logger = get_logger(__name__)
        for attempt in range(retry):
            try:
                logger.info(f"Running agent: {agent.name}, Attempt: {attempt + 1}")
                # Use the Runner to execute the agent with the provided input
                result = await Runner.run(agent, input=input, max_turns=max_turns)
                if result:
                    break  # Exit loop if successful
            except Exception as e:
                logger.error(f"Error occurred while running agent: {e}")
                if attempt == retry - 1:
                    raise
            else:
                raise RuntimeError(
                    f"Failed to run agent {agent.name} after {retry} attempts."
                )


class GoogleADKConfig(AgentSDKConfig):
    pass


class PydanticAIConfig(AgentSDKConfig):
    pass


class LangGraphConfig(AgentSDKConfig):
    pass


class AgentsConfig(BaseModel):
    agents: list[AgentSDKConfig] = Field(
        ...,
        description="A collection of agents to be used in the plan context.",
    )


SDK_CLASS_MAP: dict[SDKType, type[AgentSDKConfig]] = {
    SDKType.OPENAI: OpenAISDKConfig,
    SDKType.GOOGLE: GoogleADKConfig,
    SDKType.PYDANTIC: PydanticAIConfig,
    SDKType.LANGGRAPH: LangGraphConfig,
}
