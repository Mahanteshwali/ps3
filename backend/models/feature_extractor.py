"""
Feature Extractor — converts a normalized event (or a window of events)
into a numeric feature vector for the ML classifier.
"""
from typing import Any, Dict, List
import numpy as np


# Feature vector schema (order matters — must match training)
FEATURE_NAMES = [
    "failed_login_count",       # failed login attempts in window
    "unique_source_ips",        # distinct source IPs seen
    "unique_dest_ips",          # distinct destination IPs seen
    "total_bytes",              # total bytes in window
    "avg_bytes_per_event",      # mean bytes per event
    "event_count",              # total events in window
    "internal_lateral_conns",   # internal-to-internal unique pairs
    "dns_query_count",          # number of DNS queries
    "outbound_bytes",           # bytes to external IPs (dest_ip starts with non-10/172/192)
    "cross_layer_count",        # number of distinct layers seen
    "failure_ratio",            # ratio of failed/error events to total
    "short_interval_bursts",    # events arriving in rapid succession (proxy: event_count)
]


def _is_internal(ip: str | None) -> bool:
    if not ip:
        return False
    return (
        ip.startswith("10.")
        or ip.startswith("192.168.")
        or ip.startswith("172.")
    )


def extract_features(events: List[Dict[str, Any]]) -> np.ndarray:
    """
    Extract a fixed-length feature vector from a list of normalized events
    (typically a time-window batch for a single source IP).
    Returns shape (1, len(FEATURE_NAMES)).
    """
    if not events:
        return np.zeros((1, len(FEATURE_NAMES)))

    failed_logins = sum(
        1 for e in events
        if e.get("event_type") in ("failed_login", "login_failure", "auth_failure")
        or e.get("status") in ("failure", "failed", "error", "reject")
    )

    source_ips = {e.get("source_ip") for e in events if e.get("source_ip")}
    dest_ips = {e.get("dest_ip") for e in events if e.get("dest_ip")}

    total_bytes = sum(e.get("bytes", 0) for e in events)
    event_count = len(events)
    avg_bytes = total_bytes / event_count if event_count else 0

    # Lateral movement: internal → internal connections
    lateral_pairs = {
        (e.get("source_ip"), e.get("dest_ip"))
        for e in events
        if _is_internal(e.get("source_ip")) and _is_internal(e.get("dest_ip"))
        and e.get("source_ip") != e.get("dest_ip")
    }

    dns_count = sum(
        1 for e in events
        if e.get("event_type") in ("dns_query", "dns_request", "dns")
        or e.get("extra", {}).get("protocol", "").lower() == "dns"
    )

    outbound_bytes = sum(
        e.get("bytes", 0) for e in events
        if not _is_internal(e.get("dest_ip")) and e.get("dest_ip")
    )

    layers = {e.get("layer") for e in events if e.get("layer")}

    failures = sum(
        1 for e in events
        if e.get("status") in ("failure", "failed", "error", "reject", "blocked")
    )
    failure_ratio = failures / event_count if event_count else 0.0

    features = np.array([[
        failed_logins,
        len(source_ips),
        len(dest_ips),
        total_bytes,
        avg_bytes,
        event_count,
        len(lateral_pairs),
        dns_count,
        outbound_bytes,
        len(layers),
        failure_ratio,
        event_count,  # burst proxy
    ]], dtype=np.float64)

    return features
