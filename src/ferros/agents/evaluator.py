from __future__ import annotations

import asyncio
import pathlib
from typing import Any

import loguru
from agents import Agent, RunContextWrapper, Runner, RunResult, custom_span
from agents.mcp import MCPServer
from tenacity import retry, stop_after_attempt, wait_random_exponential

from ferros.core.logging import get_logger
from ferros.core.utils import get_settings
from ferros.models.agents import AgentsConfig
from ferros.models.evaluation import EvaluationResult, EvaluationResults
from ferros.models.plan import Plan
from ferros.tools.evaluation import evaluation_check_tool

MINIMUM_EVALUATION_CHECKS = 3


def get_instructions(
    context: RunContextWrapper[AgentsConfig],
    agent: Agent[AgentsConfig],
) -> str:
    """
    Get the instructions for the evaluator agent.

    Returns:
        str: The instructions for the evaluator agent.
    """

    prompt_file = "evaluator.md"
    prompts_home = pathlib.Path(__file__).parent / "prompts"
    evaluator_prompt = open(prompts_home / prompt_file).read()
    return evaluator_prompt


def get_evaluator(
    tools: list[Any] | None = None,
    mcp_servers: list[MCPServer] | None = None,
) -> Agent[AgentsConfig]:
    """
    Get the evaluator agent with the appropriate instructions.

    Args:
        context (RunContextWrapper[AgentsConfig]): The run context.
        agent (Agent[AgentsConfig]): The agent instance.

    Returns:
        Agent[AgentsConfig]: The evaluator agent.
    """
    settings = get_settings()
    return Agent(
        name="Evaluator",
        instructions=get_instructions,
        model=settings.evaluator.model,
        tool_use_behavior="run_llm_again",
        model_settings=settings.evaluator.model_settings,
        output_type=EvaluationResult,
        tools=tools or [],
        mcp_servers=mcp_servers or [],
    )


def process_evals(
    results: list[RunResult | BaseException], checks: int, logger: loguru.Logger
) -> EvaluationResults:
    """
    Process the evaluation results to ensure they meet the minimum checks.

    Args:
        evaluations (EvaluationResults): The evaluation results to process.

    Returns:
        EvaluationResults: The processed evaluation results.
    """
    failures = [
        item
        for item in results
        if isinstance(item, BaseException) or not item.final_output
    ]
    success = [
        item.final_output
        for item in results
        if isinstance(item, RunResult) and item.final_output
    ]

    if not results:
        logger.error("No evaluation runs were executed.")
        raise ValueError("Results evaluation failed")

    if len(failures) == checks:
        logger.error(
            f"All {checks} evaluation runs failed. Please check the evaluation results."
        )
        raise ValueError(
            "All evaluation runs failed. Please check the evaluation results."
        )

    if len(success) < MINIMUM_EVALUATION_CHECKS:
        logger.error(
            f"Not enough successful evaluation runs found: {len(success)}. "
            f"Expected at least {MINIMUM_EVALUATION_CHECKS} successful runs."
        )
        raise ValueError(
            f"Not enough successful evaluation runs found: {len(success)}. "
            f"Expected at least 3 successful runs."
        )

    if not success:
        logger.error("No successful evaluation runs found.")
        raise ValueError("No successful evaluation runs found.")

    evaluations: EvaluationResults = EvaluationResults(results=success)
    return evaluations


@retry(
    stop=stop_after_attempt(3),
    wait=wait_random_exponential(multiplier=1, max=15),
    reraise=True,
)
async def evaluate_result(
    plan: Plan,
    revision: int,
    server: MCPServer,
    checks: int = MINIMUM_EVALUATION_CHECKS,
) -> EvaluationResults:
    """
    Evaluate the latest writer or editor result for a given plan and revision.

    Args:
        plan (Plan): The plan to evaluate.
        revision (int): The revision number of the plan.
        server (MCPServer): The MCP server to use for evaluation.
        checks (int, optional): The number of evaluation checks to perform.
            Defaults to 3.
    Returns:
        EvaluationResults: The results of the evaluation.
    """

    logger = get_logger(__name__)
    with custom_span(
        name="Evaluation",
        data={"Plan Id": plan.id, "Revision": revision, "Checks": checks},
    ):
        logger.info(
            f"Evaluating results for plan: {plan.id}, revision: {revision}, "
            f"checks: {checks}"
        )
        user_input = (
            f"\nThe latest writer or editor result to be evaluated is "
            f"for plan: {plan.id}, revision: {revision}"
        )
        user_inputs = [f"{user_input} check number: {i}" for i in range(1, checks + 1)]
        agent = get_evaluator(tools=[evaluation_check_tool], mcp_servers=[server])
        runs = [
            Runner.run(agent, input=eval_input, max_turns=20)
            for eval_input in user_inputs
        ]
        results: list[RunResult | BaseException] = await asyncio.gather(
            *runs, return_exceptions=True
        )
        evaluations = process_evals(results, checks, logger)
        logger.info(
            f"Evaluation results for plan {plan.id}, revision {revision}: "
            f"Score: {evaluations.score:0.2f}% - "
            f"Status: {'PASS' if evaluations.passed else 'FAIL'}"
        )
        logger.info(
            f"Evaluation completed with {len(evaluations.results)} successful checks."
        )

    return evaluations
