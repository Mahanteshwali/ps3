"""
Ingestion router — accepts raw logs from all three layers,
normalizes them, and pushes them onto the Redis Stream.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict
import logging

from ingestion.normalizer import normalize
from ingestion.redis_producer import publish_event

router = APIRouter()
logger = logging.getLogger(__name__)


class LogPayload(BaseModel):
    """Flexible log payload — any key-value pairs accepted."""
    model_config = {"extra": "allow"}


@router.post("/network", summary="Ingest a network-layer log event")
async def ingest_network(payload: LogPayload):
    return await _ingest(payload.model_dump(), "network")


@router.post("/endpoint", summary="Ingest an endpoint-layer log event")
async def ingest_endpoint(payload: LogPayload):
    return await _ingest(payload.model_dump(), "endpoint")


@router.post("/application", summary="Ingest an application-layer log event")
async def ingest_application(payload: LogPayload):
    return await _ingest(payload.model_dump(), "application")


async def _ingest(raw: Dict[str, Any], layer: str) -> Dict[str, Any]:
    try:
        event = normalize(raw, layer)  # type: ignore[arg-type]
        stream_id = await publish_event(event)
        logger.info(f"Ingested [{layer}] event {event['event_id']} → {stream_id}")
        return {
            "status": "accepted",
            "event_id": event["event_id"],
            "layer": layer,
            "stream_id": stream_id,
        }
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
