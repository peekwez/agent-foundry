from __future__ import annotations

import http.server
import socketserver

from codename import codename  # type: ignore
from redis import ResponseError

from ferros.agents.runner import run_agent
from ferros.core.logging import get_logger
from ferros.core.utils import get_redis_client
from ferros.messaging.constants import GROUP_NAME, STREAM_NAME
from ferros.models.task import TaskConfig

HEALTH_PORT = 5050


class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
    """
    A simple HTTP request handler for health checks.
    Responds with a 200 OK status and a message indicating the service is healthy.
    """

    def do_GET(self) -> None:
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK\n")
        else:
            self.send_response(404)
            self.end_headers()


def start_health_check_server(host: str = "0.0.0.0", port: int = HEALTH_PORT) -> None:
    """
    Start a simple HTTP server for health checks.
    This server listens on the specified port and responds to GET requests
    at the /health endpoint with a 200 OK status.

    Args:
        port (int): The port on which the health check server will listen.
    """
    logger = get_logger(__name__)
    logger.info(f"Starting health check server on {host}:{port}")
    with socketserver.TCPServer((host, port), HealthCheckHandler) as httpd:
        logger.info(f"Health check server started at http://{host}:{port}/health")
        httpd.serve_forever()


async def consume_tasks() -> None:
    """
    Consume tasks from the Redis stream and process them using the agent.
    This function creates a Redis stream group if it does not exist,
    then continuously reads messages from the stream and processes them
    using the `run_agent` function. Each message is expected to be a JSON
    """

    logger = get_logger(__name__)

    redis = get_redis_client()
    try:
        redis.xgroup_create(
            name=STREAM_NAME, groupname=GROUP_NAME, id="0", mkstream=True
        )
    except ResponseError:
        logger.info(f"Group `{GROUP_NAME}` already exists.")

    consumer_name = codename(separator="-")
    logger.info(f"Starting task consumer with name: {consumer_name}")

    try:
        while True:
            response = redis.xreadgroup(
                groupname=GROUP_NAME,
                consumername=consumer_name,
                streams={STREAM_NAME: ">"},
                count=1,
                block=5000,
            )
            if response:
                _, messages = response[0]  # type: ignore
                for message_id, message in messages:  # type: ignore
                    config = TaskConfig.model_validate_json(message["data"])  # type: ignore
                    try:
                        logger.info(f"Processing task with ID: {config.trace_id}")
                        await run_agent(
                            user_input=config.goal,
                            context_input=config.context_strings,
                            revisions=config.revisions,
                            trace_id=config.trace_id,
                        )

                    except Exception as e:
                        logger.error(
                            f"Error processing task with ID {config.trace_id}: {e}"
                        )
                    else:
                        logger.info(
                            f"Task with ID {config.trace_id} processed successfully."
                        )
                    finally:
                        redis.xack(STREAM_NAME, GROUP_NAME, message_id)  # type: ignore
                    logger.info(f"Processed task with ID: {config.trace_id}")
                    # Process the task data here
    except Exception as e:
        logger.error(f"Error processing task: {e}")
    except KeyboardInterrupt:
        logger.info("Task consumer stopped by user.")
