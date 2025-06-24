import pathlib
from typing import Any

from agents import Agent, RunContextWrapper, Runner
from agents.mcp import MCPServer

from ferros.agents.factory import get_agent_configs
from ferros.core.logging import get_logger
from ferros.core.utils import get_settings, log_done
from ferros.models.agents import AgentsConfig
from ferros.models.plan import Plan
from ferros.tools.web_search import web_search_tool


def get_instructions(
    replanner: bool,
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
            f"--\n"
        )
        text.append(string)
    prompt_file = "re-planner.md" if replanner else "planner.md"
    prompts_home = pathlib.Path(__file__).parent / "prompts"
    planner_prompt = open(prompts_home / prompt_file).read()
    return planner_prompt.format(agent_list="\n".join(text))


def get_planner(
    tools: list[Any] | None = None,
    mcp_servers: list[MCPServer] | None = None,
    replanner: bool = False,
) -> Agent[AgentsConfig]:
    """
    Get the planner agent with the appropriate instructions.

    Args:
        context (RunContextWrapper[AgentsConfig]): The run context.
        agent (Agent[AgentsConfig]): The agent instance.

    Returns:
        Agent[AgentsConfig]: The planner agent.
    """

    def _instructions(
        context: RunContextWrapper[AgentsConfig], agent: Agent[AgentsConfig]
    ) -> str:
        return get_instructions(replanner, context, agent)

    settings = get_settings()
    return Agent(
        name="Planner" if not replanner else "Re-Planner",
        instructions=_instructions,
        model=settings.planner.model,
        tool_use_behavior="run_llm_again",
        model_settings=settings.planner.model_settings,
        output_type=Plan,
        tools=tools or [],
        mcp_servers=mcp_servers or [],
    )


async def plan_task(
    plan_id: str, revision: int, user_input: str, server: MCPServer
) -> Plan:
    """
    Plan the task using the planner agent.

    Args:
        plan_id (str): The unique identifier for the plan.
        revision (int): The revision number for the plan.
        user_input (str): The user input for the task.
        server (MCPServerSse): The MCP server to fetch the output from.

    Returns:
        Plan: The generated plan object with the steps for the task.
    """
    logger = get_logger(__name__)
    input = f"{user_input}\n\nUse the UUID: {plan_id} as the plan id."
    context = get_agent_configs()
    agent = get_planner(
        tools=[web_search_tool], mcp_servers=[server], replanner=revision > 1
    )
    result = await Runner.run(agent, input=input, max_turns=20, context=context)
    plan: Plan = result.final_output
    logger.info(f"Task plan created with {len(plan.steps)} steps...")

    size = len(plan.steps)
    if agent.name == "Planner":
        log_done(f"Task plan created with {size} steps...")
    elif agent.name == "Re-Planner":
        new_size = len([s for s in plan.steps if s.status == "pending"])
        log_done(f"Task re-planning created with {new_size} steps...")
    return plan
