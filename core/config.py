import os

OPENAI_MODEL = "o3"  # Change to any model available in your org
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
