# backend/utils/redis_cache.py
# Simple Redis get/set helpers.
# Always fails silently — cache is optional, never blocks the user.

import json
import redis.asyncio as aioredis
from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

# Single global Redis client (connection pool managed internally)
redis_client = aioredis.from_url(
    settings.redis_url,
    encoding="utf-8",
    decode_responses=True
)

# ─── Cache key patterns (document these centrally) ────────────────────────────
# LLM response cache:    "llm:{md5(prompt)}"         TTL: 3600s  (1 hour)
# JD extraction cache:   "jd:{md5(jd_text)}"         TTL: 86400s (24 hours)
# Resume parse cache:    "resume:{md5(raw_text)}"     TTL: 3600s  (1 hour)
# ──────────────────────────────────────────────────────────────────────────────


async def get_cache(key: str) -> dict | None:
    """
    Retrieve a cached dict by key.
    Returns None on cache miss OR any Redis error.
    """
    try:
        value = await redis_client.get(key)
        if value:
            logger.info(f"Cache HIT: {key}")
            return json.loads(value)
        logger.info(f"Cache MISS: {key}")
        return None
    except Exception as e:
        logger.warning(f"Redis get failed (key={key}): {e} — falling through")
        return None


async def set_cache(key: str, value: dict, ttl: int = 3600) -> None:
    """
    Store a dict in Redis with TTL (seconds).
    Fails silently — caching is never a hard requirement.
    """
    try:
        await redis_client.setex(key, ttl, json.dumps(value))
        logger.info(f"Cache SET: {key} (TTL={ttl}s)")
    except Exception as e:
        logger.warning(f"Redis set failed (key={key}): {e} — continuing without cache")


async def delete_cache(key: str) -> None:
    """Delete a cache entry."""
    try:
        await redis_client.delete(key)
    except Exception as e:
        logger.warning(f"Redis delete failed (key={key}): {e}")


async def check_redis_health() -> bool:
    """Ping Redis — used in health check endpoint."""
    try:
        await redis_client.ping()
        return True
    except Exception:
        return False
