# Optional: helper to run the worker programmatically if you prefer
from rq import Worker, Queue, Connection
import os, redis

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_conn = redis.from_url(REDIS_URL)
if __name__ == "__main__":
    with Connection(redis_conn):
        q = Queue()
        worker = Worker([q])
        worker.work()
