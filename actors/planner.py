from actors.base import build_agent
from core.models import Plan
from actors.manager import AGENT_REGISTRY


AGENT_REGISTRY_SUFFIX = f"{100*'-'}\n\n".join(
    [
        f">> Agent Name: {agent.name}\n>> Agent Instructions: {agent.instructions.split('You have access')[0]}"
        for _, agent in AGENT_REGISTRY.items()
    ]
)


planner = build_agent(
    name="Planner",
    instructions=(
        "You are an expert project planner. Break the HUMAN_GOAL "
        "into a minimum DAG of atomic steps. Each step must reference "
        "one of the agents provided below"
        "Return ONLY valid JSON matching the Plan schema. The revision "
        "should be for this plan should be 1 and the status of steps should "
        "be pending. The agents are list below: \n\n"
        f"{AGENT_REGISTRY_SUFFIX}"
    ),
    output_type=Plan,
)


re_planner = build_agent(
    name="Re-Planner",
    instructions=(
        "You are a Re-planner, so you will be given a plan ",
        "and must update it with additional steps based on the "
        "original goal and any feedback provided by other agents. "
        "Each step must reference one of the agents listed below exactly. "
        "Return ONLY valid JSON matching the Plan schema."
        "The new steps should form part of the next revision and the status "
        "of the new steps should be tagged as pending with the existing steps"
        "tagged as completed. The agents are list below: \n\n"
        f"{100*'-'}"
        f"{AGENT_REGISTRY_SUFFIX}\n\n",
        "Read the `context` memory value to get information regarding available data in "
        "memory. You should then fetch the existing `plan` and the latest evaluation "
        "results to use as additional context to replan the task.",
    ),
    output_type=Plan,
)
