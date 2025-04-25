from actors.base import build_agent
from actors.manager import AGENT_REGISTRY
from core.models import Plan

AGENT_REGISTRY_SUFFIX = f"{100 * '-'}\n\n".join(
    [
        (
            f">> Agent Name: {agent.name}\n"
            f">> Agent Instructions: {agent.instructions.split('You have access')[0]}"
        )
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
        f"{AGENT_REGISTRY_SUFFIX}\n\n"
        "Fetch the context memory value to get information regarding available "
        "data to help with the planning if they are relevant. The key to use is "
        "'blackboard:<plan id>' and the value is a JSON object\n\n"
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
        f"{100 * '-'}"
        f"{AGENT_REGISTRY_SUFFIX}\n\n",
        "Fetch the context memory value to get information regarding available "
        "data to help with the re-planning if they are relevant. The key to use is "
        "'blackboard:<plan id>' and the value is a JSON object\n\n"
        "Fetch the existing plan from memory to know what steps are available and "
        "what dependencies exist. The key to use is 'plan:<plan id>' and the value "
        "is a JSON object\n\n",
    ),
    output_type=Plan,
)
