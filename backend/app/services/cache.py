from functools import lru_cache

import redis

from app.config import settings


@lru_cache(maxsize=1)
def get_redis_client() -> redis.Redis:
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)


def safe_get(key: str):
    try:
        return get_redis_client().get(key)
    except Exception:
        return None


def safe_setex(key: str, ttl: int, value: str = "1") -> bool:
    try:
        return bool(get_redis_client().setex(key, ttl, value))
    except Exception:
        return False


def safe_delete(key: str) -> bool:
    try:
        return bool(get_redis_client().delete(key))
    except Exception:
        return False


def increment_with_ttl(key: str, ttl: int) -> int:
    client = get_redis_client()
    try:
        pipe = client.pipeline()
        pipe.incr(key)
        pipe.expire(key, ttl)
        count, _ = pipe.execute()
        return int(count)
    except Exception:
        return 0
