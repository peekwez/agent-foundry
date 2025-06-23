import uuid

from pydantic import AnyUrl, BaseModel, Field


class TaskConfig(BaseModel):
    goal: str = Field(
        ...,
        description="The goal of the task to be performed by the agent.",
    )
    contexts: list[AnyUrl] = Field(
        ..., description="List of context URLs for the task."
    )
    revisions: int = Field(
        3, ge=0, description="Number of revisions to perform if needed."
    )
    trace_id: str = Field(
        default_factory=lambda: f"{uuid.uuid4().hex}",
        description="Unique identifier for tracing the task execution.",
    )

    @property
    def context_strings(self) -> list[str]:
        """
        Returns a list of context strings from the URLs.
        """
        return [ctx.unicode_string() for ctx in self.contexts]
