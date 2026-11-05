"""
OpenZess Studio launcher.

Rebuilds the frontend if it is stale, starts the Rust sidecar if one has
been compiled, runs the FastAPI server and opens the studio in a browser.

    python main.py [--port 8000] [--no-browser] [--reload] [--skip-build]
"""

import argparse
import os
import subprocess
import sys
import threading
import time
import webbrowser

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)


def __getattr__(name):
    """Lazily expose `app` so `uvicorn main:app` works without importing
    (and freezing the frontend build path of) backend.app at import time."""
    if name == "app":
        from backend.app import app
        return app
    raise AttributeError(name)


def open_browser(url: str) -> None:
    time.sleep(1.5)  # give uvicorn a moment to bind
    print(f"\n🚀 Opening OpenZess Studio at: {url}\n")
    webbrowser.open(url)


def launch_rust_sidecar_if_available():
    """Launch the compiled Rust sidecar (`cargo build --release`) if present."""
    exe = "openzess-rust-sidecar" + (".exe" if os.name == "nt" else "")
    target = os.path.join(ROOT, "rust-sidecar", "target")
    candidates = [os.path.join(target, profile, exe) for profile in ("release", "debug")]
    sidecar_bin = next((c for c in candidates if os.path.exists(c)), None)

    if sidecar_bin:
        print(f"   🦀 Starting Rust sidecar from: {sidecar_bin}")
        try:
            return subprocess.Popen([sidecar_bin], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError as e:
            print(f"   ⚠️ Could not launch Rust sidecar: {e}")
    return None


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="Launch OpenZess Studio")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-browser", action="store_true", help="do not open a browser tab")
    parser.add_argument("--reload", action="store_true", help="auto-reload on backend code changes (development)")
    parser.add_argument("--skip-build", action="store_true", help="do not rebuild a stale frontend")
    args = parser.parse_args()

    if not args.skip_build:
        from backend.frontend_build import ensure_frontend_build
        ensure_frontend_build()

    import uvicorn
    from backend.rust_bridge import is_rust_engine_online

    rust_proc = launch_rust_sidecar_if_available()
    time.sleep(0.3)
    rust_online = is_rust_engine_online(timeout=0.3)

    from backend.app import app, static_dir  # after the build, so it is served

    url = f"http://localhost:{args.port}/studio/index.html"
    print("=" * 64)
    print("   ⚡ OpenZess Studio — 2-D CFD platform")
    print("=" * 64)
    print(f"   • Python server:   FastAPI + WebSockets (port {args.port})")
    print(f"   • Rust kernel:     {'online (Rayon)' if rust_online else 'not running — Python solver is used'}")
    print("   • Instant preview: potential flow / Stokes solve (no ML model)")
    print(f"   • Frontend build:  {static_dir or 'MISSING — run npm ci && npm run build in frontend/'}")
    print(f"   • Studio URL:      {url}")
    print("=" * 64)

    if not args.no_browser:
        threading.Thread(target=open_browser, args=(url,), daemon=True).start()

    try:
        if args.reload:
            # Reload needs an import string; the worker re-imports the app
            uvicorn.run("backend.app:app", host="127.0.0.1", port=args.port, reload=True)
        else:
            uvicorn.run(app, host="127.0.0.1", port=args.port)
    finally:
        if rust_proc:
            print("\nShutting down Rust sidecar...")
            rust_proc.terminate()


if __name__ == "__main__":
    main()
