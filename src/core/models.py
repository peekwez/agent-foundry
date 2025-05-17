from typing import Literal

from agents import ModelSettings
from pydantic import BaseModel, Field


class AgentSettings(BaseModel):
    name: str = Field(..., description="The name of the agent.")
    is_task_agent: bool = Field(
        True, description="Indicates if the agent is a task agent."
    )
    model: str = Field(..., description="The model to be used by the agent.")
    model_settings: ModelSettings = Field(
        default=ModelSettings(
            temperature=0.0,
            max_tokens=8192,
            tool_choice="required",
        ),
        description="Settings for the model.",
    )


class ProviderSettings(BaseModel):
    api_key: str = Field(..., description="API key for the model provider.")
    base_url: str = Field(..., description="Base URL for the model provider.")


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
    agent: Literal[
        "Researcher",
        "Extractor",
        "Analyzer",
        "Writer",
        "Editor",
        "Evaluator",
    ] = Field(..., description="The agent responsible for executing the step.")
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
