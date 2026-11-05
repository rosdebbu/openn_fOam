"""Server hardening and launcher tests."""

import os

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

import backend.app as appmod
from backend import frontend_build

client = TestClient(appmod.app)


@pytest.mark.parametrize("origin", ["http://localhost:5173", "http://127.0.0.1:8000"])
def test_cors_allows_local_dev_origins(origin):
    resp = client.get("/api/projects", headers={"Origin": origin})
    assert resp.headers.get("access-control-allow-origin") == origin


def test_cors_rejects_foreign_sites():
    # A page on evil.example must not be able to read or DELETE projects
    resp = client.options("/api/projects", headers={
        "Origin": "https://evil.example",
        "Access-Control-Request-Method": "DELETE",
    })
    assert "access-control-allow-origin" not in resp.headers


def test_websocket_rejects_foreign_origin():
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/ws/simulate", headers={"Origin": "https://evil.example"}) as ws:
            ws.receive_text()
    assert exc.value.code == 1008


def test_missing_build_shows_instructions_not_raw_source(monkeypatch):
    monkeypatch.setattr(appmod, "static_dir", None)
    resp = client.get("/studio/index.html")
    assert resp.status_code == 404
    assert "npm install" in resp.text and "/src/main.ts" not in resp.text


def _fake_frontend(tmp_path, monkeypatch, built: bool):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.ts").write_text("x")
    (tmp_path / "package.json").write_text("{}")
    (tmp_path / "node_modules").mkdir()
    index = tmp_path / "dist" / "index.html"
    if built:
        index.parent.mkdir()
        index.write_text("<html>")
        # dist newer than every source
        os.utime(index, (os.path.getmtime(tmp_path / "src" / "main.ts") + 10,) * 2)
    monkeypatch.setattr(frontend_build, "FRONTEND_DIR", str(tmp_path))
    monkeypatch.setattr(frontend_build, "DIST_INDEX", str(index))
    return index


def test_fresh_build_is_not_rebuilt(tmp_path, monkeypatch):
    _fake_frontend(tmp_path, monkeypatch, built=True)
    monkeypatch.setattr(frontend_build.subprocess, "run",
                        lambda *a, **k: pytest.fail("npm must not run for a fresh build"))
    assert not frontend_build.build_is_stale()
    assert frontend_build.ensure_frontend_build() is True


def test_stale_build_runs_npm_portably(tmp_path, monkeypatch):
    index = _fake_frontend(tmp_path, monkeypatch, built=False)
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        index.parent.mkdir(exist_ok=True)
        index.write_text("<html>")

        class Result:
            returncode, stdout, stderr = 0, "", ""
        return Result()

    monkeypatch.setattr(frontend_build.shutil, "which", lambda name: "/opt/node/bin/npm")
    monkeypatch.setattr(frontend_build.subprocess, "run", fake_run)
    assert frontend_build.ensure_frontend_build() is True
    cmd, kwargs = calls[-1]
    # Full argv, no shell: `shell=True` + a list ran a bare `npm` on POSIX
    assert cmd == ["/opt/node/bin/npm", "run", "build"]
    assert not kwargs.get("shell")


def test_missing_npm_is_reported_not_crashed(tmp_path, monkeypatch, capsys):
    _fake_frontend(tmp_path, monkeypatch, built=False)
    monkeypatch.setattr(frontend_build.shutil, "which", lambda name: None)
    assert frontend_build.ensure_frontend_build() is False
    assert "npm was not found" in capsys.readouterr().out
