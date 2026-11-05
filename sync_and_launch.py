"""
OpenZess sync & launch: install frontend dependencies if needed, rebuild the
bundle when the sources changed, then hand off to main.py.

    python sync_and_launch.py [main.py options]
"""

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from backend.frontend_build import ensure_frontend_build  # noqa: E402


def display_dashboard() -> None:
    commit_hash = "unknown"
    try:
        res = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                             capture_output=True, text=True)
        if res.returncode == 0:
            commit_hash = res.stdout.strip()
    except OSError:
        pass

    print("=" * 64)
    print("   ⚡ OpenZess Studio — Sync & Launch")
    print("=" * 64)
    print(f"   • Git commit:     {commit_hash}")
    print("   • Project code:   UR2627GEN317")
    print("   • Tracking sheet: RELEASE_LOG_SHEET.md")
    print("=" * 64)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("\n[OpenZess] Checking the frontend build...")
    ensure_frontend_build(install_deps=True)
    display_dashboard()
    sys.exit(subprocess.call(
        [sys.executable, os.path.join(ROOT, "main.py"), "--skip-build", *sys.argv[1:]],
        cwd=ROOT,
    ))
