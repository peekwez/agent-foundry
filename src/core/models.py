from enum import Enum
from typing import Literal

from agents import ModelSettings
from pydantic import BaseModel, ConfigDict, Field


class AgentName(str, Enum):
    RESEARCHER = "researcher"
    EXTRACTOR = "extractor"
    ANALYZER = "analyzer"
    WRITER = "writer"
    EDITOR = "editor"
    EVALUATOR = "evaluator"

    @classmethod
    def _missing_(cls, value: object) -> "AgentName | None":
        """
        Find the corresponding AgentName for a given value.

        Args:
            value (object): The value to match against AgentName members.

        Returns:
            AgentName | None: The matching AgentName member or None.
        """
        if isinstance(value, str):
            value_lower = value.lower()
            for member in cls:
                if member.value == value_lower:
                    return member
        return None

    def __str__(self) -> str:
        return self.value


class BaseAgentName(str, Enum):
    CONTEXT_BUILDER = "context builder"
    PLANNER = "planner"

    @classmethod
    def _missing_(cls, value: object) -> "BaseAgentName | None":
        """
        Find the corresponding BaseAgentName for a given value.

        Args:
            value (object): The value to match against BaseAgentName members.

        Returns:
            BaseAgentName | None: The matching BaseAgentName member or None.
        """
        if isinstance(value, str):
            value_lower = value.lower()
            for member in cls:
                if member.value == value_lower:
                    return member
        return None

    def __str__(self) -> str:
        return self.value


class AgentSettings(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: BaseAgentName | AgentName = Field(..., description="The name of the agent.")
    is_task_agent: bool = Field(
        default=True, description="Indicates if the agent is a task agent."
    )
    model: str = Field(..., description="The model to be used by the agent.")
    model_settings: ModelSettings = Field(
        default=ModelSettings(
            temperature=None,
            max_tokens=8192,
            tool_choice="required",
        ),
        description="Settings for the model.",
    )


class ProviderSettings(BaseModel):
    api_key: str = Field(..., description="API key for the model provider.")
    base_url: str | None = Field(
        default=None, description="Base URL for the model provider."
    )


class Settings(BaseModel):
    provider: ProviderSettings = Field(
        ..., description="Configuration for the model provider."
    )
    context_builder: AgentSettings = Field(
        ..., description="Configuration for the context builder agent."
    )
    planner: AgentSettings = Field(
        ..., description="Configuration for the planner agent."
    )
    researcher: AgentSettings = Field(
        ..., description="Configuration for the researcher agent."
    )
    extractor: AgentSettings = Field(
        ..., description="Configuration for the extractor agent."
    )
    analyzer: AgentSettings = Field(
        ..., description="Configuration for the analyzer agent."
    )
    writer: AgentSettings = Field(
        ..., description="Configuration for the writer agent."
    )
    editor: AgentSettings = Field(
        ..., description="Configuration for the editor agent."
    )
    evaluator: AgentSettings = Field(
        ..., description="Configuration for the evaluator agent."
    )


class PlanStep(BaseModel):
    id: int = Field(..., description="Unique identifier for the step.")
    agent: AgentName = Field(
        ..., description="The agent responsible for executing the step."
    )
    prompt: str = Field(..., description="The prompt to be sent to the agent.")
    revision: int = Field(..., description="The revision number of the step.")
    status: Literal["pending", "completed"] = Field(
        ..., description="The status of the step."
    )
    depends_on: list[int] = Field(
        ..., description="A list of step IDs that this step depends on."
    )


class Plan(BaseModel):
    id: str = Field(..., description="Unique identifier for the plan.")
    goal: str = Field(..., description="The goal of the plan.")
    steps: list[PlanStep] = Field(
        ...,
        description="A collection of steps to be executed by different agents.",
    )


class ContextItem(BaseModel):
    file_path_or_url: str = Field(
        ..., description="The file path or URL to the context data."
    )
    description: str = Field(..., description="A description of the context data.")


class Context(BaseModel):
    contexts: list[ContextItem] = Field(
        ...,
        description="A collection of contexts to be used by different agents.",
    )


class Score(BaseModel):
    score: Literal["pass", "fail"] = Field(
        ..., description="Score given by the evaluator."
    )
    feedback: str = Field(..., description="Feedback from the evaluator on the task.")
