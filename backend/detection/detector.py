"""
Detector — orchestrates the full detection pipeline for a single event:
  1. Add event to the correlation window
  2. Extract features from the window
  3. Run ML classifier
  4. Apply cross-layer confidence boost
  5. Map severity
  6. Generate explanation + playbook
  7. Return AlertDocument (or None if benign)
"""
import logging
from typing import Any, Dict, Optional

from models.feature_extractor import extract_features
from models.threat_classifier import predict
from detection.correlator import get_window
from detection.severity import get_severity
from detection.explainer import generate_explanation
from playbooks.engine import get_playbook, get_mitre
from db.models import AlertDocument

logger = logging.getLogger(__name__)

# Minimum confidence to emit a non-benign alert
CONFIDENCE_THRESHOLD = 0.55


def process_event(event: Dict[str, Any]) -> Optional[AlertDocument]:
    """
    Run the full detection pipeline for a normalized event.
    Returns an AlertDocument if a threat is detected, else None.
    """
    window = get_window()
    window.add(event)

    source_ip = event.get("source_ip", "unknown")
    window_events = window.get_window(source_ip)

    # Feature extraction
    features = extract_features(window_events)

    # ML inference
    result = predict(features)
    threat_type: str = result["threat_type"]
    confidence: float = result["confidence"]

    # Cross-layer confidence boost
    confidence = window.boost_confidence(window_events, confidence)

    # Skip low-confidence and benign results
    if threat_type == "benign" or confidence < CONFIDENCE_THRESHOLD:
        logger.debug(f"Benign/low-conf [{source_ip}]: {threat_type} @ {confidence:.2f}")
        return None

    # Severity
    severity = get_severity(threat_type, confidence)

    # Explainability
    explanation = generate_explanation(threat_type, window_events, confidence)

    # Playbook & MITRE
    playbook = get_playbook(threat_type)
    mitre_info = get_mitre(threat_type)

    # Layers involved
    layers = window.layers_involved(window_events)

    # Timestamps
    timestamps = [e.get("timestamp") for e in window_events if e.get("timestamp")]
    first_seen = min(timestamps) if timestamps else None
    last_seen = max(timestamps) if timestamps else None

    alert = AlertDocument(
        threat_type=threat_type,     # type: ignore[arg-type]
        severity=severity,            # type: ignore[arg-type]
        confidence=confidence,
        explanation=explanation,
        playbook=playbook,
        event_ids=[e.get("event_id", "") for e in window_events],
        source_ip=source_ip,
        layers_involved=layers,       # type: ignore[arg-type]
        first_seen=first_seen,
        last_seen=last_seen,
        mitre_tactic=mitre_info["tactic"] if mitre_info else None,
        mitre_technique=mitre_info["technique"] if mitre_info else None,
        mitre_technique_id=mitre_info["technique_id"] if mitre_info else None,
    )

    logger.info(
        f"🚨 ALERT [{severity}] {threat_type} from {source_ip} "
        f"(conf={confidence:.2f}, layers={layers})"
    )
    return alert
