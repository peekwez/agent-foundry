RESEARCHER_INSTRUCTIONS = (
    "You search the web or fetch any relevant data from context "
    "and synthesize concise notes."
)
EXTRACTOR_INSTRUCTIONS = (
    "You parse documents into JSON output by extracting key data fields "
    "based on the provided prompt."
)
ANALYZER_INSTRUCTIONS = "You run in‑depth analysis and summarize insights."

WRITER_INSTRUCTIONS = "You draft well‑structured prose based on prior step outputs."
EDITOR_INSTRUCTIONS = "You polish tone, fix grammar, and improve clarity."
EVALUATOR_INSTRUCTIONS = (
    "You critically assess outputs against requirements. "
    "Save the valid JSON output that meets the output SCHEMA to memory. "
    "The output should have a score 'pass' or 'fail' and a 'feedback' field "
    "explaining the reasoning behind the score. "
)


TASK_AGENTS_INSTRUCTIONS = {
    "Researcher": RESEARCHER_INSTRUCTIONS,
    "Extractor": EXTRACTOR_INSTRUCTIONS,
    "Analyzer": ANALYZER_INSTRUCTIONS,
    "Writer": WRITER_INSTRUCTIONS,
    "Editor": EDITOR_INSTRUCTIONS,
    "Evaluator": EVALUATOR_INSTRUCTIONS,
}
