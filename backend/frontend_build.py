"""
Keep frontend/dist in sync with frontend/src.

Called explicitly by the launchers (main.py, sync_and_launch.py) — never at
import time, so importing backend.app (tests, uvicorn workers, reloads)
does not spawn npm.
"""

import os
import shutil
import subprocess

FRONTEND_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend"
)
DIST_INDEX = os.path.join(FRONTEND_DIR, "dist", "index.html")

# Inputs that change the built bundle
_SOURCES = ("src", "public", "index.html", "vite.config.ts", "package.json",
            "package-lock.json", "tsconfig.json", "tsconfig.app.json")


def _newest_mtime(path: str) -> float:
    if os.path.isfile(path):
        return os.path.getmtime(path)
    newest = 0.0
    for root, _, files in os.walk(path):
        for name in files:
            try:
                newest = max(newest, os.path.getmtime(os.path.join(root, name)))
            except OSError:
                continue
    return newest


def build_is_stale() -> bool:
    """True when dist/ is missing or older than any frontend source."""
    if not os.path.exists(DIST_INDEX):
        return True
    built = os.path.getmtime(DIST_INDEX)
    return any(
        _newest_mtime(os.path.join(FRONTEND_DIR, name)) > built
        for name in _SOURCES
        if os.path.exists(os.path.join(FRONTEND_DIR, name))
    )


def _run(cmd: list, timeout: int) -> bool:
    # A resolved executable path (npm.cmd on Windows) runs without shell=True.
    # shell=True with an argument list runs only cmd[0] on POSIX, which is
    # how the old launcher ended up executing a bare `npm`.
    try:
        res = subprocess.run(cmd, cwd=FRONTEND_DIR, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(f"[OpenZess] {' '.join(cmd[1:])} failed: {exc}")
        return False
    if res.returncode != 0:
        print(f"[OpenZess] `npm {' '.join(cmd[1:])}` failed:\n{(res.stderr or res.stdout)[-2000:]}")
        return False
    return True


def ensure_frontend_build(install_deps: bool = True) -> bool:
    """Rebuild the Vue bundle if it is missing or stale.

    Returns True when an up-to-date build exists afterwards.
    """
    if not os.path.exists(os.path.join(FRONTEND_DIR, "package.json")):
        return os.path.exists(DIST_INDEX)
    if not build_is_stale():
        print("[OpenZess] Frontend build is up to date.")
        return True

    npm = shutil.which("npm")
    if not npm:
        print("[OpenZess] frontend/dist is missing or stale and npm was not found.\n"
              "           Install Node.js 18+ and run `npm ci && npm run build` in frontend/.")
        return os.path.exists(DIST_INDEX)

    if install_deps and not os.path.isdir(os.path.join(FRONTEND_DIR, "node_modules")):
        print("[OpenZess] Installing frontend dependencies (npm ci)...")
        if not _run([npm, "ci"], timeout=900):
            return os.path.exists(DIST_INDEX)

    print("[OpenZess] Building the frontend (npm run build)...")
    ok = _run([npm, "run", "build"], timeout=900)
    if ok:
        print("[OpenZess] Frontend build complete.")
    return ok and os.path.exists(DIST_INDEX)
