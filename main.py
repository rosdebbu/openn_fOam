"""
OpenZess Studio Launcher
Starts the backend FastAPI server and opens the Web Studio UI in your default web browser.
"""

import uvicorn
import webbrowser
import time
import threading
import sys
import os
import subprocess

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Expose app for ASGI servers (e.g., uvicorn main:app)
from backend.app import app
from backend.rust_bridge import is_rust_engine_online


def open_browser():
    """Wait for server to start, then open browser."""
    time.sleep(1.5)
    url = "http://localhost:8000/studio/index.html"
    print(f"\n🚀 Launching OpenZess Web Studio at: {url}\n")
    webbrowser.open(url)


def launch_rust_sidecar_if_available():
    """Check for compiled Rust sidecar binary or launch background daemon."""
    sidecar_bin = os.path.join(os.path.dirname(__file__), "rust-sidecar", "target", "release", "openzess-rust-sidecar.exe")
    if not os.path.exists(sidecar_bin):
        sidecar_bin = os.path.join(os.path.dirname(__file__), "rust-sidecar", "target", "debug", "openzess-rust-sidecar.exe")

    if os.path.exists(sidecar_bin):
        print(f"   🦀 Starting Rust Sidecar from: {sidecar_bin}")
        try:
            proc = subprocess.Popen([sidecar_bin], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return proc
        except Exception as e:
            print(f"   ⚠️ Could not launch Rust sidecar: {e}")
    return None


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    rust_proc = launch_rust_sidecar_if_available()
    time.sleep(0.3)
    rust_online = is_rust_engine_online(timeout=0.3)

    print("=" * 64)
    print("   ⚡ OpenZess Hybrid Studio — Multi-Engine CFD Platform")
    print("=" * 64)
    print("   • Python Gateway: FastAPI ASGI WebSockets (Port 8000)")
    print(f"   • Rust Engine:    Rayon Bare-Metal Sidecar ({'Online ⚡' if rust_online else 'Standby / Auto-fallback 🛡️'})")
    print("   • AI Surrogate:   PINN Physics Surrogate (<50ms Inference)")
    print("   • Visualization:  Three.js 3D WebGL + 60-120 FPS RK4 Streamlines")
    print("=" * 64)

    # Launch browser thread
    threading.Thread(target=open_browser, daemon=True).start()

    # Run uvicorn server
    try:
        uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, log_level="info")
    finally:
        if rust_proc:
            print("\nShutting down Rust sidecar...")
            rust_proc.terminate()


if __name__ == "__main__":
    main()

