"""
Simulation router — triggers synthetic attack scenarios through the
full detection pipeline, enabling demo and validation without real traffic.
"""
import logging
import random
import asyncio
from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ingestion.normalizer import normalize
from ingestion.redis_producer import publish_event

router = APIRouter()
logger = logging.getLogger(__name__)

AttackType = Literal[
    "brute_force",
    "lateral_movement",
    "data_exfiltration",
    "command_and_control",
    "false_positive",
]


class SimulateRequest(BaseModel):
    attack_type: AttackType
    intensity: int = 50          # number of events to generate
    source_ip: Optional[str] = None
    target_ip: Optional[str] = None


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _random_internal_ip() -> str:
    return f"10.0.{random.randint(1, 10)}.{random.randint(2, 254)}"


def _random_external_ip() -> str:
    return f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"


def _generate_events(req: SimulateRequest) -> list[dict]:
    """Generate synthetic raw log events for the requested attack type."""
    src = req.source_ip or _random_internal_ip()
    dst = req.target_ip or _random_internal_ip()
    events = []
    n = req.intensity

    if req.attack_type == "brute_force":
        for _ in range(n):
            events.append({
                "timestamp": _ts(),
                "source_ip": src,
                "dest_ip": dst,
                "event_type": "failed_login",
                "username": "admin",
                "status": "failure",
                "bytes": random.randint(80, 200),
                "protocol": "SSH",
            })

    elif req.attack_type == "lateral_movement":
        for i in range(n):
            target = f"10.0.{random.randint(1, 5)}.{random.randint(2, 50)}"
            events.append({
                "timestamp": _ts(),
                "source_ip": src,
                "dest_ip": target,
                "event_type": "smb_connect",
                "status": "success",
                "bytes": random.randint(500, 5000),
                "protocol": "SMB",
            })

    elif req.attack_type == "data_exfiltration":
        ext_dst = req.target_ip or _random_external_ip()
        for _ in range(n):
            events.append({
                "timestamp": _ts(),
                "source_ip": src,
                "dest_ip": ext_dst,
                "event_type": "large_upload",
                "status": "success",
                "bytes": random.randint(500_000, 2_000_000),
                "protocol": "HTTPS",
            })

    elif req.attack_type == "command_and_control":
        c2_host = req.target_ip or _random_external_ip()
        for i in range(n):
            etype = "dns_query" if i % 3 == 0 else "http_beacon"
            events.append({
                "timestamp": _ts(),
                "source_ip": src,
                "dest_ip": c2_host,
                "event_type": etype,
                "status": "success",
                "bytes": random.randint(200, 2000),
                "protocol": "DNS" if etype == "dns_query" else "HTTP",
            })

    elif req.attack_type == "false_positive":
        # Scanner-like traffic that looks like brute force but is authorised
        for _ in range(n):
            events.append({
                "timestamp": _ts(),
                "source_ip": src,
                "dest_ip": _random_internal_ip(),
                "event_type": "port_scan",
                "status": "failure" if random.random() < 0.45 else "success",
                "bytes": random.randint(60, 150),
                "protocol": "TCP",
                "scanner": "nessus",
            })

    return events


LAYER_MAP: dict[str, list[str]] = {
    "brute_force": ["network", "application"],
    "lateral_movement": ["network", "endpoint"],
    "data_exfiltration": ["network", "application"],
    "command_and_control": ["network", "endpoint"],
    "false_positive": ["network"],
}


@router.post("/attack", summary="Simulate a synthetic attack scenario")
async def simulate_attack(req: SimulateRequest):
    events = _generate_events(req)
    layers = LAYER_MAP.get(req.attack_type, ["network"])
    published = 0

    for i, raw in enumerate(events):
        layer = layers[i % len(layers)]
        normalized = normalize(raw, layer)  # type: ignore[arg-type]
        await publish_event(normalized)
        published += 1
        # Small stagger to mimic real traffic burst
        if i % 10 == 9:
            await asyncio.sleep(0.01)

    logger.info(f"Simulation: {req.attack_type} — {published} events injected")
    return {
        "status": "simulated",
        "attack_type": req.attack_type,
        "events_injected": published,
        "source_ip": req.source_ip or "auto",
        "message": f"Injected {published} synthetic {req.attack_type} events. "
                   "Check /alerts/live for detections.",
    }
