# from rich import console

# from ferros.core.stream import stream_updates


# async def print_stream_updates(plan_id: str) -> None:
#     """
#     Print the stream updates for a given plan ID.

#     Args:
#         plan_id (str): The ID of the plan.
#     """
#     screen = console.Console()
#     try:
#         screen.print(f"Starting to stream updates for plan ID: {plan_id}")
#         await stream_updates(plan_id, screen)
#     except Exception as e:
#         screen.print(f"An error occurred while streaming updates: {e}")
