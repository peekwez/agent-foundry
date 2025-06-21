from typing import Literal

from pydantic import BaseModel, Field

from ferros.models.agent import SDKType


class PlanStep(BaseModel):
    id: int = Field(..., description="Unique identifier for the step.")
    agent_name: str = Field(
        ..., description="The agent responsible for executing the step."
    )
    agent_sdk: SDKType = Field(
        ..., description="The SDK used by the agent (e.g., 'mcp', 'langchain')."
    )
    agent_version: str = Field(
        ..., description="The version of the agent responsible for executing the step."
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
