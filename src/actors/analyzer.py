from actors.base import build_agent

analyzer = build_agent(
    name="Analyzer",
    instructions="You run in‑depth analysis and summarize insights.",
    model="o3",
    task_agent=True,
)
