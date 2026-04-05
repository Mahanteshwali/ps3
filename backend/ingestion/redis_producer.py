"""
Redis Streams producer — publishes normalized events to the threat-events stream.
"""
import json
import logging
import os
from typing import Any, Dict

import redis.asyncio as aioredis
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

_redis: aioredis.Redis | None = None
STREAM_NAME = os.getenv("REDIS_STREAM", "threat-events")
MAX_STREAM_LEN = 100_000  # cap stream to avoid runaway memory


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        url = os.getenv("REDIS_URL", "redis://localhost:6379")
        _redis = aioredis.from_url(url, decode_responses=True)
        logger.info(f"Connected to Redis at {url}")
    return _redis


async def publish_event(event: Dict[str, Any]) -> str:
    """
    Publish a normalized event dict to the Redis Stream.
    Returns the generated stream entry ID.
    """
    r = await get_redis()
    # Redis streams require flat string key-value pairs
    payload = {"data": json.dumps(event)}
    entry_id = await r.xadd(STREAM_NAME, payload, maxlen=MAX_STREAM_LEN, approximate=True)
    logger.debug(f"Published event {event.get('event_id')} → stream ID {entry_id}")
    return entry_id


async def close_redis():
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None
