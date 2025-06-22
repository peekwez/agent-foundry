from typing import Literal

from pydantic import BaseModel, Field


class EvaluationQuestion(BaseModel):
    """
    Represents an evaluation question with its associated metadata.
    """

    question: str = Field(
        ...,
        description="An evaluation question that must be answered yes or no.",
    )
    answer: Literal["yes", "no"] = Field(
        ...,
        description="The answer to the evaluation question, either 'yes' or 'no'.",
    )


class EvaluationResult(BaseModel):
    """
    Represents a collection of evaluation questions and their answers.
    """

    questions: list[EvaluationQuestion] = Field(
        ...,
        description="A list of evaluation questions.",
    )
    revision: int = Field(
        default=1,
        description=(
            "The revision of the plan that is being evaluated. This is set based "
            "on the plan revision."
        ),
    )
    check_number: int = Field(
        default=1,
        description=(
            "The check number for the evaluation. This is set to 1 by default "
            "unless specified otherwise in the task goal."
        ),
    )
    score: float = Field(
        default=0.0,
        description=(
            "The score for the evaluation, calculated based on the answers. "
            "The sum of all 'yes' answers is divided by the total number of questions "
            "to get a percentage score. This score is between 0 and 100. "
            "Two decimal places are allowed."
        ),
    )
    threshold: float = Field(
        default=80.0,
        description=(
            "The threshold for passing the evaluation. This is set to 80% by default "
            "unless specified otherwise in the task goal."
        ),
    )
    threshold_source: Literal["default", "task goal"] = Field(
        default="default",
        description=(
            "The source of the threshold value, which can be 'default' or 'task goal'. "
            "This indicates whether the threshold is the default value or specified in "
            "the task goal."
        ),
    )
    passed: bool = Field(
        default=False,
        description=(
            "Indicates whether the task has passed the evaluation based on the score. "
            "The threshold for passing is 80% unless the task goal specifies otherwise."
        ),
    )
    replan: bool = Field(
        default=False,
        description=(
            "Indicates whether the plan needs to be revised based on the evaluation."
        ),
    )
    planning_feedback: str = Field(
        default="",
        description=(
            "Feedback for the re-planner if the task needs to be revised. "
            "This should be a concise summary of the issues found in the evaluation."
        ),
    )


class EvaluationResults(BaseModel):
    """
    Represents a collection of evaluation results for multiple checks.
    """

    results: list[EvaluationResult] = Field(
        ...,
        description="A list of evaluation results for different checks.",
    )

    @property
    def score(self) -> float:
        """
        Aggregate the scores from all evaluation results.

        Returns:
            float: The aggregated score, which is the average of all individual scores.
        """
        if not self.results:
            return 0.0
        total_score = sum(result.score for result in self.results)
        return total_score / len(self.results) if self.results else 0.0

    @property
    def threshold(self) -> float:
        """
        Get the threshold for passing the evaluation.

        Returns:
            float: The threshold value, which is the maximum threshold from all results.
        """
        if not self.results:
            return 0.0
        return max(result.threshold for result in self.results)

    @property
    def passed(self) -> bool:
        """
        Check if all evaluation results passed.

        Returns:
            bool: True if all evaluations passed, False otherwise.
        """
        return self.score >= self.threshold

    @property
    def feedback(self) -> str:
        """
        Aggregate feedback from all evaluation results.

        Returns:
            str: Concatenated feedback from all evaluations.
        """
        feedback_lines = [
            f"Check {result.check_number}: {result.planning_feedback}"
            for result in self.results
            if result.planning_feedback
        ]
        return "\n".join(feedback_lines)
