"""
Threat Classifier — Scikit-learn RandomForest trained on synthetic data.
Detects: brute_force, lateral_movement, data_exfiltration, command_and_control,
         false_positive, benign.

Run this file directly to train and save the model:
    python -m models.threat_classifier
"""
import logging
import os
import joblib
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

from models.feature_extractor import FEATURE_NAMES

logger = logging.getLogger(__name__)

LABELS = [
    "brute_force",
    "lateral_movement",
    "data_exfiltration",
    "command_and_control",
    "false_positive",
    "benign",
]

MODEL_DIR = Path(os.getenv("MODEL_PATH", "models/saved/threat_classifier.pkl")).parent
MODEL_PATH = MODEL_DIR / "threat_classifier.pkl"


# ---------------------------------------------------------------------------
# Synthetic training data generation
# ---------------------------------------------------------------------------

def _rng(seed=42):
    return np.random.default_rng(seed)


def _generate_synthetic_data(n_per_class: int = 500):
    """
    Generate labelled synthetic feature vectors for each threat class.
    Each row corresponds to FEATURE_NAMES order.
    """
    rng = _rng()
    X, y = [], []

    def add(samples, label):
        X.extend(samples)
        y.extend([label] * len(samples))

    n = n_per_class

    # --- brute_force ---
    # High failed_login_count, many same source IPs, low bytes
    bf = np.column_stack([
        rng.integers(40, 200, n),      # failed_login_count  ↑
        rng.integers(1, 3, n),         # unique_source_ips   (same attacker)
        rng.integers(1, 5, n),         # unique_dest_ips
        rng.integers(500, 5000, n),    # total_bytes         ↓
        rng.integers(10, 50, n),       # avg_bytes
        rng.integers(50, 250, n),      # event_count
        rng.integers(0, 2, n),         # internal_lateral_conns
        rng.integers(0, 5, n),         # dns_query_count
        rng.integers(0, 500, n),       # outbound_bytes
        rng.integers(1, 3, n),         # cross_layer_count
        rng.uniform(0.7, 1.0, n),      # failure_ratio       ↑
        rng.integers(50, 250, n),      # short_interval_bursts ↑
    ])
    add(bf.tolist(), "brute_force")

    # --- lateral_movement ---
    # High unique_dest_ips internally, moderate events, moderate bytes
    lm = np.column_stack([
        rng.integers(0, 5, n),         # failed_login_count  ↓
        rng.integers(1, 4, n),         # unique_source_ips
        rng.integers(10, 50, n),       # unique_dest_ips     ↑
        rng.integers(5000, 50000, n),  # total_bytes
        rng.integers(100, 1000, n),    # avg_bytes
        rng.integers(20, 100, n),      # event_count
        rng.integers(8, 40, n),        # internal_lateral_conns ↑
        rng.integers(5, 30, n),        # dns_query_count
        rng.integers(0, 1000, n),      # outbound_bytes      ↓
        rng.integers(2, 3, n),         # cross_layer_count
        rng.uniform(0.0, 0.2, n),      # failure_ratio
        rng.integers(20, 100, n),      # short_interval_bursts
    ])
    add(lm.tolist(), "lateral_movement")

    # --- data_exfiltration ---
    # Very high outbound_bytes, high total_bytes, few sources
    de = np.column_stack([
        rng.integers(0, 3, n),               # failed_login_count
        rng.integers(1, 3, n),               # unique_source_ips
        rng.integers(1, 5, n),               # unique_dest_ips
        rng.integers(500_000, 5_000_000, n), # total_bytes     ↑↑
        rng.integers(10_000, 100_000, n),    # avg_bytes       ↑↑
        rng.integers(5, 50, n),              # event_count
        rng.integers(0, 2, n),               # internal_lateral_conns
        rng.integers(0, 10, n),              # dns_query_count
        rng.integers(400_000, 4_000_000, n), # outbound_bytes  ↑↑
        rng.integers(1, 3, n),               # cross_layer_count
        rng.uniform(0.0, 0.1, n),            # failure_ratio
        rng.integers(5, 50, n),              # short_interval_bursts
    ])
    add(de.tolist(), "data_exfiltration")

    # --- command_and_control (C2) ---
    # Regular beaconing: moderate event_count, high dns_count, regular intervals
    c2 = np.column_stack([
        rng.integers(0, 2, n),          # failed_login_count
        rng.integers(1, 2, n),          # unique_source_ips
        rng.integers(1, 3, n),          # unique_dest_ips
        rng.integers(1000, 20000, n),   # total_bytes
        rng.integers(50, 500, n),       # avg_bytes
        rng.integers(30, 200, n),       # event_count        ↑ (beaconing)
        rng.integers(0, 3, n),          # internal_lateral_conns
        rng.integers(20, 100, n),       # dns_query_count    ↑↑
        rng.integers(500, 10000, n),    # outbound_bytes
        rng.integers(1, 2, n),          # cross_layer_count
        rng.uniform(0.0, 0.1, n),       # failure_ratio
        rng.integers(30, 200, n),       # short_interval_bursts ↑
    ])
    add(c2.tolist(), "command_and_control")

    # --- false_positive ---
    # Looks like brute force but actually a monitoring tool / batch job
    fp = np.column_stack([
        rng.integers(20, 60, n),        # failed_login_count (moderate, not extreme)
        rng.integers(1, 2, n),          # unique_source_ips  (known scanner)
        rng.integers(50, 200, n),       # unique_dest_ips    ↑ (scanner sweeps)
        rng.integers(1000, 10000, n),   # total_bytes
        rng.integers(20, 100, n),       # avg_bytes
        rng.integers(30, 100, n),       # event_count
        rng.integers(0, 200, n),        # internal_lateral_conns (scanners sweep internally)
        rng.integers(0, 5, n),          # dns_query_count
        rng.integers(0, 200, n),        # outbound_bytes
        rng.integers(1, 2, n),          # cross_layer_count
        rng.uniform(0.3, 0.6, n),       # failure_ratio (moderate — not overwhelmingly failed)
        rng.integers(30, 100, n),       # short_interval_bursts
    ])
    add(fp.tolist(), "false_positive")

    # --- benign ---
    # Normal traffic: low everything
    bn = np.column_stack([
        rng.integers(0, 3, n),          # failed_login_count
        rng.integers(1, 10, n),         # unique_source_ips
        rng.integers(1, 15, n),         # unique_dest_ips
        rng.integers(100, 50000, n),    # total_bytes
        rng.integers(10, 5000, n),      # avg_bytes
        rng.integers(1, 30, n),         # event_count
        rng.integers(0, 3, n),          # internal_lateral_conns
        rng.integers(0, 10, n),         # dns_query_count
        rng.integers(0, 5000, n),       # outbound_bytes
        rng.integers(1, 3, n),          # cross_layer_count
        rng.uniform(0.0, 0.1, n),       # failure_ratio
        rng.integers(1, 30, n),         # short_interval_bursts
    ])
    add(bn.tolist(), "benign")

    return np.array(X, dtype=np.float64), np.array(y)


