"""
Log Normalizer — converts heterogeneous log payloads from all three layers
(network, endpoint, application) into a single unified schema.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Literal
import uuid


LayerType = Literal["network", "endpoint", "application"]


def normalize(raw: Dict[str, Any], layer: LayerType) -> Dict[str, Any]:
    """
    Normalize a raw log payload into the unified threat event schema.

    Unified Schema:
    {
        "event_id":    str   — unique UUID
        "timestamp":   str   — ISO8601 UTC
        "layer":       str   — network | endpoint | application
        "source_ip":   str
        "dest_ip":     str | None
        "event_type":  str   — e.g. "failed_login", "dns_query", "file_write"
        "username":    str | None
        "bytes":       int   — bytes transferred (0 if N/A)
        "status":      str | None — e.g. "failure", "success", "blocked"
        "extra":       dict  — layer-specific fields preserved as-is
        "raw":         dict  — original payload
    }
    """
    now = datetime.now(timezone.utc).isoformat()

    base = {
        "event_id": str(uuid.uuid4()),
        "timestamp": raw.get("timestamp", now),
        "layer": layer,
        "source_ip": raw.get("source_ip", raw.get("src_ip", raw.get("ip", "0.0.0.0"))),
        "dest_ip": raw.get("dest_ip", raw.get("dst_ip", raw.get("target_ip", None))),
        "event_type": _extract_event_type(raw, layer),
        "username": raw.get("username", raw.get("user", raw.get("account", None))),
        "bytes": int(raw.get("bytes", raw.get("bytes_sent", raw.get("size", 0)))),
        "status": raw.get("status", raw.get("result", raw.get("outcome", None))),
        "extra": _extract_extra(raw, layer),
        "raw": raw,
    }
    return base


def _extract_event_type(raw: Dict[str, Any], layer: LayerType) -> str:
    """Best-effort event type extraction per layer."""
    if "event_type" in raw:
        return raw["event_type"]
    if layer == "network":
        return raw.get("protocol", "network_traffic").lower()
    if layer == "endpoint":
        return raw.get("action", raw.get("event", "endpoint_event")).lower()
    if layer == "application":
        return raw.get("log_type", raw.get("action", "app_event")).lower()
    return "unknown"


def _extract_extra(raw: Dict[str, Any], layer: LayerType) -> Dict[str, Any]:
    """Preserve layer-specific fields that don't map to the base schema."""
    standard_keys = {
        "timestamp", "source_ip", "src_ip", "ip", "dest_ip", "dst_ip",
        "target_ip", "event_type", "username", "user", "account",
        "bytes", "bytes_sent", "size", "status", "result", "outcome",
    }
    return {k: v for k, v in raw.items() if k not in standard_keys}
