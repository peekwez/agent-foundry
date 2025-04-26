import os
import pathlib


OPENAI_MODEL = "o3"  # Change to any model available in your org
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CONTEXT_STORAGE_PATH = pathlib.Path(__file__).parent.parent.parent / "tmp"
RESULTS_STORAGE_PATH = pathlib.Path(__file__).parent.parent.parent / "results"
