from actors.base import build_agent

editor = build_agent(
    name="Editor",
    instructions="You polish tone, fix grammar and improve clarity.",
    model="o3",
)
