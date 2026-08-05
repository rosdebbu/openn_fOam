"""
OpenZess FastAPI Server
Exposes REST APIs & WebSockets for live CFD simulation streaming and VTK exports.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
import asyncio
import numpy as np
import os
import json

from .mesh import Mesh2D
from .solver import AcceleratedSolver
from .ai_predictor import predict_pinn_flow
from .vtk_writer import export_vtk

app = FastAPI(title="OpenZess CFD Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global last results storage for VTK export
last_results = {}

# Serve Frontend static files (built Vue 3 dist or raw frontend)
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
dist_path = os.path.join(frontend_path, "dist")
static_dir = dist_path if os.path.exists(dist_path) else frontend_path
if os.path.exists(static_dir):
    app.mount("/studio", StaticFiles(directory=static_dir, html=True), name="frontend")


@app.get("/")
def root_redirect():
    return RedirectResponse(url="/studio/index.html")


@app.get("/api/health")
def health_check():
    return {"status": "online", "engine": "OpenZess Accelerated CFD", "features": ["VTK Export", "Three.js 3D", "Graphify"]}


@app.get("/api/export/vtk")
def download_vtk():
    """Export and download the last simulation run as a VTK file for ParaView."""
    if not last_results:
        return {"error": "No simulation results available to export."}
    
    mesh = last_results["mesh"]
    u = last_results["u"]
    v = last_results["v"]
    p = last_results["p"]
    
    export_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "exports")
    vtk_path = os.path.join(export_dir, "openzess_simulation.vtk")
    
    export_vtk(mesh, u, v, p, vtk_path)
    return FileResponse(vtk_path, media_type="application/octet-stream", filename="openzess_simulation.vtk")


@app.websocket("/ws/simulate")
async def websocket_simulate(websocket: WebSocket):
    await websocket.accept()
    try:
        data_str = await websocket.receive_text()
        params = json.loads(data_str)
        
        nx = int(params.get("nx", 41))
        ny = int(params.get("ny", 41))
        Re = float(params.get("Re", 100.0))
        mode = params.get("mode", "cfd")
        max_iter = int(params.get("max_iter", 1000))
        
        mesh = Mesh2D(nx=nx, ny=ny)
        
        if mode == "ai":
            u, v, p = predict_pinn_flow(mesh, Re)
            speed = np.sqrt(u**2 + v**2).tolist()
            
            global last_results
            last_results = {"mesh": mesh, "u": u, "v": v, "p": p}
            
            payload = {
                "iteration": 1,
                "residual": 0.0,
                "converged": True,
                "u": u.tolist(),
                "v": v.tolist(),
                "p": p.tolist(),
                "speed": speed,
                "mode": "ai"
            }
            await websocket.send_text(json.dumps(payload))
            await websocket.close()
            return

        # Traditional CFD mode
        solver = AcceleratedSolver(mesh=mesh, Re=Re)
        dt = 0.005
        
        for iteration in range(1, max_iter + 1):
            res = solver.step(dt)
            
            if iteration % 15 == 0 or res < 1e-5 or iteration == max_iter:
                speed = np.sqrt(solver.u**2 + solver.v**2).tolist()
                
                last_results = {"mesh": mesh, "u": solver.u, "v": solver.v, "p": solver.p}
                
                payload = {
                    "iteration": iteration,
                    "residual": float(res),
                    "converged": bool(res < 1e-5),
                    "u": solver.u.tolist(),
                    "v": solver.v.tolist(),
                    "p": solver.p.tolist(),
                    "speed": speed,
                    "mode": "cfd"
                }
                await websocket.send_text(json.dumps(payload))
                await asyncio.sleep(0.01)
                
                if res < 1e-5:
                    break
                    
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Error during simulation stream: {e}")
        try:
            await websocket.send_text(json.dumps({"error": str(e)}))
        except:
            pass