# ---------------------------------------------------------------------------
# Train & persist
# ---------------------------------------------------------------------------

def train_and_save():
    logger.info("Generating synthetic training data...")
    X, y = _generate_synthetic_data(n_per_class=600)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", RandomForestClassifier(
            n_estimators=200,
            max_depth=12,
            min_samples_leaf=2,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
        )),
    ])

    logger.info("Training RandomForest classifier...")
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    logger.info("\n" + classification_report(y_test, y_pred, target_names=LABELS))

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)
    logger.info(f"Model saved to {MODEL_PATH}")
    return pipeline


# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------

_pipeline = None


def load_model() -> Pipeline:
    global _pipeline
    if _pipeline is None:
        if MODEL_PATH.exists():
            _pipeline = joblib.load(MODEL_PATH)
            logger.info(f"Loaded model from {MODEL_PATH}")
        else:
            logger.warning("No saved model found — training from scratch...")
            _pipeline = train_and_save()
    return _pipeline


def predict(features: np.ndarray) -> dict:
    """
    Run inference on a feature vector.
    Returns: { threat_type, confidence, all_probabilities }
    """
    model = load_model()
    proba = model.predict_proba(features)[0]
    classes = model.classes_
    idx = int(np.argmax(proba))
    return {
        "threat_type": classes[idx],
        "confidence": float(proba[idx]),
        "probabilities": {c: float(p) for c, p in zip(classes, proba)},
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    train_and_save()
