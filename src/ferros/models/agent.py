import hashlib
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from agents import Agent, AgentOutputSchemaBase, ModelSettings, Runner
from agents.mcp import MCPServer
from pydantic import BaseModel, ConfigDict, Field

from ferros.core.utils import load_yaml_j2

AgentSDK = Literal["openai-sdk", "google-adk", "pydantic-ai", "langgraph"]


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

    @property
    def etcd_key(self) -> str:
        """
        Generate the etcd key for the agent configuration.

        Returns:
            str: The etcd key for the agent configuration.
        """
        return f"/agents/{self.name.lower()}/{self.sdk.lower()}/{self.version.lower()}"

    @classmethod
    def from_yaml(cls, file_path: str) -> "AgentSDKConfig":
        """
        Create an instance from YAML content.

        Args:
            yaml_content (str): The YAML configuration content.

        Return:
            AgentSDKConfig: An instance of AgentSDKConfig.
        """
        contents = Path(file_path).read_bytes()
        h = hashlib.sha256()
        h.update(contents)
        data = load_yaml_j2(file_path)
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
        return Agent(
            name=self.name.capitalize(),
            model=self.model,
            instructions=self.instructions,
            tools=tools or [],
            mcp_servers=mcp_servers or [],
            tool_use_behavior="run_llm_again",
            model_settings=self.model_settings,
            output_type=output_type,
        )

    async def run_agent(self, agent: Agent, input: str, max_turns: int = 60) -> None:
        """
        Run the agent using the provided runner.

        Args:
            agent (Agent): The agent to be run.
            input (str): The input to be provided to the agent.
            max_turns (int): The maximum number of turns to run the agent.
        """

        await Runner.run(agent, input=input, max_turns=max_turns)


class GoogleADKConfig(AgentSDKConfig):
    pass


class PydanticAIConfig(AgentSDKConfig):
    pass


class LangGraphConfig(AgentSDKConfig):
    pass


class AgentsConfig(BaseModel):
    agents: list[
        OpenAISDKConfig | GoogleADKConfig | PydanticAIConfig | LangGraphConfig
    ] = Field(
        ...,
        description="A collection of agents to be used in the plan context.",
    )
