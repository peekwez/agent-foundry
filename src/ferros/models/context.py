from pydantic import BaseModel, Field


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
