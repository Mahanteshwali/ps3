"""
Dedicated false positive test case (PRD requirement).

Tests that a known-benign scanning tool (e.g. Nessus) that generates
moderate failed-login counts is correctly classified as 'false_positive'
and NOT escalated to a MEDIUM/HIGH/CRITICAL severity alert.
"""
import sys
from pathlib import Path

# Allow import from backend/
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import numpy as np
import pytest

from models.feature_extractor import extract_features, FEATURE_NAMES
from models.threat_classifier import predict, load_model, train_and_save
from detection.severity import get_severity


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module", autouse=True)
def ensure_model():
    """Train model once for all tests in this module."""
    train_and_save()


def make_scanner_events(n: int = 40) -> list[dict]:
    """
    Simulate a Nessus-style vulnerability scanner:
    - Moderate failed logins (~40%)
    - Many dest IPs (sweeping subnet)
    - Low bytes per event
    - Single source IP (known scanner host)
    """
    import random
    events = []
    for i in range(n):
        events.append({
            "event_id": f"fp-test-{i}",
            "timestamp": "2026-01-01T00:00:00Z",
            "layer": "network",
            "source_ip": "10.0.0.99",   # known scanner
            "dest_ip": f"10.0.1.{i % 200 + 2}",
            "event_type": "port_scan",
            "username": None,
            "bytes": random.randint(60, 150),
            "status": "failure" if i % 2 == 0 else "success",
            "extra": {"scanner": "nessus"},
            "raw": {},
        })
    return events


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestFalsePositiveScenario:

    def test_scanner_events_classified_as_false_positive_or_benign(self):
        """
        A Nessus-like scanner should NOT be classified as brute_force.
        Expected: 'false_positive' or 'benign'.
        """
        events = make_scanner_events(40)
        features = extract_features(events)
        result = predict(features)

        assert result["threat_type"] in ("false_positive", "benign"), (
            f"Expected false_positive/benign but got '{result['threat_type']}' "
            f"(confidence={result['confidence']:.2f}). "
            f"Probabilities: {result['probabilities']}"
        )

    def test_false_positive_severity_is_always_low(self):
        """
        Even at high confidence, false_positive severity must be LOW.
        """
        for confidence in [0.55, 0.75, 0.90, 0.99]:
            sev = get_severity("false_positive", confidence)
            assert sev == "LOW", (
                f"false_positive at confidence={confidence} should be LOW, got {sev}"
            )

    def test_benign_severity_is_always_low(self):
        """Benign events must never escalate beyond LOW."""
        for confidence in [0.55, 0.80, 0.99]:
            sev = get_severity("benign", confidence)
            assert sev == "LOW", f"benign at {confidence} should be LOW, got {sev}"

    def test_feature_vector_shape(self):
        """Feature extractor must produce a vector matching FEATURE_NAMES length."""
        events = make_scanner_events(10)
        features = extract_features(events)
        assert features.shape == (1, len(FEATURE_NAMES)), (
            f"Expected shape (1, {len(FEATURE_NAMES)}), got {features.shape}"
        )

    def test_scanner_confidence_below_critical_threshold(self):
        """
        Scanner traffic should not produce CRITICAL severity regardless
        of what the classifier outputs.
        """
        events = make_scanner_events(40)
        features = extract_features(events)
        result = predict(features)
        sev = get_severity(result["threat_type"], result["confidence"])
        assert sev in ("LOW", "MEDIUM"), (
            f"Scanner traffic should not produce HIGH/CRITICAL. Got {sev}."
        )
