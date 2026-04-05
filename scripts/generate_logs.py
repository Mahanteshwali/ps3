"""
Synthetic log generator — simulates multi-layer log traffic at configurable
rates for local testing and load validation (target: 500+ events/sec).

Usage:
    python scripts/generate_logs.py --rate 500 --duration 30
    python scripts/generate_logs.py --attack brute_force --rate 200
"""
import argparse
import asyncio
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import httpx

BASE_URL = "http://localhost:8000"

LAYERS = ["network", "endpoint", "application"]


def _ts():
    return datetime.now(timezone.utc).isoformat()


def _random_ip(internal=True):
    if internal:
        return f"10.0.{random.randint(1,10)}.{random.randint(2,254)}"
    return f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"


def make_benign_event(layer: str) -> dict:
    return {
        "timestamp": _ts(),
        "source_ip": _random_ip(),
        "dest_ip": _random_ip(),
        "event_type": random.choice(["http_request", "dns_query", "file_read", "login"]),
        "username": random.choice(["alice", "bob", "charlie", None]),
        "status": "success",
        "bytes": random.randint(100, 50_000),
    }


def make_attack_event(attack: str, src_ip: str, layer: str) -> dict:
    base = {"timestamp": _ts(), "source_ip": src_ip}
    if attack == "brute_force":
        return {**base, "dest_ip": _random_ip(), "event_type": "failed_login",
                "username": "admin", "status": "failure", "bytes": 120}
    if attack == "lateral_movement":
        return {**base, "dest_ip": _random_ip(), "event_type": "smb_connect",
                "status": "success", "bytes": random.randint(500, 5000)}
    if attack == "data_exfiltration":
        return {**base, "dest_ip": _random_ip(internal=False), "event_type": "large_upload",
                "status": "success", "bytes": random.randint(500_000, 2_000_000)}
    if attack == "command_and_control":
        return {**base, "dest_ip": _random_ip(internal=False),
                "event_type": random.choice(["dns_query", "http_beacon"]),
                "status": "success", "bytes": random.randint(200, 2000)}
    return make_benign_event(layer)


async def send_event(client: httpx.AsyncClient, layer: str, payload: dict):
    try:
        await client.post(f"{BASE_URL}/ingest/{layer}", json=payload, timeout=5.0)
    except Exception:
        pass  # fire-and-forget for load testing


async def run(rate: int, duration: int, attack: str | None):
    interval = 1.0 / rate
    end_time = time.time() + duration
    attack_src = _random_ip() if attack else None
    sent = 0

    async with httpx.AsyncClient() as client:
        while time.time() < end_time:
            layer = random.choice(LAYERS)
            if attack and random.random() < 0.6:
                payload = make_attack_event(attack, attack_src, layer)
            else:
                payload = make_benign_event(layer)

            asyncio.create_task(send_event(client, layer, payload))
            sent += 1

            if sent % (rate * 5) == 0:
                elapsed = time.time() - (end_time - duration)
                actual_rate = sent / max(elapsed, 0.001)
                print(f"[{elapsed:.1f}s] Sent {sent} events | ~{actual_rate:.0f} eps")

            await asyncio.sleep(interval)

    print(f"\n✅ Done — {sent} events sent in {duration}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Synthetic log generator")
    parser.add_argument("--rate", type=int, default=100, help="Events per second")
    parser.add_argument("--duration", type=int, default=60, help="Duration in seconds")
    parser.add_argument(
        "--attack",
        choices=["brute_force", "lateral_movement", "data_exfiltration", "command_and_control"],
        default=None,
        help="Mix in a specific attack type (60%% of traffic)",
    )
    args = parser.parse_args()
    print(f"🚀 Generating {args.rate} eps for {args.duration}s"
          + (f" with {args.attack} attack" if args.attack else "") + "...")
    asyncio.run(run(args.rate, args.duration, args.attack))
