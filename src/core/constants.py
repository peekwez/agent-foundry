from pathlib import Path

from core.models import AgentName

RESULTS_STORAGE_PATH = Path(__file__).parents[2] / "tmp/results"

RESEARCHER_INSTRUCTIONS = (
    "You search the web or fetch any relevant data from context\n"
    "and synthesize concise notes."
)
EXTRACTOR_INSTRUCTIONS = (
    "You parse documents into JSON output by extracting key data fields\n"
    "based on the provided prompt."
)
ANALYZER_INSTRUCTIONS = "You run in‑depth analysis and summarize insights."

WRITER_INSTRUCTIONS = "You draft well‑structured prose based on prior step outputs."
EDITOR_INSTRUCTIONS = "You polish tone, fix grammar, and improve clarity."
EVALUATOR_INSTRUCTIONS = (
    "You critically assess outputs against requirements. \n"
    "You must save the evaluation result based on the output SCHEMA using \n"
    "the `write_result` function. The output should have a score 'pass' or \n"
    "'fail' and a 'feedback' field explaining the reasoning behind the score."
)


TASK_AGENTS_INSTRUCTIONS = {
    AgentName.RESEARCHER.value: RESEARCHER_INSTRUCTIONS,
    AgentName.EXTRACTOR.value: EXTRACTOR_INSTRUCTIONS,
    AgentName.ANALYZER.value: ANALYZER_INSTRUCTIONS,
    AgentName.WRITER.value: WRITER_INSTRUCTIONS,
    AgentName.EDITOR.value: EDITOR_INSTRUCTIONS,
    AgentName.EVALUATOR.value: EVALUATOR_INSTRUCTIONS,
}
