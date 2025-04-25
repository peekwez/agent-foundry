from typing import Literal

from pydantic import BaseModel, Field


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
