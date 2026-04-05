"""
Cross-Layer Correlator — groups events by source IP within a sliding
time window and boosts confidence when signals span multiple layers.
"""
import time
import logging
from collections import defaultdict
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

# Window: group events within this many seconds per source IP
WINDOW_SECONDS = 120


class CorrelationWindow:
    """
    In-memory sliding window that accumulates events per source_ip.
    For a production system, back this with Redis hashes / sorted sets.
    """

    def __init__(self, window_seconds: int = WINDOW_SECONDS):
        self.window = window_seconds
        # { source_ip: [(timestamp_float, event_dict), ...] }
        self._store: Dict[str, List[Tuple[float, Dict[str, Any]]]] = defaultdict(list)

    def add(self, event: Dict[str, Any]):
        ip = event.get("source_ip", "unknown")
        self._store[ip].append((time.time(), event))
        self._evict(ip)

    def get_window(self, source_ip: str) -> List[Dict[str, Any]]:
        """Return all events for source_ip still within the window."""
        self._evict(source_ip)
        return [e for _, e in self._store[source_ip]]

    def _evict(self, ip: str):
        cutoff = time.time() - self.window
        self._store[ip] = [(ts, e) for ts, e in self._store[ip] if ts >= cutoff]

    def boost_confidence(self, events: List[Dict[str, Any]], base_confidence: float) -> float:
        """
        Apply a confidence multiplier based on how many distinct layers
        contributed signals. More layers → higher confidence.
        """
        layers = {e.get("layer") for e in events if e.get("layer")}
        boost = 1.0 + (len(layers) - 1) * 0.10   # +10% per additional layer
        boosted = min(base_confidence * boost, 0.99)
        if boost > 1.0:
            logger.debug(
                f"Correlation boost ×{boost:.2f} ({layers}) "
                f"{base_confidence:.2f} → {boosted:.2f}"
            )
        return boosted

    def layers_involved(self, events: List[Dict[str, Any]]) -> List[str]:
        return list({e.get("layer") for e in events if e.get("layer")})


# Singleton used by the detection pipeline
_window = CorrelationWindow()


def get_window() -> CorrelationWindow:
    return _window
