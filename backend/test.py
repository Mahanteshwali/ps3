import httpx, asyncio; print(asyncio.run(httpx.AsyncClient().post('http://localhost:8000/simulate/attack', json={'attack_type': 'brute_force'})))
