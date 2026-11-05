"""
OpenZess Hybrid Bridge — Python + Rust Native Acceleration
Connects the Python FastAPI core to the Rust bare-metal CFD compute engine.

Features:
- Auto-detection: checks if the Rust sidecar is online (default: http://127.0.0.1:8081)
- Zero-downtime fallback: if Rust is offline, automatically falls back to Python SciPy
- Seamless telemetry conversion between Rust and Python dictionaries
"""

import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

RUST_SIDECAR_URL = "http://127.0.0.1:8081"


def is_rust_engine_online(timeout: float = 0.25) -> bool:
    """Check if the high-performance Rust compute sidecar is reachable."""
    try:
        req = urllib.request.Request(f"{RUST_SIDECAR_URL}/health", headers={"User-Agent": "OpenZess-Python-Bridge"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def solve_with_rust(
    nx: int = 41,
    ny: int = 41,
    lx: float = 1.0,
    ly: float = 1.0,
    nu: float = 0.01,
    dt: float = 0.005,
    steps: int = 25,
    lid_u: float = 1.0,
    archetype: str = "cavity",
    obstacle_mask: Optional[list] = None,
    timeout: float = 30.0,
) -> Optional[Dict[str, Any]]:
    """
    Offload Navier-Stokes time steps to the Rust engine.

    The geometry (domain size, cell-centred grid, solid mask) and viscosity
    come from the Python side so both engines solve the same problem; Rust
    returns u, v, p (+ speed, vorticity, residual, CFL). Forces are then
    integrated in Python with the same routine as the SciPy solver.
    """
    payload = json.dumps({
        "nx": nx,
        "ny": ny,
        "lx": lx,
        "ly": ly,
        "nu": nu,
        "dt": dt,
        "steps": steps,
        "lid_u": lid_u,
        "archetype": archetype,
        "obstacle_mask": obstacle_mask,
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            f"{RUST_SIDECAR_URL}/cfd/solve",
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "OpenZess-Python-Bridge"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                return data
    except Exception as e:
        # Fallback to Python if Rust service cannot be reached
        print(f"[Hybrid Bridge] Rust engine call bypassed: {e}")
        return None


def benchmark_with_rust(
    nx: int = 41,
    ny: int = 41,
    steps: int = 200,
    timeout: float = 10.0,
) -> Optional[Dict[str, Any]]:
    """Run a high-speed raw throughput benchmark in Rust."""
    payload = json.dumps({
        "nx": nx,
        "ny": ny,
        "nu": 0.01,
        "dt": 0.005,
        "steps": steps,
        "lid_u": 1.0,
        "archetype": "cavity",
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            f"{RUST_SIDECAR_URL}/cfd/benchmark",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None
