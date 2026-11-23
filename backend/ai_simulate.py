"""Deterministic prompt -> executable simulation spec for POST /api/ai/simulate.

Guarantees a simple request ("a simple house") always yields a runnable spec,
independent of any LLM. A model's JSON (Laya / Qwen) can be fed through
`validate_spec` to get the same coercion and CFL guard.
"""

import re
from typing import Any

# First keyword hit wins, so specific words precede generic ones.
# (keywords, archetype, custom shape or None, default size)
RULES: list[tuple[tuple[str, ...], str, str | None, float]] = [
    (("house", "home", "cottage", "cabin"), "cad", "house", 0.15),
    (("tower", "skyscraper", "building"), "cad", "tower", 0.12),
    (("box", "block", "cube", "square"), "cad", "square", 0.12),
    (("f1", "formula 1", "formula one", "downforce"), "f1", None, 0.0),
    (("submarine", "hull"), "submarine", None, 0.0),
    (("drone", "rotor", "quadcopter"), "drone", None, 0.0),
    (("airfoil", "naca", "wing"), "airfoil", None, 0.0),
    (("cylinder", "von karman", "karman"), "cylinder", None, 0.0),
    (("venturi", "pipe", "nozzle", "converging"), "venturi", None, 0.0),
    (("cavity", "lid"), "cavity", None, 0.0),
]
SUBSTANCES = {"seawater": "water", "water": "water", "oil": "oil", "ethanol": "ethanol", "air": "air", "wind": "air"}


def validate_spec(raw: dict[str, Any]) -> dict[str, Any]:
    """Coerce types ("41x41" -> 41), clamp ranges, and cap dt for explicit-scheme stability."""
    mesh = raw.get("mesh") or {}
    fluid = raw.get("fluid") or {}
    num = raw.get("numerics") or {}

    def num_of(v: Any, default: float) -> float:
        m = re.search(r"-?\d+(\.\d+)?", str(v))
        return float(m.group(0)) if m else default

    n = int(min(max(num_of(mesh.get("nx", raw.get("gridResolution", 41)), 41), 16), 128))
    re_num = min(max(num_of(fluid.get("reynolds", raw.get("reynoldsNumber", 100)), 100), 1.0), 5000.0)
    dx, nu = 1.0 / (n - 1), 1.0 / re_num
    dt_max = min(0.65 * dx, 0.25 * dx * dx / nu)  # Co < 0.65 (U_ref = 1), diffusion <= 0.25
    dt = min(max(num_of(num.get("dt", raw.get("dt", 0.005)), 0.005), 1e-5), dt_max)
    return {
        **raw,
        "mesh": {"nx": n, "ny": n},
        "fluid": {**fluid, "substance": fluid.get("substance", "air"), "reynolds": re_num},
        "numerics": {**num, "dt": dt, "autoCfl": True},
    }


def build_spec(prompt: str) -> dict[str, Any]:
    text = prompt.lower()
    for keywords, archetype, shape, size in RULES:
        kw = next((k for k in keywords if k in text), None)
        if kw is None:
            continue
        substance = next((v for k, v in SUBSTANCES.items() if k in text), "air")
        re_m = re.search(r"\bre(?:ynolds)?\s*(?:number)?\s*[=:]?\s*(\d+)", text)
        spec = validate_spec({
            "mode": "2d",
            "archetype": archetype,
            "geometry": {"type": shape or archetype},
            "fluid": {"substance": substance, "reynolds": int(re_m.group(1)) if re_m else 100},
        })
        if shape:
            spec["obstacleSpec"] = {"shape": shape, "cx": 0.4, "cy": 0.5, "size": size, "aoa": 0}
        return {"ok": True, "message": f"Built a {shape or archetype} simulation ({substance}, Re={spec['fluid']['reynolds']:g}).", "simulation_spec": spec}
    return {
        "ok": False,
        "message": "No supported shape found. Try: house, tower, box, cylinder, airfoil, F1 wing, venturi pipe, cavity, drone, submarine.",
    }
