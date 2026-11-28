"""Measure two backend claims from docs/PROJECT_ANALYSIS.md (findings B4 and B6).

1. B4: a running simulation blocks the event loop, so /api/health slows down.
2. B6: bad inputs (Re <= 0, Re = 1e12, a non-numeric grid) are accepted without a clear error.

Start your OWN backend first. Do not reuse a server you did not start:
    python -m uvicorn backend.app:app --host 127.0.0.1 --port 8010
Then, from the repo root:
    python scripts/verify_backend_limits.py
Needs: httpx, websockets (both installed with the project requirements).
"""
import asyncio, json, time, httpx, websockets

BASE, WS = "http://127.0.0.1:8010", "ws://127.0.0.1:8010/ws/simulate"

async def sim(params):
    t = time.time(); frames = 0; err = None
    async with websockets.connect(WS) as ws:
        await ws.send(json.dumps(params))
        try:
            async for m in ws:
                d = json.loads(m); frames += 1
                if "error" in d: err = d["error"][:90]
        except Exception as e:
            err = f"closed: {e}"
    return time.time() - t, frames, err

async def pinger(stop, out):
    async with httpx.AsyncClient() as c:
        while not stop.is_set():
            t = time.time()
            try:
                await c.get(BASE + "/api/health", timeout=30)
                out.append(time.time() - t)
            except Exception as e:
                out.append(999)
            await asyncio.sleep(0.1)

async def main():
    # baseline health latency
    async with httpx.AsyncClient() as c:
        t = time.time(); await c.get(BASE + "/api/health"); print(f"idle /api/health: {1000*(time.time()-t):.0f} ms")
    stop, lat = asyncio.Event(), []
    p = asyncio.create_task(pinger(stop, lat))
    dur, frames, err = await sim({"archetype": "cylinder", "gridResolution": 96, "maxIterations": 200, "reynoldsNumber": 100, "dt": 0.005})
    stop.set(); await p
    print(f"sim 96x96 cylinder 200 it: {dur:.1f}s, {frames} frames, err={err}")
    print(f"/api/health WHILE simulating: n={len(lat)} median={1000*sorted(lat)[len(lat)//2]:.0f} ms  max={1000*max(lat):.0f} ms")
    for label, prm in [("Re=0", {"archetype": "cavity", "reynoldsNumber": 0, "maxIterations": 5}),
                       ("Re=-5", {"archetype": "cavity", "reynoldsNumber": -5, "maxIterations": 5}),
                       ("Re=1e12", {"archetype": "cavity", "reynoldsNumber": 1e12, "maxIterations": 5}),
                       ("gridResolution='abc'", {"archetype": "cavity", "gridResolution": "abc"})]:
        d, f, e = await sim(prm)
        print(f"{label:22} -> frames={f} err={e}")
asyncio.run(main())
