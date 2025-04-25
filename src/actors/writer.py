from actors.base import build_agent

writer = build_agent(
    name="Writer",
    instructions="You draft well‑structured prose based on prior step outputs.",
)
