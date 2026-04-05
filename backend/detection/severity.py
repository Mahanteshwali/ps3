"""
Severity mapper — translates (threat_type, confidence) into a severity level.
"""
from typing import Literal

SeverityLevel = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]

# Base severity by threat type
_BASE: dict[str, SeverityLevel] = {
    "brute_force":          "MEDIUM",
    "lateral_movement":     "HIGH",
    "data_exfiltration":    "CRITICAL",
    "command_and_control":  "CRITICAL",
    "false_positive":       "LOW",
    "benign":               "LOW",
}

# Confidence thresholds to upgrade severity
_UPGRADES: list[tuple[float, int]] = [
    # (min_confidence, levels_to_upgrade)
    (0.90, 1),
    (0.75, 0),
]


_LEVELS: list[SeverityLevel] = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


def get_severity(threat_type: str, confidence: float) -> SeverityLevel:
    """
    Return severity level given threat type and classifier confidence.
    High-confidence detections are bumped up one level.
    """
    base = _BASE.get(threat_type, "MEDIUM")
    idx = _LEVELS.index(base)

    for min_conf, upgrade in _UPGRADES:
        if confidence >= min_conf:
            idx = min(idx + upgrade, len(_LEVELS) - 1)
            break

    # Benign and false positives never escalate beyond LOW
    if threat_type in ("benign", "false_positive"):
        return "LOW"

    return _LEVELS[idx]
