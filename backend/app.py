"""
OpenZess FastAPI Server
Exposes REST APIs & WebSockets for live CFD simulation streaming and VTK exports.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
import asyncio
import numpy as np
import os
import json
import re

def sanitize_case_name(name: str) -> str:
    """Sanitize custom simulation name to ensure valid filesystem and OpenFOAM directory conventions."""
    if not name or not isinstance(name, str):
        return "openzess_case"
    cleaned = re.sub(r'[^a-zA-Z0-9_\-]', '_', name.strip())
    return cleaned[:64] or "openzess_case"

from .mesh import Mesh2D
from .solver import AcceleratedSolver, CasePhysics, BUOYANT_ARCHETYPES, parse_dict_overrides
from .ai_predictor import predict_cavity_stokes, predict_potential_flow
from .vtk_writer import export_vtk
from .openfoam_export import generate_openfoam_case_zip
from .rust_bridge import is_rust_engine_online, solve_with_rust, benchmark_with_rust
from . import projects as project_store

app = FastAPI(title="OpenZess CFD Engine")

# The studio is served from this server (same origin) or from the Vite dev
# server on another local port. Allowing "*" let ANY website the user visits
# call this API cross-origin - including DELETE /api/projects.
LOCAL_ORIGIN_RE = re.compile(r"^https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?$")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=LOCAL_ORIGIN_RE.pattern,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global last results storage for VTK export
last_results = {}

# The compiled Vue bundle lives in frontend/dist (`npm run build`). The
# launchers rebuild it when stale (backend/frontend_build.py); importing this
# module never spawns npm.
frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
dist_dir = os.path.join(frontend_path, "dist")
_dist_index = os.path.join(dist_dir, "index.html")

if os.path.exists(_dist_index):
    static_dir = dist_dir
    newest_time = os.path.getmtime(_dist_index)
    import datetime
    dt_str = datetime.datetime.fromtimestamp(newest_time).strftime('%Y-%m-%d %H:%M:%S')
    print(f"[OpenZess] Serving frontend build from: {static_dir} (built {dt_str})")
else:
    # Never fall back to serving frontend/ itself: its index.html loads
    # /src/main.ts, which a browser cannot run (blank page).
    static_dir = None
    newest_time = 0
    print("[OpenZess] WARNING: frontend/dist not found - run `npm ci && npm run build` in frontend/.")

@app.middleware("http")
async def add_no_cache_headers(request, call_next):
    response = await call_next(request)
    # Aggressively disable caching for all studio pages, scripts, and stylesheets
    if request.url.path.startswith("/studio") or request.url.path.startswith("/assets") or request.url.path == "/":
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        response.headers["X-OpenZess-Build-Time"] = str(int(newest_time))
    return response

@app.get("/")
@app.get("/studio")
@app.get("/studio/")
@app.get("/studio/index.html")
def serve_studio_index():
    index_file = os.path.join(static_dir, "index.html") if static_dir else ""
    if index_file and os.path.exists(index_file):
        return FileResponse(
            index_file,
            media_type="text/html",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    # No compiled build available: return an explicit 404 (redirecting back to
    # /studio/ would create an infinite redirect loop with the route above).
    return Response(
        content=(
            "<!DOCTYPE html><html><head><title>OpenZess Studio - Build Required</title></head>"
            "<body style=\"font-family: sans-serif; background:#130f16; color:#e2e8f0; padding:40px;\">"
            "<h2>OpenZess Studio frontend build not found</h2>"
            "<p>No compiled <code>frontend/dist/index.html</code> was detected. "
            "Run <code>npm install && npm run build</code> inside the <code>frontend/</code> directory, then restart the server.</p>"
            "</body></html>"
        ),
        media_type="text/html",
        status_code=404,
        headers={"Cache-Control": "no-store"}
    )

if static_dir:
    app.mount("/studio", StaticFiles(directory=static_dir, html=True), name="frontend")
    assets_dir = os.path.join(static_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


@app.get("/health")
@app.get("/api/health")
def health_check():
    rust_live = is_rust_engine_online(timeout=0.2)
    return {
        "status": "online",
        "engine": "OpenZess Hybrid Physics Platform",
        "hybrid_mode": True,
        "engines": {
            "python": "SciPy Sparse Fractional-Step (Active)",
            "ai": "Instant preview: potential flow / Stokes cavity (no ML model)",
            "rust": f"Rust Rayon sidecar ({'online' if rust_live else 'offline - Python fallback'})"
        },
        "features": ["Hybrid Rust+Python", "VTK Export", "OpenFOAM case export", "Three.js 3D", "Instant potential-flow preview"]
    }


@app.get("/api/engine/status")
def engine_status():
    rust_live = is_rust_engine_online(timeout=0.2)
    return {
        "hybrid": True,
        "active_backend": "Rust Rayon Engine" if rust_live else "Python SciPy Engine",
        "rust_sidecar_online": rust_live,
        "available_engines": [
            {"id": "python", "name": "Python SciPy Solver", "type": "High-Precision Sparse CPU"},
            {"id": "rust", "name": "Rust kernel", "type": "Multi-threaded (Rayon) explicit solver"},
            {"id": "ai", "name": "Instant preview", "type": "Potential flow / Stokes solve (no ML model)"}
        ]
    }


@app.get("/api/engine/benchmark")
def run_hybrid_benchmark(steps: int = 150):
    rust_data = benchmark_with_rust(nx=41, ny=41, steps=steps)
    return {
        "engine": "rust" if rust_data else "python",
        "status": "success",
        "data": rust_data or {"message": "Rust sidecar is in standby; benchmark running on Python SciPy baseline."}
    }


# ---------------------------------------------------------------------------
# Project Persistence: named simulation snapshots that SURVIVE reloads
# ---------------------------------------------------------------------------
@app.post("/api/projects")
@app.post("/api/projects/save")
def save_project_snapshot(payload: dict = None):
    """Save the complete project state under a named snapshot."""
    if not isinstance(payload, dict):
        payload = {}
    name = payload.get("name") or payload.get("caseName") or "openzess_project"
    state = payload.get("state") or {
        k: v for k, v in payload.items() if k not in ("name", "caseName")
    }
    meta = project_store.save_project(name, state)
    return {"status": "success", **meta}


@app.get("/api/projects")
def list_project_snapshots():
    return {"status": "success", "projects": project_store.list_projects()}


@app.get("/api/projects/load")
def load_project_snapshot(name: str = ""):
    state = project_store.load_project(name) if name else None
    if state is None:
        return {"status": "not_found", "state": None}
    return {"status": "success", "state": state}


@app.delete("/api/projects")
def delete_project_snapshot(name: str = ""):
    removed = project_store.delete_project(name) if name else False
    return {"status": "success" if removed else "not_found", "deleted": removed}


@app.get("/api/export/vtk")
def download_vtk(name: str = "openzess_simulation"):
    """Export and download the last simulation run as a VTK file for ParaView."""
    safe_name = sanitize_case_name(name)
    if last_results and "mesh" in last_results:
        mesh = last_results["mesh"]
        u = last_results["u"]
        v = last_results["v"]
        p = last_results["p"]
    else:
        # Default baseline domain if accessed prior to running a simulation
        mesh = Mesh2D(nx=41, ny=41, lx=1.0, ly=1.0)
        u = np.zeros((41, 41))
        v = np.zeros((41, 41))
        p = np.zeros((41, 41))
    
    vtk_bytes = export_vtk(mesh, u, v, p)
    return Response(
        content=vtk_bytes,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={safe_name}.vtk"
        }
    )


@app.get("/api/export/openfoam")
@app.get("/api/export/openfoam-zip")
def download_openfoam_case(name: str = "openzess_openfoam_case"):
    """Export complete OpenFOAM case directory structure as a ZIP package."""
    safe_name = sanitize_case_name(name)
    params = last_results.get("params", {})
    zip_bytes = generate_openfoam_case_zip(params, case_name=safe_name)
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={safe_name}_openfoam_case.zip"
        }
    )


# Hard limits on client-supplied run parameters. The solver allocates
# O(nx*ny) memory and an LU factorization, so an unbounded grid request
# from any WebSocket client could exhaust RAM.
MAX_GRID = 256
MAX_ITERATIONS = 20000


def _clamp(value, lo, hi):
    return max(lo, min(hi, value))


def _field(arr) -> list:
    """Round a 2-D field to 3 decimals for transport (cuts JSON ~70%)."""
    return np.round(np.nan_to_num(np.asarray(arr, dtype=float), nan=0.0), 3).tolist()


def _frame(solver, mesh, *, iteration, residual, converged, mode, courant, continuity,
           extra=None, inviscid=False):
    """Build one WebSocket frame from a solver holding u, v, p."""
    speed = np.sqrt(solver.u**2 + solver.v**2)
    cd, cl, forces_extra = solver.compute_forces(include_viscous=not inviscid)
    payload = {
        "iteration": int(iteration),
        "residual": float(residual),
        "converged": bool(converged),
        "u": _field(solver.u),
        "v": _field(solver.v),
        "p": _field(solver.p),
        "speed": _field(speed),
        "mode": mode,
        "cd": cd,
        "cl": cl,
        "courantMax": float(np.round(courant, 4)),
        "continuityError": float(continuity),
        "uMax": float(np.round(np.max(speed), 4)),
        "uAvg": float(np.round(np.mean(speed), 4)),
        "pMin": float(np.round(np.min(solver.p), 4)),
        "pMax": float(np.round(np.max(solver.p), 4)),
        "dx": float(mesh.dx),
        "dy": float(mesh.dy),
        **forces_extra,
    }
    if extra:
        payload.update(extra)
    return payload


def _scalar_extra(solver) -> dict:
    """Transported scalar for archetypes that carry one (real data only)."""
    arch = solver.archetype
    if arch in ("plume", "weather_plume"):
        temp = solver.physics.ambient_temp + solver.physics.delta_t_ref * solver.s
        return {"scalar": _field(temp), "scalarName": "T", "scalarUnit": "K"}
    if arch == "water_dam":
        return {"scalar": _field(solver.s), "scalarName": "alpha.heavy", "scalarUnit": ""}
    if arch == "venturi":
        return {"scalar": _field(solver.s), "scalarName": "tracer", "scalarUnit": ""}
    return {}


@app.websocket("/ws/simulate")
async def websocket_simulate(websocket: WebSocket):
    global last_results
    # CORS does not cover WebSockets: refuse browser pages from other sites
    # (non-browser clients send no Origin header).
    origin = websocket.headers.get("origin")
    if origin and not LOCAL_ORIGIN_RE.match(origin):
        await websocket.close(code=1008)
        return
    await websocket.accept()
    try:
        data_str = await websocket.receive_text()
        params = json.loads(data_str)

        # Support both camelCase (from frontend) and snake_case
        nx = _clamp(int(params.get("gridResolution", params.get("nx", 41))), 8, MAX_GRID)
        ny = _clamp(int(params.get("gridResolution", params.get("ny", 41))), 8, MAX_GRID)
        Re = float(params.get("reynoldsNumber", params.get("Re", 100.0)))
        mode = str(params.get("solverMode", params.get("mode", "cfd"))).lower()
        archetype = str(params.get("archetype", "cavity")).lower()
        max_iter = _clamp(int(params.get("maxIterations", params.get("max_iter", 300))), 1, MAX_ITERATIONS)
        dt = float(params.get("dt", 0.005))
        aoa_deg = float(params.get('aoa', params.get('angle_of_attack', params.get('angleOfAttack', 0.0))))

        # Full user physics: substance, inlet velocity, gravity, temperatures,
        # custom obstacle geometry — all applied to the actual solver.
        # Temperatures are Kelvin.
        substance = str(params.get("substance", "air")).lower()
        nf = params.get("naturalForces", {}) or {}
        gravity = nf.get("gravity") or params.get("gravity") or [0.0, -9.81, 0.0]
        ambient_temp = float(nf.get("ambientTemp", params.get("ambientTemp", 293.15)))
        inlet_velocity = float(
            params.get("inletVelocity", params.get("lidVelocity", 1.0))
        )
        obstacle_spec = params.get("obstacleSpec") or params.get("geometry")

        # User-edited dictionary overrides (deltaT, nu, inlet velocity) from
        # the dict editor — applied to the real solver run.
        overrides = parse_dict_overrides(params.get("dictOverrides"))
        dt = _clamp(overrides.get("dt", dt), 1e-5, 0.1)

        physics = CasePhysics(
            substance=substance,
            inlet_velocity=overrides.get("inlet_velocity", inlet_velocity),
            reynolds=Re,
            gravity=gravity,
            ambient_temp=ambient_temp,
            hot_temp=params.get("hotTemp"),
            nu=overrides.get("nu"),
        )

        # Channel / external-flow archetypes get a 2:1 domain
        lx = 2.0 if archetype in ["cylinder", "obstacle", "airfoil"] else 1.0
        ly = 1.0
        if archetype in ["cylinder", "obstacle", "airfoil"]:
            nx = _clamp(max(nx * 2, 60), 8, 2 * MAX_GRID)

        mesh = Mesh2D(nx=nx, ny=ny, lx=lx, ly=ly)
        solver = AcceleratedSolver(
            mesh=mesh, physics=physics, archetype=archetype, aoa_deg=aoa_deg,
            obstacle_spec=obstacle_spec,
        )
        mask_list = solver.obstacle_mask.tolist()

        # Buoyancy-driven flows have no instant approximation and the Rust
        # kernel has no scalar transport: run them on the Python CFD solver.
        if mode in ("ai", "rust", "rust_bare_metal") and archetype in BUOYANT_ARCHETYPES:
            print(f"[OpenZess] '{mode}' mode does not model buoyancy; running '{archetype}' on the CFD solver.")
            mode = "cfd"

        # 1. Instant preview ("ai" mode): potential flow / Stokes cavity.
        #    This is NOT a neural network — see backend/ai_predictor.py.
        if mode == "ai":
            if archetype == "cavity":
                u, v, p = predict_cavity_stokes(mesh, solver.lid_velocity, physics.nu)
            else:
                u, v, p = predict_potential_flow(mesh, solver.obstacle_mask, solver.lid_velocity)
            solver.u, solver.v, solver.p = u, v, p
            last_results = {"mesh": mesh, "u": u, "v": v, "p": p, "params": params}
            speed_max = float(np.max(np.sqrt(u**2 + v**2)))
            payload = _frame(
                solver, mesh, iteration=1, residual=0.0, converged=True, mode="ai",
                courant=speed_max * dt / mesh.dx,
                continuity=solver._continuity_error(dt),
                extra={"obstacleMask": mask_list},
                inviscid=archetype != "cavity",
            )
            await websocket.send_text(json.dumps(payload))
            await websocket.close()
            return

        # 2. Rust kernel (multi-threaded Jacobi Poisson via Rayon)
        if mode in ["rust", "rust_bare_metal"]:
            # Blocking HTTP call: run it in a worker thread so the event loop
            # (other clients, health checks) is not frozen meanwhile.
            rust_res = await asyncio.to_thread(
                solve_with_rust,
                nx=nx, ny=ny, lx=lx, ly=ly, nu=physics.nu, dt=dt,
                steps=min(max_iter, 2000), lid_u=solver.lid_velocity,
                archetype=archetype, obstacle_mask=mask_list,
            )
            if rust_res and rust_res.get("diverged"):
                await websocket.send_text(json.dumps({
                    "error": (
                        f"Rust solver diverged after {rust_res.get('iteration')} steps. "
                        "Lower the Reynolds number or dt, or refine the grid."
                    ),
                    "diverged": True,
                }))
                await websocket.close()
                return
            if rust_res:
                solver.u = np.array(rust_res["u"], dtype=float)
                solver.v = np.array(rust_res["v"], dtype=float)
                solver.p = np.array(rust_res["p"], dtype=float)
                last_results = {"mesh": mesh, "u": solver.u, "v": solver.v, "p": solver.p, "params": params}
                payload = _frame(
                    solver, mesh,
                    iteration=rust_res["iteration"],
                    residual=rust_res["residual"],
                    converged=rust_res["converged"],
                    mode="rust_bare_metal",
                    courant=rust_res.get("cfl", 0.0),
                    continuity=rust_res.get("dt_used", dt) * float(np.mean(np.abs(solver.divergence()))),
                    extra={"obstacleMask": mask_list, "elapsed_ms": rust_res.get("elapsed_ms", 0.0)},
                )
                await websocket.send_text(json.dumps(payload))
                await websocket.close()
                return
            print("🦀 Rust sidecar offline/unreachable; automatically falling back to Python SciPy.")

        # 3. Python CFD (SciPy sparse fractional-step AcceleratedSolver)
        # Adaptive frame striding: smooth playback without flooding the socket
        stride = 4 if max_iter <= 80 else (6 if max_iter <= 200 else 8)

        for iteration in range(1, max_iter + 1):
            res = solver.step(dt)

            if solver.diverged:
                last_results = {"mesh": mesh, "u": solver.u, "v": solver.v, "p": solver.p, "params": params}
                await websocket.send_text(json.dumps({
                    "error": (
                        f"Simulation diverged at iteration {iteration}: velocity exceeded "
                        "10x the reference speed. Lower the Reynolds number or dt, or "
                        "refine the grid."
                    ),
                    "diverged": True,
                    "iteration": iteration,
                }))
                break

            converged = res < 1e-5
            if iteration == 1 or iteration % stride == 0 or converged or iteration == max_iter:
                last_results = {"mesh": mesh, "u": solver.u, "v": solver.v, "p": solver.p, "params": params}
                extra = _scalar_extra(solver)
                # Static geometry: send the mask only on the first/last frame
                if iteration == 1 or iteration == max_iter or converged:
                    extra["obstacleMask"] = mask_list
                payload = _frame(
                    solver, mesh, iteration=iteration, residual=res,
                    converged=converged, mode="cfd", courant=solver.cfl,
                    continuity=solver.continuity_error, extra=extra,
                )
                await websocket.send_text(json.dumps(payload))
                await asyncio.sleep(0.002)  # yield to the event loop

                if converged:
                    break

        # Close explicitly (matches the AI and Rust paths) so clients receive a
        # proper close frame instead of an abrupt TCP teardown.
        await websocket.close()

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"Error during simulation stream: {e}")
        try:
            await websocket.send_text(json.dumps({"error": str(e)}))
        except Exception:
            pass
