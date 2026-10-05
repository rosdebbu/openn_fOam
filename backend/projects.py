"""
OpenZess Project Persistence — Named Simulation Snapshots
Stores complete project state (physics, geometry, custom CAD spec, dict
overrides) as JSON files so a saved project survives page reloads, browser
restarts, and server restarts. This is what makes "Save" actually permanent.
"""

import json
import os
import re
import time

SNAPSHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_projects")

_SAFE_NAME_RE = re.compile(r"[^a-zA-Z0-9_\-]")


def _safe_name(name: str) -> str:
    cleaned = _SAFE_NAME_RE.sub("_", str(name or "").strip())[:64]
    return cleaned or "openzess_project"


def _ensure_dir() -> None:
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)


def save_project(name: str, data: dict) -> dict:
    """Persist a named project snapshot as JSON. Returns stored metadata."""
    _ensure_dir()
    safe = _safe_name(name)
    payload = {
        "name": safe,
        "displayName": str(name or safe),
        "savedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
        "savedAtEpoch": time.time(),
        "state": data or {},
    }
    path = os.path.join(SNAPSHOT_DIR, f"{safe}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    return {
        "name": safe,
        "displayName": payload["displayName"],
        "savedAt": payload["savedAt"],
    }


def list_projects() -> list:
    """List all saved project snapshots, newest first."""
    _ensure_dir()
    entries = []
    for fname in os.listdir(SNAPSHOT_DIR):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(SNAPSHOT_DIR, fname)
        try:
            with open(path, "r", encoding="utf-8") as fh:
                payload = json.load(fh)
            entries.append({
                "name": payload.get("name", fname[:-5]),
                "displayName": payload.get("displayName", fname[:-5]),
                "savedAt": payload.get("savedAt", ""),
                "savedAtEpoch": payload.get("savedAtEpoch", 0),
                "archetype": (payload.get("state") or {}).get("archetype", ""),
            })
        except Exception:
            continue
    entries.sort(key=lambda e: e.get("savedAtEpoch", 0), reverse=True)
    return entries


def load_project(name: str) -> dict | None:
    """Load a saved project snapshot's full state, or None if missing."""
    safe = _safe_name(name)
    path = os.path.join(SNAPSHOT_DIR, f"{safe}.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh).get("state")
    except Exception:
        return None


def delete_project(name: str) -> bool:
    safe = _safe_name(name)
    path = os.path.join(SNAPSHOT_DIR, f"{safe}.json")
    if os.path.exists(path):
        try:
            os.remove(path)
            return True
        except Exception:
            return False
    return False