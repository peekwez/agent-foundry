from typing import Any

from agents import FunctionTool, RunContextWrapper
from pydantic import BaseModel, Field

from ferros.models.evaluation import EvaluationResult


class EvaluationArguments(BaseModel):
    evaluation_result: str = Field(
        ...,
        description="The evaluation result as a JSON string.",
    )


def check_evaluation(evaluation_result: str) -> str:
    """
    Check the evaluations based on the provided evaluation result.

    Args:
        evaluation_result (str): The evaluation result as a JSON string.

    Returns:
        str: A message indicating the evaluation result is valid and
            consistent with the score.
    """

    # is the evaluation result a valid JSON string?
    try:
        evaluation = EvaluationResult.model_validate_json(evaluation_result)
    except Exception as e:
        raise ValueError(f"Invalid evaluation json data: {e}") from e

    # check if the evaluation score was computed correctly
    score = evaluation.score
    num_questions = len(evaluation.questions)
    pass_questions = len([q for q in evaluation.questions if q.answer.lower() == "yes"])
    calculated_score = 100.0 * float(
        pass_questions / float(num_questions) if num_questions > 0 else 0
    )

    if abs(calculated_score - score) > 0.05:  # Allowing a small margin of error
        raise ValueError(
            f"Score {score} does not match calculated score {calculated_score} "
            "based on the number of questions answered with a `yes`."
        )

    # check if pass status is set correctly
    if evaluation.passed and evaluation.score < evaluation.threshold:
        raise ValueError(
            f"Score {score} is below the threshold {evaluation.threshold}. "
            "Evaluation did not pass. Please check the evaluation result."
        )

    # check if fail status is set correctly
    if not evaluation.passed and evaluation.score >= evaluation.threshold:
        raise ValueError(
            f"Score {score} is above the threshold {evaluation.threshold}. "
            "Evaluation passed. Please check the evaluation result."
        )

    return "Evaluation result is valid and consistent with the score."


async def run_check_evaluation(ctx: RunContextWrapper[Any], args: str) -> str:
    """
    Run the web search tool with the provided context and arguments.

    Args:
        ctx (RunContextWrapper): The context wrapper for the run.
        args (str): The arguments for the web search.

    Returns:
        str: The result of the web search.
    """
    try:
        parsed = EvaluationArguments.model_validate_json(args)
        result = check_evaluation(parsed.evaluation_result)
        return result
    except ValueError as e:
        raise ValueError(f"Evaluation failed: {e}") from e


evaluation_check_tool = FunctionTool(
    name="evaluation_check",
    description="Validate the evaluation result with rule checks.",
    params_json_schema=EvaluationArguments.model_json_schema(),
    on_invoke_tool=run_check_evaluation,
)

__all__ = ["evaluation_check_tool"]
