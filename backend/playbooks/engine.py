"""
Playbook Engine — maps threat types to ordered mitigation steps.
"""
from typing import List

_PLAYBOOKS: dict[str, List[str]] = {
    "brute_force": [
        "Block source IP at firewall level",
        "Reset credentials for targeted accounts",
        "Enable account lockout policy (≥5 failures)",
        "Enable Multi-Factor Authentication (MFA)",
        "Review authentication logs for the past 24h",
    ],
    "lateral_movement": [
        "Isolate compromised endpoint(s) from the network",
        "Review and revoke excessive internal access privileges",
        "Audit internal connection logs for affected IP range",
        "Deploy network segmentation rules",
        "Hunt for additional compromised hosts using EDR",
    ],
    "data_exfiltration": [
        "Block outbound traffic to identified external IPs immediately",
        "Alert Data Loss Prevention (DLP) team",
        "Identify and classify data that may have been leaked",
        "Preserve forensic evidence — do not wipe affected systems",
        "Notify legal / compliance team per data breach regulations",
        "Revoke credentials of accounts involved in the transfer",
    ],
    "command_and_control": [
        "Block C2 destination IPs and domains at DNS and firewall",
        "Quarantine the beaconing host",
        "Run malware scan on affected endpoint",
        "Hunt for implant / persistence mechanisms (scheduled tasks, registry)",
        "Rotate all credentials on affected host",
        "Review all outbound DNS queries for similar patterns",
    ],
    "false_positive": [
        "Mark event as acknowledged — no action required",
        "Add source IP to allowlist if it is a known scanner or monitoring tool",
        "Tune detection threshold to reduce future false positives",
    ],
    "benign": [
        "No action required — event is within normal baseline",
    ],
}


def get_playbook(threat_type: str) -> List[str]:
    """Return ordered mitigation steps for the given threat type."""
    return _PLAYBOOKS.get(threat_type, ["Investigate alert manually."])
