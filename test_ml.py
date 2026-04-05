import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from api.routers.simulate import SimulateRequest, _generate_events, LAYER_MAP
from ingestion.normalizer import normalize
from models.feature_extractor import extract_features
from models.threat_classifier import predict

for at in ["brute_force", "lateral_movement", "data_exfiltration", "command_and_control", "false_positive"]:
    req = SimulateRequest(attack_type=at, intensity=50)
    events = _generate_events(req)
    layers = LAYER_MAP.get(at, ["network"])
    normalized_events = []
    for i, raw in enumerate(events):
        layer = layers[i % len(layers)]
        normalized_events.append(normalize(raw, layer))
        
    features = extract_features(normalized_events)
    res = predict(features)
    print(f"Attack: {at.ljust(20)} -> ML Output: {res['threat_type'].ljust(20)} Conf: {res['confidence']:.2f}")

