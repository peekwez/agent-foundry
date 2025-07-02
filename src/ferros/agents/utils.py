from ferros.models.plan import PlanStep


def get_step(
    agent_name: str,
    steps: list[PlanStep],
    index: int | None = None,
    is_last: bool = True,
) -> PlanStep | None:
    """
    Get the last agent from a list of agents.

    Args:
        agent_name (str): The name of the agent.
        steps (list[PlanStep]): The list of agent steps.

    Returns:
        PlanStep: The latest agent step.
    """

    def fn(x: PlanStep) -> bool:
        return x.agent_name.lower() == agent_name.lower()

    if is_last and index is None:
        index = -1

    if index is None and not is_last:
        raise ValueError(
            "Index must be an integer or None. If None, the last step will be returned."
        )

    if not isinstance(index, int):
        raise ValueError(
            "Index must be an integer or None. If None, the last step will be returned."
        )

    try:
        return sorted(filter(fn, steps), key=lambda x: x.id)[index]
    except IndexError:
        return None
