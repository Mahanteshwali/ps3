"""
Alerts router — REST API for querying stored threat alerts.
Includes a Server-Sent Events (SSE) endpoint for real-time dashboard feed.
"""
import asyncio
import json
import logging
import os
from typing import Optional

import redis.asyncio as aioredis
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from db.mongo_client import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", summary="List all alerts (paginated)")
async def list_alerts(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    severity: Optional[str] = Query(None, description="Filter by severity: LOW|MEDIUM|HIGH|CRITICAL"),
    threat_type: Optional[str] = Query(None, description="Filter by threat type"),
):
    db = get_db()
    query: dict = {}
    if severity:
        query["severity"] = severity.upper()
    if threat_type:
        query["threat_type"] = threat_type.lower()

    skip = (page - 1) * limit
    cursor = db["alerts"].find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
    alerts = await cursor.to_list(length=limit)
    total = await db["alerts"].count_documents(query)

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "alerts": alerts,
    }


@router.get("/stats", summary="Alert severity & type counts")
async def alert_stats():
    db = get_db()
    pipeline = [
        {"$group": {"_id": "$severity", "count": {"$sum": 1}}},
    ]
    severity_counts = {
        doc["_id"]: doc["count"]
        async for doc in db["alerts"].aggregate(pipeline)
    }
    pipeline2 = [
        {"$group": {"_id": "$threat_type", "count": {"$sum": 1}}},
    ]
    type_counts = {
        doc["_id"]: doc["count"]
        async for doc in db["alerts"].aggregate(pipeline2)
    }
    total = await db["alerts"].count_documents({})
    return {
        "total": total,
        "by_severity": severity_counts,
        "by_threat_type": type_counts,
    }


@router.get("/live", summary="SSE stream of real-time alerts")
async def live_alerts():
    """
    Server-Sent Events endpoint.
    Uses Redis Pub/Sub with listen() (proper async blocking) as the
    message source, bridged via asyncio.Queue so keep-alives still work.
    """
    redis_url = os.getenv("REDIS_URL", "redis://127.0.0.1:16379")

    async def event_generator():
        queue: asyncio.Queue = asyncio.Queue()

        # Background task: subscribe and push every alert into the local queue
        async def _listen():
            r = await aioredis.from_url(redis_url, decode_responses=True)
            pubsub = r.pubsub()
            await pubsub.subscribe("alerts:live")
            try:
                async for message in pubsub.listen():
                    if message.get("type") == "message":
                        await queue.put(message["data"])
            except asyncio.CancelledError:
                pass
            finally:
                await pubsub.unsubscribe("alerts:live")
                await r.aclose()

        listener_task = asyncio.create_task(_listen())

        yield ": keep-alive\n\n"
        try:
            while True:
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {data}\n\n"
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            listener_task.cancel()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{alert_id}", summary="Get a single alert with explanation and playbook")
async def get_alert(alert_id: str):
    db = get_db()
    alert = await db["alerts"].find_one({"alert_id": alert_id}, {"_id": 0})
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found.")
    return alert
