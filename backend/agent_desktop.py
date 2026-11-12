"""
OpenZess Agent Desktop Integration Module.

Provides native desktop computer-use and accessibility tree automation
powered by Vercel Labs' `agent-desktop` (Rust-based accessibility CLI).

Enables OpenZess to:
- Detect and inspect native desktop applications (ParaView, OpenFOAM terminals, browsers).
- Automate post-processing by launching ParaView with generated .vtk / OpenFOAM cases.
- Read desktop UI state as structured JSON via the OS accessibility tree.
- Dispatch headless or headed keyboard and mouse interactions via element refs.
"""

import json
import logging
import os
import shutil
import subprocess
from typing import Any, Dict, List, Optional

logger = logging.getLogger("openzess.agent_desktop")


def get_agent_desktop_bin() -> Optional[str]:
    """Find the agent-desktop binary on the system PATH."""
    bin_name = "agent-desktop.cmd" if os.name == "nt" else "agent-desktop"
    path = shutil.which(bin_name)
    if not path:
        path = shutil.which("agent-desktop")
    return path


def is_agent_desktop_available() -> bool:
    """Check if agent-desktop is installed and callable."""
    bin_path = get_agent_desktop_bin()
    if not bin_path:
        return False
    try:
        res = subprocess.run([bin_path, "version"], capture_output=True, text=True, timeout=5)
        return res.returncode == 0
    except Exception as exc:
        logger.debug("agent-desktop check failed: %s", exc)
        return False


def run_agent_desktop_command(args: List[str], timeout: int = 20) -> Dict[str, Any]:
    """Execute an agent-desktop CLI command and parse the JSON output."""
    bin_path = get_agent_desktop_bin()
    if not bin_path:
        return {
            "ok": False,
            "error": "agent-desktop CLI not found on system PATH. Install with: npm install -g agent-desktop"
        }

    cmd = [bin_path] + args
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout
        )
        stdout = proc.stdout.strip()
        if not stdout:
            return {"ok": proc.returncode == 0, "error": proc.stderr.strip() if proc.returncode != 0 else ""}

        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            return {
                "ok": proc.returncode == 0,
                "raw_output": stdout,
                "error": proc.stderr.strip() if proc.returncode != 0 else ""
            }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"agent-desktop command timed out after {timeout}s"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def get_desktop_status() -> Dict[str, Any]:
    """Return adapter health, platform info, and accessibility permission state."""
    return run_agent_desktop_command(["status"])


def list_desktop_windows(app: Optional[str] = None) -> Dict[str, Any]:
    """List all open desktop application windows."""
    args = ["list-windows"]
    if app:
        args.extend(["--app", app])
    return run_agent_desktop_command(args)


def list_desktop_apps() -> Dict[str, Any]:
    """List all running desktop GUI applications."""
    return run_agent_desktop_command(["list-apps"])


def take_app_snapshot(app_name: Optional[str] = None, interactive_only: bool = True, compact: bool = True) -> Dict[str, Any]:
    """Capture accessibility tree as structured JSON with unique @ref IDs."""
    args = ["snapshot"]
    if app_name:
        args.extend(["--app", app_name])
    if interactive_only:
        args.append("-i")
    if compact:
        args.append("-c")
    return run_agent_desktop_command(args)


def click_desktop_ref(ref_id: str, headed: bool = False) -> Dict[str, Any]:
    """Click an accessibility element using its unique ref ID."""
    args = ["click", ref_id]
    if headed:
        args.append("--headed")
    return run_agent_desktop_command(args)


def type_desktop_text(text: str, target_ref: str) -> Dict[str, Any]:
    """Insert text into a desktop target element."""
    # agent-desktop type <REF> [TEXT]
    args = ["type", target_ref, text]
    return run_agent_desktop_command(args)


def press_desktop_key(key: str) -> Dict[str, Any]:
    """Send a keyboard key or combo (e.g., 'return', 'escape', 'tab', 'ctrl+c')."""
    return run_agent_desktop_command(["press", key])


def capture_window_screenshot(output_path: str, app_name: Optional[str] = None) -> Dict[str, Any]:
    """Capture a PNG screenshot of a desktop window."""
    args = ["screenshot", output_path]
    if app_name:
        args.extend(["--app", app_name])
    return run_agent_desktop_command(args)


def launch_desktop_paraview(vtk_file_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Launch native desktop ParaView and optionally open a VTK simulation case.
    Searches common install locations on Windows and system PATH.
    """
    paraview_candidates = [
        shutil.which("paraview.exe") or shutil.which("paraview"),
        r"C:\Program Files\ParaView 5.12.0\bin\paraview.exe",
        r"C:\Program Files\ParaView 5.11.0\bin\paraview.exe",
        r"C:\Program Files\ParaView 5.10.0\bin\paraview.exe",
        r"C:\Program Files\ParaView\bin\paraview.exe"
    ]
    paraview_bin = next((p for p in paraview_candidates if p and os.path.exists(p)), None)

    if not paraview_bin:
        return {
            "ok": False,
            "error": "ParaView executable not found in PATH or standard Program Files locations."
        }

    cmd = [paraview_bin]
    if vtk_file_path and os.path.exists(vtk_file_path):
        cmd.append(os.path.abspath(vtk_file_path))

    try:
        subprocess.Popen(cmd)
        return {
            "ok": True,
            "message": f"ParaView launched successfully with: {vtk_file_path or 'empty workspace'}",
            "executable": paraview_bin
        }
    except Exception as exc:
        return {"ok": False, "error": f"Failed to launch ParaView: {exc}"}

