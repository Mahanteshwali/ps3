"""
Redis Stream Consumer — background worker that reads events from the
threat-events stream and drives the detection pipeline.

This module is designed to run as a standalone process:
    python -m detection.stream_consumer
"""
import asyncio
import json
import logging
import os
import signal
import sys

import redis.asyncio as aioredis
from dotenv import load_dotenv

load_dotenv()

from detection.detector import process_event
from db.mongo_client import connect_db, get_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
STREAM_NAME = os.getenv("REDIS_STREAM", "threat-events")
GROUP_NAME = os.getenv("REDIS_CONSUMER_GROUP", "threat-detector")
CONSUMER_NAME = os.getenv("REDIS_CONSUMER_NAME", "worker-1")
BATCH_SIZE = 50          # events per read call
BLOCK_MS = 1000          # block-wait in ms if stream is empty

# SSE broadcast queue (shared with the alerts router)
_sse_queue: asyncio.Queue = asyncio.Queue(maxsize=500)


def get_sse_queue() -> asyncio.Queue:
    return _sse_queue


async def _ensure_group(r: aioredis.Redis):
    """Create the consumer group if it doesn't exist yet."""
    try:
        await r.xgroup_create(STREAM_NAME, GROUP_NAME, id="0", mkstream=True)
        logger.info(f"Created consumer group '{GROUP_NAME}' on stream '{STREAM_NAME}'")
    except Exception as e:
        if "BUSYGROUP" in str(e):
            logger.debug("Consumer group already exists — OK")
        else:
            raise


async def run():
    """Main consumer loop."""
    await connect_db()
    db = get_db()
    r = await aioredis.from_url(REDIS_URL, decode_responses=True)
    await _ensure_group(r)

    logger.info(f"🟢 Stream consumer running — reading from '{STREAM_NAME}'")

    loop_running = True

    def _handle_signal(sig, frame):
        nonlocal loop_running
        logger.info(f"Received signal {sig} — shutting down worker...")
        loop_running = False

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    processed = 0

    while loop_running:
        try:
            messages = await r.xreadgroup(
                groupname=GROUP_NAME,
                consumername=CONSUMER_NAME,
                streams={STREAM_NAME: ">"},
                count=BATCH_SIZE,
                block=BLOCK_MS,
            )

            if not messages:
                continue

            for _stream, entries in messages:
                for entry_id, fields in entries:
                    try:
                        raw_data = fields.get("data", "{}")
                        event = json.loads(raw_data)

                        # Run detection pipeline
                        alert = process_event(event)

                        # Persist log
                        await db["logs"].insert_one({**event, "_id": event["event_id"]})

                        if alert:
                            doc = alert.model_dump()
                            doc["_id"] = doc["alert_id"]
                            await db["alerts"].insert_one(doc)

                            # Broadcast via Redis Pub/Sub so API SSE endpoint gets it
                            await r.publish("alerts:live", json.dumps(doc, default=str))

                            # Also put in local SSE queue (fallback if in-process)
                            if not _sse_queue.full():
                                await _sse_queue.put(doc)

                        # Acknowledge message
                        await r.xack(STREAM_NAME, GROUP_NAME, entry_id)
                        processed += 1

                        if processed % 500 == 0:
                            logger.info(f"Processed {processed} events total")

                    except Exception as e:
                        logger.error(f"Error processing entry {entry_id}: {e}", exc_info=True)
                        # Don't ack — let it be retried via PEL

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Stream read error: {e}", exc_info=True)
            await asyncio.sleep(1)

    await r.aclose()
    logger.info("Worker stopped.")


if __name__ == "__main__":
    asyncio.run(run())
