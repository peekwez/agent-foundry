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


class Evaluations(BaseModel):
    """
    Represents a collection of evaluation questions and their answers.
    """

    questions: list[EvaluationQuestion] = Field(
        ...,
        description="A list of evaluation questions.",
    )

    @property
    def score(self) -> float:
        """
        Calculate the score based on the answers to the evaluation questions.

        Returns:
            float: The score as a percentage of correct answers.
        """
        if not self.questions:
            return 0.0
        correct_answers = sum(1.0 for q in self.questions if q.answer == "yes")
        return (correct_answers / len(self.questions)) * 100.0

    @property
    def feedback(self) -> str:
        """
        Generate feedback based on the evaluation questions.

        Returns:
            str: Feedback summarizing the evaluation results.
        """
        if not self.questions:
            return "No evaluation questions provided."

        feedback: list[str] = []
        for q in self.questions:
            feedback.append(f"**Question**: {q.question}\n**Answer**: {q.answer}")

        return "\n\n".join(feedback)
