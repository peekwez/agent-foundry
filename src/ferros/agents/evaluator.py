from __future__ import annotations

import asyncio
import pathlib
from typing import Any

import loguru
from agents import Agent, RunContextWrapper, Runner, custom_span
from agents.mcp import MCPServer
from tenacity import retry, stop_after_attempt, wait_random_exponential

from ferros.core.logging import get_logger
from ferros.core.store import send_update
from ferros.core.utils import get_settings
from ferros.models.agents import AgentsConfig
from ferros.models.evaluation import EvaluationResult, EvaluationResults
from ferros.models.plan import Plan
from ferros.tools.evaluation import evaluation_check_tool

STEP_ID = 70000
AGENT_NAME = "evaluator"
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
    evals: list[EvaluationResult | None], checks: int, logger: loguru.Logger
) -> EvaluationResults:
    """
    Process the evaluation results to ensure they meet the minimum checks.

    Args:
        evaluations (EvaluationResults): The evaluation results to process.

    Returns:
        EvaluationResults: The processed evaluation results.
    """
    failures = [item for item in evals if item is None]
    success = [item for item in evals if isinstance(item, EvaluationResult)]

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

    evaluations: EvaluationResults = EvaluationResults(results=success)
    return evaluations


async def run_eval(
    plan_id: str, revision: int, server: MCPServer, check_num: int
) -> EvaluationResult | None:
    """
    Run the evaluation process for a given plan and revision.

    Args:
        user_input (str): The user input for the evaluation.
        server (MCPServer): The MCP server to use for evaluation.

    Returns:
        RunResult | BaseException: The result of the evaluation run.
    """

    logger = get_logger(__name__)
    with custom_span(
        name="Evaluation Run",
        data={
            "Plan Id": plan_id,
            "Revision": revision,
            "Check Number": check_num,
        },
    ):
        user_input = (
            f"\nThe latest writer or editor result to be evaluated is "
            f"for plan: {plan_id}, revision: {revision}"
        )
        try:
            await send_update(plan_id, STEP_ID + check_num, AGENT_NAME, "running")
            logger.info(f"Running evaluation for plan: {plan_id}, revision: {revision}")
            agent = get_evaluator(tools=[evaluation_check_tool], mcp_servers=[server])
            result = await Runner.run(agent, input=user_input, max_turns=20)
            eval = result.final_output
            logger.info(
                f"Evaluation run completed for plan: {plan_id}, "
                f"revision: {revision}, check number: {check_num}"
            )
            await send_update(plan_id, STEP_ID + check_num, AGENT_NAME, "completed")
            return eval
        except Exception as e:
            await send_update(plan_id, STEP_ID + check_num, AGENT_NAME, "failed")
            logger.error(
                f"Evaluation run failed for plan: {plan_id}, "
                f"revision: {revision}, check number: {check_num}: {e}"
            )
            return None


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

    async def run_eval_func(check_num: int) -> EvaluationResult | None:
        return await run_eval(
            plan_id=plan.id, revision=revision, server=server, check_num=check_num
        )

    with custom_span(
        name="Evaluation",
        data={"Plan Id": plan.id, "Revision": revision, "Checks": checks},
    ):
        await send_update(plan.id, STEP_ID, AGENT_NAME, "running")
        logger.info(
            f"Evaluating results for plan: {plan.id}, revision: {revision}, "
            f"checks: {checks}"
        )
        try:
            futures = [run_eval_func(check_num=i) for i in range(1, checks + 1)]
            results: list[EvaluationResult | None] = await asyncio.gather(*futures)
            evaluations = process_evals(results, checks, logger)
            logger.info(
                f"Evaluation results for plan {plan.id}, revision {revision}: "
                f"Score: {evaluations.score:0.2f}% - "
                f"Status: {'PASS' if evaluations.passed else 'FAIL'}"
            )
            await send_update(plan.id, STEP_ID, AGENT_NAME, "completed")
            return evaluations
        except Exception as e:
            await send_update(plan.id, STEP_ID, AGENT_NAME, "failed")
            logger.error(
                f"Evaluation failed for plan: {plan.id}, revision: {revision}: {e}"
            )
            raise e
