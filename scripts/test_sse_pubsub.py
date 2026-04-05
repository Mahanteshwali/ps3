"""
Full end-to-end SSE test:
1. Subscribe to the /alerts/live SSE endpoint (like the browser does)  
2. Trigger a brute_force simulation via the API
3. Check if the alert arrives on the SSE connection without refresh
"""
import asyncio
import json
import httpx

API = "http://localhost:8000"


async def main():
    print("📡 Opening SSE connection to /alerts/live ...")

    # Open the SSE connection
    timeout = httpx.Timeout(connect=5.0, read=20.0, write=5.0, pool=5.0)
    alerts_received = []

    async with httpx.AsyncClient(timeout=timeout) as client:
        # Start SSE listener in background
        async def sse_listener():
            async with client.stream("GET", f"{API}/alerts/live") as resp:
                print(f"✅ SSE connected: HTTP {resp.status_code}")
                async for line in resp.aiter_lines():
                    if line.startswith("data:"):
                        try:
                            alert = json.loads(line[5:].strip())
                            alerts_received.append(alert)
                            print(f"🚨 LIVE ALERT: [{alert.get('severity')}] {alert.get('threat_type')} from {alert.get('source_ip')}")
                        except:
                            pass
                    if len(alerts_received) >= 1:
                        break  # got one, test passed

        sse_task = asyncio.create_task(sse_listener())

        # Give SSE a moment to connect
        await asyncio.sleep(1.5)

        # Trigger an attack
        print("🔥 Triggering brute_force simulation ...")
        try:
            res = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: __import__('requests').post(
                    f"{API}/simulate/attack",
                    json={"attack_type": "brute_force", "intensity": 30},
                    timeout=30
                )
            )
            print(f"   → Simulation: HTTP {res.status_code}")
        except Exception as e:
            print(f"   → Simulation error: {e}")

        # Wait up to 15s for SSE to receive something
        print("⏳ Waiting for live alert on SSE connection...")
        await asyncio.wait_for(sse_task, timeout=15.0)

    if alerts_received:
        print(f"\n✅ SUCCESS — SSE delivered {len(alerts_received)} alert(s) without page refresh!")
    else:
        print("\n❌ FAILED — No alerts received on SSE stream.")


asyncio.run(main())
