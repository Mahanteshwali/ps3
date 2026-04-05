"""
Explainability Engine — produces human-readable explanations for each threat.
Uses template-based reasoning tied to the top contributing features.
"""
from typing import Any, Dict, List


# Templates per threat type.
# Placeholders are filled from the aggregated set of events.
_TEMPLATES: Dict[str, str] = {
    "brute_force": (
        "Detected Brute Force attack: {failed_logins} failed login attempts "
        "in {window_sec}s from IP {source_ip}. "
        "Failure ratio: {failure_ratio:.0%}. "
        "Threshold exceeded by {excess}×."
    ),
    "lateral_movement": (
        "Detected Lateral Movement: host {source_ip} made connections to "
        "{dest_count} internal endpoints across {layer_count} layer(s). "
        "Unusual internal traversal pattern detected."
    ),
    "data_exfiltration": (
        "Detected Data Exfiltration: {mb_out:.1f} MB transferred to external "
        "destination(s) from {source_ip} — {excess}× above normal baseline. "
        "Occurred across {layer_count} layer(s)."
    ),
    "command_and_control": (
        "Detected Command & Control (C2) beaconing: {source_ip} made "
        "{dns_count} DNS queries and {event_count} outbound calls in a "
        "regular interval pattern. Consistent with C2 communication."
    ),
    "false_positive": (
        "Possible False Positive: activity from {source_ip} triggered "
        "{failed_logins} failed login attempts but patterns are consistent "
        "with an authorised scanner or monitoring tool (moderate failure "
        "ratio: {failure_ratio:.0%})."
    ),
    "benign": (
        "No threat detected. Traffic from {source_ip} is within normal "
        "baseline parameters."
    ),
}

_BRUTE_FORCE_THRESHOLD = 10    # failed logins considered baseline


def generate_explanation(
    threat_type: str,
    events: List[Dict[str, Any]],
    confidence: float,
    window_sec: int = 120,
) -> str:
    """
    Build a human-readable explanation string for a detected threat.
    """
    source_ip = _most_common_source(events)
    failed_logins = sum(
        1 for e in events
        if e.get("status") in ("failure", "failed", "error", "reject")
        or e.get("event_type") in ("failed_login", "login_failure", "auth_failure")
    )
    dest_ips = {e.get("dest_ip") for e in events if e.get("dest_ip")}
    dns_count = sum(
        1 for e in events
        if e.get("event_type") in ("dns_query", "dns_request", "dns")
    )
    total_bytes = sum(e.get("bytes", 0) for e in events)
    outbound_bytes = sum(
        e.get("bytes", 0) for e in events
        if _is_external(e.get("dest_ip"))
    )
    layers = {e.get("layer") for e in events if e.get("layer")}
    failure_ratio = failed_logins / len(events) if events else 0.0

    ctx = {
        "source_ip": source_ip,
        "failed_logins": failed_logins,
        "window_sec": window_sec,
        "failure_ratio": failure_ratio,
        "excess": max(1, round(failed_logins / max(_BRUTE_FORCE_THRESHOLD, 1))),
        "dest_count": len(dest_ips),
        "layer_count": len(layers),
        "mb_out": outbound_bytes / (1024 * 1024),
        "dns_count": dns_count,
        "event_count": len(events),
        "total_mb": total_bytes / (1024 * 1024),
    }

    template = _TEMPLATES.get(threat_type, "Threat detected: {threat_type}.")
    try:
        return template.format(**ctx)
    except KeyError:
        return f"Threat detected: {threat_type} (confidence {confidence:.0%})."


def _most_common_source(events: List[Dict[str, Any]]) -> str:
    from collections import Counter
    ips = [e.get("source_ip", "unknown") for e in events]
    if not ips:
        return "unknown"
    return Counter(ips).most_common(1)[0][0]


def _is_external(ip: str | None) -> bool:
    if not ip:
        return False
    return not (
        ip.startswith("10.")
        or ip.startswith("192.168.")
        or ip.startswith("172.")
    )
