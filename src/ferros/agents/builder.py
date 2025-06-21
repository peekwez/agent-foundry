import pathlib

from agents import Agent, RunContextWrapper

from ferros.core.utils import get_settings
from ferros.models.context import Context


def get_instructions(context: RunContextWrapper, agent: Agent) -> str:
    """
    Get the instructions for the context builder agent.

    Returns:
        str: The instructions for the context builder agent.
    """
    prompts_home = pathlib.Path(__file__).parent / "prompts"
    context_builder_prompt = open(prompts_home / "context-builder.md").read()
    return context_builder_prompt


settings = get_settings()

context_builder = Agent(
    name="Context Builder",
    model=settings.context.model,
    instructions=get_instructions,
    model_settings=settings.context.model_settings,
    tool_use_behavior="run_llm_again",
    output_type=Context,
)
