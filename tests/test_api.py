"""End-to-end tests of the FastAPI app (WebSocket stream + REST endpoints)."""

import io
import json
import zipfile

import numpy as np
import pytest
from fastapi.testclient import TestClient

import backend.app as appmod
from backend import projects
from backend.solver import ARCHETYPES, BUOYANT_ARCHETYPES

client = TestClient(appmod.app)


def run_ws(params: dict) -> list:
    frames = []
    with client.websocket_connect("/ws/simulate") as ws:
        ws.send_text(json.dumps(params))
        while True:
            try:
                frame = json.loads(ws.receive_text())
            except Exception:
                break
            frames.append(frame)
            if "error" in frame or frame.get("converged"):
                break
    return frames


def base_params(**overrides):
    params = {
        "archetype": "cavity", "solverMode": "cfd", "gridResolution": 21,
        "reynoldsNumber": 100, "maxIterations": 30, "dt": 0.005,
        "inletVelocity": 1.0, "hotTemp": 358.15,
    }
    params.update(overrides)
    if params["archetype"] == "cad":
        params.setdefault("obstacleSpec", {"shape": "circle", "cx": 0.4, "cy": 0.5, "size": 0.1})
    return params


@pytest.mark.parametrize("mode", ["cfd", "ai"])
@pytest.mark.parametrize("arch", ARCHETYPES)
def test_stream_every_archetype(arch, mode):
    frames = run_ws(base_params(archetype=arch, solverMode=mode))
    assert frames, "no frames received"
    last = frames[-1]
    assert "error" not in last, last.get("error")
    for key in ("cd", "cl", "courantMax", "continuityError", "uMax", "pMin", "pMax"):
        assert np.isfinite(last[key]), key
    assert last["continuityError"] >= 0
    assert "obstacleMask" in frames[0]
    expected_mode = "cfd" if (mode == "cfd" or arch in BUOYANT_ARCHETYPES) else "ai"
    assert last["mode"] == expected_mode


def test_buoyant_cases_stream_real_temperature_field():
    last = run_ws(base_params(archetype="plume"))[-1]
    temperature = np.array(last["scalar"])
    assert last["scalarName"] == "T" and last["scalarUnit"] == "K"
    assert temperature.min() >= 293.15 - 1e-6
    assert temperature.max() == pytest.approx(358.15, abs=1.0)  # heater strip


def test_grid_request_is_clamped():
    frames = run_ws(base_params(gridResolution=100_000, maxIterations=1))
    assert len(frames[0]["u"]) == appmod.MAX_GRID


def test_rust_mode_falls_back_to_python_when_sidecar_offline(monkeypatch):
    monkeypatch.setattr(appmod, "solve_with_rust", lambda **kwargs: None)
    last = run_ws(base_params(archetype="cylinder", solverMode="rust"))[-1]
    assert last["mode"] == "cfd"


def test_rust_divergence_is_reported(monkeypatch):
    monkeypatch.setattr(appmod, "solve_with_rust", lambda **kwargs: {"diverged": True, "iteration": 7})
    last = run_ws(base_params(archetype="cylinder", solverMode="rust"))[-1]
    assert last["diverged"] is True and "diverged" in last["error"]


def test_health(monkeypatch):
    monkeypatch.setattr(appmod, "is_rust_engine_online", lambda timeout=0.2: False)
    resp = client.get("/api/health")
    assert resp.status_code == 200 and resp.json()["status"] == "online"


def test_vtk_export_matches_last_run():
    run_ws(base_params(gridResolution=21, maxIterations=5))
    resp = client.get("/api/export/vtk", params={"name": "my case!"})
    assert resp.status_code == 200
    assert 'filename="my_case_.vtk"' in resp.headers["content-disposition"] or \
        "filename=my_case_.vtk" in resp.headers["content-disposition"]
    text = resp.text
    assert text.startswith("# vtk DataFile Version 3.0")
    assert "DIMENSIONS 21 21 1" in text and "POINT_DATA 441" in text
    mesh = appmod.last_results["mesh"]
    assert f"ORIGIN {mesh.dx / 2} {mesh.dy / 2} 0.0" in text  # cell centres
    velocity_lines = text.split("VECTORS velocity float\n")[1].split("\n\n")[0].splitlines()
    assert len(velocity_lines) == 441


def test_openfoam_zip_is_a_complete_runnable_case():
    resp = client.get("/api/export/openfoam-zip", params={"name": "demo"})
    assert resp.status_code == 200
    zf = zipfile.ZipFile(io.BytesIO(resp.content))
    names = set(zf.namelist())
    for required in ("system/controlDict", "system/fvSchemes", "system/fvSolution",
                     "system/blockMeshDict", "constant/transportProperties",
                     "0/U", "0/p", "Allrun"):
        assert f"demo/{required}" in names, required
    allrun = zf.getinfo("demo/Allrun")
    assert (allrun.external_attr >> 16) & 0o111, "Allrun must be executable"


def test_project_snapshot_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(projects, "SNAPSHOT_DIR", str(tmp_path))
    saved = client.post("/api/projects/save", json={"name": "Run A", "state": {"archetype": "cylinder"}})
    assert saved.json()["name"] == "Run_A"
    listing = client.get("/api/projects").json()["projects"]
    assert [p["name"] for p in listing] == ["Run_A"]
    assert client.get("/api/projects/load", params={"name": "Run A"}).json()["state"] == {"archetype": "cylinder"}
    assert client.delete("/api/projects", params={"name": "Run_A"}).json()["deleted"] is True
    assert client.get("/api/projects").json()["projects"] == []


def test_snapshot_names_cannot_escape_the_snapshot_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(projects, "SNAPSHOT_DIR", str(tmp_path))
    client.post("/api/projects/save", json={"name": "../../evil", "state": {}})
    assert [p.name for p in tmp_path.iterdir()] == ["______evil.json"]


def test_system_endpoint_reports_real_host_figures():
    info = client.get("/api/system").json()
    assert info["cpu_count"] and info["cpu_count"] > 0
    assert 0 < info["disk_used"] <= info["disk_total"]
    if info["mem_total"] is not None:  # stdlib cannot read RAM everywhere
        assert info["mem_total"] > 0
