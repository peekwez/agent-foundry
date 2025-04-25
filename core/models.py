from dataclasses import dataclass
from typing import List, Literal


@dataclass
class PlanStep:
    id: int
    """ Unique identifier for the step.  Integer incremented by 1 for each step. """
    agent: str
    """ The agent responsible for executing the step. """
    prompt: str
    """ The prompt to be sent to the agent. """
    revision: int
    """ The revision number of the step.  Incremented by 1 for each revision. """
    status: Literal["pending", "completed"]
    """ The status of the step. """
    depends_on: List[int]
    """ A list of step IDs that this step depends on. """


@dataclass
class Plan:
    id: str
    """ Unique identifier for the plan.  Randomly generated UUID. """

    goal: str
    """ The goal of the plan. """

    steps: List[PlanStep]
    """ A plan is a collection of steps to be executed by different agents. """


@dataclass
class Score:
    score: Literal["pass", "fail"]
    """ Score given by the evaluator. """

    feedback: str
    """ Feedback from the evaluator on the task. """
