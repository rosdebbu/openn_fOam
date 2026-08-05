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

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def open_browser():
    """Wait for server to start, then open browser."""
    time.sleep(1.5)
    url = "http://localhost:8000/studio/index.html"
    print(f"\n🚀 Launching OpenZess Web Studio at: {url}\n")
    webbrowser.open(url)


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass
    print("=" * 60)
    print("   ⚡ OpenZess Studio — Indigenous AI-Native CFD Platform")
    print("=" * 60)
    print("   • Backend Engine: SciPy Sparse Accelerated CFD Solver")
    print("   • AI Layer: Instant PINN Surrogate Physics")
    print("   • Frontend: 60 FPS HTML5 Canvas Web Studio UI")
    print("=" * 60)
    
    # Launch browser thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run uvicorn server
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, log_level="info")


if __name__ == "__main__":
    main()
