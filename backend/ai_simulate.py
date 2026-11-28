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
    (("spaceship", "rocket", "starship", "shuttle"), "spaceship", None, 0.0),
    (("drone", "rotor", "quadcopter"), "drone", None, 0.0),
    (("airfoil", "naca", "wing"), "airfoil", None, 0.0),
    (("cylinder", "von karman", "karman"), "cylinder", None, 0.0),
    (("venturi", "pipe", "nozzle", "converging"), "venturi", None, 0.0),
    (("cavity", "lid"), "cavity", None, 0.0),
]
SUBSTANCES = {"seawater": "water", "water": "water", "oil": "oil", "ethanol": "ethanol", "air": "air", "wind": "air"}


def explicit_reynolds(prompt: str) -> int | None:
    """Re typed by the user ("Re=900", "reynolds number 900"). It always beats a model's guess."""
    m = re.search(r"\bre(?:ynolds)?\s*(?:number)?\s*[=:]?\s*(\d+)", prompt.lower())
    return int(m.group(1)) if m else None


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
        spec = validate_spec({
            "mode": "2d",
            "archetype": archetype,
            "geometry": {"type": shape or archetype},
            "fluid": {"substance": substance, "reynolds": explicit_reynolds(prompt) or 100},
        })
        if shape:
            spec["obstacleSpec"] = {"shape": shape, "cx": 0.4, "cy": 0.5, "size": size, "aoa": 0}
        return {"ok": True, "message": f"Built a {shape or archetype} simulation ({substance}, Re={spec['fluid']['reynolds']:g}).", "simulation_spec": spec}
    return {
        "ok": False,
        "message": "No supported shape found. Try: house, tower, box, cylinder, airfoil, F1 wing, venturi pipe, cavity, drone, submarine, spaceship.",
    }


PRESET_IDS: dict[str, int] = {
    "cavity": 0,
    "cylinder": 1,
    "venturi": 2,
    "tower": 3,
    "building_fsi": 3,
    "house": 4,
    "simple_house": 4,
    "airfoil": 5,
    "f1": 5,
    "submarine": 6,
    "spaceship": 7,
    "drone": 1,
    "box": 1,
    "obstacle": 1,
    "cad": 4,
}


def normalize_rl_spec(rl_json: dict[str, Any], prompt: str = "") -> dict[str, Any]:
    """Convert Qwen3-0.6B-RL JSON output into a CFL-validated OpenZess simulation_spec."""
    arch = str(rl_json.get("archetype", "cylinder")).strip().lower()
    shape: str | None = None
    size = 0.14
    if arch in ("house", "simple_house"):
        arch, shape, size = "cad", "house", 0.15
    elif arch in ("tower", "building_fsi"):
        arch, shape, size = "cad", "tower", 0.12
    elif arch in ("box", "square"):
        arch, shape, size = "cad", "square", 0.12

    # If prompt explicitly names submarine or spaceship (newer presets), preserve it
    low = prompt.lower()
    if any(k in low for k in ("spaceship", "rocket", "starship", "shuttle")):
        arch, shape = "spaceship", None
    elif any(k in low for k in ("submarine", "torpedo")):
        arch, shape = "submarine", None

    substance = str(rl_json.get("substance", "air")).strip().lower()
    substance = SUBSTANCES.get(substance, substance if substance in ("air", "water", "oil", "ethanol", "co2") else "air")

    spec = validate_spec({
        "mode": "2d",
        "archetype": arch,
        "geometry": {"type": shape or arch},
        "fluid": {
            "substance": substance,
            "reynolds": explicit_reynolds(prompt) or rl_json.get("reynoldsNumber", rl_json.get("reynolds", 100)),
        },
        "mesh": {"nx": rl_json.get("gridResolution", 41)},
        "numerics": {
            "dt": rl_json.get("dt", 0.004),
            "turbulenceModel": str(rl_json.get("turbulenceModel", "laminar")),
            "tolerance": str(rl_json.get("tolerance", "1e-06")),
        },
    })
    if shape:
        spec["obstacleSpec"] = {"shape": shape, "cx": 0.4, "cy": 0.5, "size": size, "aoa": 0}
    preset_id = PRESET_IDS.get(shape or arch, 1)
    return {"simulation_spec": spec, "preset_id": preset_id, "shape_key": shape or arch}
