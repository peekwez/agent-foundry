from redis import Redis

from core.config import REDIS_URL


class RedisMemory:
    def __init__(self):
        self.r = Redis.from_url(REDIS_URL, decode_responses=True)

    def set(self, key: str, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("Value must be a string")
        self.r.set(key, value)

    def get(self, key: str):
        v = self.r.get(key)
        return v

    # def append_history(self, thread_id: str, role: str, content: str):
    #     self.r.rpush(
    #         f"history:{thread_id}", json.dumps({"role": role, "content": content})
    #     )

    # def fetch_history(self, thread_id: str, k: int = 20):
    #     raw = self.r.lrange(f"history:{thread_id}", -k, -1)
    #     return [json.loads(x) for x in raw]

    # def new_thread(self) -> str:
    #     return str(uuid.uuid4())
