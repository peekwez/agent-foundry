from actors.base import build_agent

extractor = build_agent(
    name="Extractor",
    instructions=(
        "You parse documents into JSON output by extracting key data "
        "fields based on the provided prompt."
    ),
    model="o3",
    task_agent=True,
)
