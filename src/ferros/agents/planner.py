import pathlib

from agents import Agent, RunContextWrapper

from ferros.core.utils import get_settings
from ferros.models.agent import AgentsConfig
from ferros.models.plan import Plan


def get_instructions(
    prompt_file: str,
    context: RunContextWrapper[AgentsConfig],
    agent: Agent[AgentsConfig],
) -> str:
    """
    Get the instructions for the planner agent.

    Returns:
        str: The instructions for the planner agent.
    """
    text: list[str] = []
    for agent_config in context.context.agents:
        name = agent_config.name.strip().capitalize()
        instructions = agent_config.instructions.strip()
        string = (
            f"--\n> "
            f">**Agent Name**: {name}\n"
            f">**Agent SDK**: {agent_config.sdk}\n"
            f">**Agent Version**: {agent_config.version}\n"
            f">**Agent Instruction**: {instructions}\n"
        )
        text.append(string)
    prompts_home = pathlib.Path(__file__).parent / "prompts"
    planner_prompt = open(prompts_home / prompt_file).read()
    return planner_prompt.format(agent_list="\n".join(text))


def get_planner_instructions(
    context: RunContextWrapper[AgentsConfig], agent: Agent[AgentsConfig]
) -> str:
    """
    Get the instructions for the planner agent.

    Returns:
        str: The instructions for the planner agent.
    """
    return get_instructions("planner.md", context, agent)


def get_re_planner_instructions(
    context: RunContextWrapper[AgentsConfig], agent: Agent[AgentsConfig]
) -> str:
    """
    Get the instructions for the re-planner agent.
    Returns:
        str: The instructions for the re-planner agent.
    """
    return get_instructions("re-planner.md", context, agent)


settings = get_settings()


planner = Agent(
    name="Planner",
    model=settings.planner.model,
    instructions=get_planner_instructions,
    tool_use_behavior="run_llm_again",
    model_settings=settings.planner.model_settings,
    output_type=Plan,
)


re_planner = Agent(
    name="Re-Planner",
    model=settings.planner.model,
    instructions=get_re_planner_instructions,
    tool_use_behavior="run_llm_again",
    model_settings=settings.planner.model_settings,
    output_type=Plan,
)
