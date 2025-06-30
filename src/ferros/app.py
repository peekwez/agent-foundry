import uuid
from typing import Annotated, Any

import arrow
import uvicorn
from fastapi import FastAPI, File, Form, UploadFile, WebSocket, WebSocketDisconnect
from pydantic import AnyUrl

from ferros.core.logging import get_logger
from ferros.core.store import save_file
from ferros.messaging.producer import publish_task
from ferros.messaging.streamer import stream_task_updates
from ferros.models.task import TaskConfig

app = FastAPI(
    title="Agent foundry API",
    description=(
        "API for the Agent foundry, a knowledge worker agent. "
        "This API allows users to run tasks with the agent, "
        "submit files, and receive updates on task progress."
    ),
    version="0.1.0",
)
started = arrow.now("Canada/Eastern")


@app.get("/")
def home() -> dict[str, str]:
    """
    Home endpoint to verify the server is running.

    Returns:
        dict: A dictionary indicating the server is running.
    """

    return {
        "name": app.title,
        "description": app.description,
        "message": "Welcome to the Agent foundry API!",
        "timestamp": arrow.now("Canada/Eastern").format("MMM DD, YYYY HH:mm:ss"),
        "version": app.version,
        "uptime": started.humanize(locale="en"),
        "status": "running",
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    """
    Health check endpoint to verify the server is running.

    Returns:
        dict: A dictionary indicating the server is healthy.
    """
    return {"status": "healthy"}


@app.post("/run-task/json")
async def run_task(task_config: TaskConfig) -> dict[str, str]:
    """
    Run the agent with the provided input.

    Returns:
        dict: A dictionary indicating the agent has been run.
    """
    await publish_task(task_config)
    return {"task_id": task_config.trace_id, "status": "task published"}


@app.post("/run-task/form")
async def run_task_form(
    goal: Annotated[str, Form()],
    files: Annotated[list[UploadFile], File()],
    context_urls: Annotated[str, Form()] = "",
    revisions: Annotated[int, Form()] = 2,
) -> dict[str, Any]:
    """
    Run the agent with the provided form data.

    Returns:
        dict: A dictionary indicating the agent has been run.
    """
    # upload file to mcp blackboard server and use response to create
    # contexts - https, http, s3, abs, etc.
    trace_id = f"{uuid.uuid4().hex}"
    contexts: list[AnyUrl] = []

    # Parse any provided context URLs
    if context_urls:
        url_list = [url.strip() for url in context_urls.split(",")]
        for url in url_list:
            if url:
                contexts.append(AnyUrl(url))

    # Process uploaded files
    for file in files:
        data = await file.read()
        ret: dict[str, str] = await save_file(
            data, trace_id, file.filename if file.filename else "file"
        )
        contexts.append(AnyUrl(ret.get("file_url", "")))

    task = TaskConfig(
        goal=goal, contexts=contexts, revisions=revisions, trace_id=trace_id
    )
    await publish_task(task)
    return {"task_id": task.trace_id, "status": "task published"}


@app.websocket("/ws/run-task/updates")
async def websocket_endpoint(websocket: WebSocket) -> None:
    logger = get_logger(__name__)
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json(mode="text")
            await websocket.send_text(f"Message received: {data}")

            task_id = data.get("task_id", None)
            if not task_id:
                await websocket.send_text("No task ID provided.")
                continue

            async for update in stream_task_updates(task_id):
                logger.info(f"Update for task {task_id}: {update}")
                await websocket.send_json(update)

    except WebSocketDisconnect:
        logger.info("Client disconnected from WebSocket.")


def run_app(host: str = "0.0.0.0", port: int = 5000) -> None:
    """
    Run the FastAPI application.

    Args:
        host (str): The host to run the application on.
        port (int): The port to run the application on.
    """
    uvicorn.run(app, host=host, port=port)
