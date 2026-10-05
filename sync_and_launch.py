"""
OpenZess Sync & Launch Controller
Ensures frontend assets are automatically compiled and up-to-date before launching the server.
Prevents stale/cached version headaches forever.
"""

import os
import sys
import time
import subprocess
import shutil

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
DIST_DIR = os.path.join(FRONTEND_DIR, "dist")
SRC_DIR = os.path.join(FRONTEND_DIR, "src")
GITWORK_DIR = r"C:\gitwork\openn_fOam"

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def get_latest_mtime(folder):
    """Find the newest modification timestamp in a folder recursively."""
    if not os.path.exists(folder):
        return 0
    max_mtime = 0
    for root, _, files in os.walk(folder):
        for f in files:
            p = os.path.join(root, f)
            try:
                mt = os.path.getmtime(p)
                if mt > max_mtime:
                    max_mtime = mt
            except Exception:
                pass
    return max_mtime

def check_and_build_frontend():
    print("\n[OpenZess] Checking Frontend Build Status...")
    src_mtime = get_latest_mtime(SRC_DIR)
    dist_mtime = get_latest_mtime(DIST_DIR)
    
    # Also check gitwork dist
    gw_dist = os.path.join(GITWORK_DIR, "frontend", "dist")
    gw_mtime = get_latest_mtime(gw_dist)
    
    needs_build = False
    if dist_mtime == 0 and gw_mtime == 0:
        needs_build = True
        print("   [!] No compiled frontend distribution found.")
    elif src_mtime > max(dist_mtime, gw_mtime):
        needs_build = True
        print("   [*] Source files (frontend/src) are newer than build artifacts.")

    if needs_build:
        print("   [+] Syncing source files & compiling Vue 3 + Three.js production bundle...")
        build_dir = os.path.join(GITWORK_DIR, "frontend") if os.path.exists(os.path.join(GITWORK_DIR, "frontend", "package.json")) else FRONTEND_DIR
        
        # Sync changed files from OneDrive src to GitWork build src
        if os.path.abspath(build_dir) != os.path.abspath(FRONTEND_DIR):
            target_src = os.path.join(build_dir, "src")
            for root, _, files in os.walk(SRC_DIR):
                rel_dir = os.path.relpath(root, SRC_DIR)
                dest_dir = os.path.join(target_src, rel_dir) if rel_dir != "." else target_src
                os.makedirs(dest_dir, exist_ok=True)
                for f in files:
                    sf_path = os.path.join(root, f)
                    df_path = os.path.join(dest_dir, f)
                    if not os.path.exists(df_path) or os.path.getmtime(sf_path) > os.path.getmtime(df_path):
                        try:
                            with open(sf_path, 'rb') as sf, open(df_path, 'wb') as df:
                                df.write(sf.read())
                        except Exception:
                            pass
                            
        try:
            res = subprocess.run(["npm", "run", "build"], cwd=build_dir, shell=True, capture_output=True, text=True)
            if res.returncode == 0:
                print("   [OK] Frontend build succeeded successfully!")
                # Ensure the local workspace dist has the latest compiled artifacts
                built_dist = os.path.join(build_dir, "dist")
                if os.path.abspath(built_dist) != os.path.abspath(DIST_DIR) and os.path.exists(built_dist):
                    shutil.copytree(built_dist, DIST_DIR, dirs_exist_ok=True)
            else:
                print(f"   [!] Build warning: {res.stderr[:200] if res.stderr else res.stdout[:200]}")
        except Exception as e:
            print(f"   [!] Could not trigger npm build: {e}")
    else:
        print("   [OK] Frontend production bundle is up-to-date!")

def display_dashboard():
    # Read active commit hash
    commit_hash = "Unknown"
    try:
        res = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT_DIR, capture_output=True, text=True)
        if res.returncode == 0:
            commit_hash = res.stdout.strip()
    except Exception:
        pass

    print("=" * 64)
    print("   ⚡ OpenZess Hybrid Studio — Auto-Sync Launcher")
    print("=" * 64)
    print(f"   • Active Git Commit:  {commit_hash}")
    print(f"   • Project Code:       UR2627GEN317")
    print(f"   • Tracking Sheet:     RELEASE_LOG_SHEET.md")
    print(f"   • Local Server URL:   http://localhost:8000/studio/index.html")
    print("=" * 64)
    print("   💡 Tip: In your browser, press Ctrl + F5 once to clear cache.\n")

if __name__ == "__main__":
    check_and_build_frontend()
    display_dashboard()
    
    # Hand off to main.py
    main_py = os.path.join(ROOT_DIR, "main.py")
    if os.path.exists(main_py):
        subprocess.run([sys.executable, main_py], cwd=ROOT_DIR)
    else:
        print(f"Error: Could not find {main_py}")
