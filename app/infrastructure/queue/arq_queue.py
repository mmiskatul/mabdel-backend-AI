from urllib.parse import urlparse
from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from app.domain.interfaces.queue import JobQueue
from app.shared.config import get_settings


def redis_settings() -> RedisSettings:
    parsed = urlparse(get_settings().redis_url)
    return RedisSettings(
        host=parsed.hostname or "redis",
        port=parsed.port or 6379,
        database=int((parsed.path or "/0").lstrip("/") or 0),
    )


class ArqJobQueue(JobQueue):
    def __init__(self):
        self._pool: ArqRedis | None = None

    async def _get_pool(self) -> ArqRedis:
        if self._pool is None:
            self._pool = await create_pool(redis_settings())
        return self._pool

    async def enqueue(self, name: str, payload: dict) -> str:
        pool = await self._get_pool()
        job = await pool.enqueue_job(name, payload)
        return job.job_id if job else ""

