"""Text-to-3D Mesh Generator for OpenZess CFD.

Provider cascade:
  1. Meshy v2 REST API (when MESHY_API_KEY is set)
  2. Free HuggingFace Space: tencent/Hunyuan3D-2 (/shape_generation)
  3. Free HuggingFace Space: hysts/Shap-E (/text-to-3d)

Saves real .glb 3D meshes to data/generated_3d/ for Three.js GLTFLoader
rendering and Navier-Stokes obstacle voxelization.
"""

import os
import re
import shutil
import time
from typing import Any

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "data", "generated_3d")
os.makedirs(OUT_DIR, exist_ok=True)


def _slug(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9_-]+", "_", text.strip().lower()).strip("_")
    return (s[:32] or "model") + f"_{int(time.time())}"


def _extract_filepath(res: Any) -> str | None:
    if isinstance(res, str) and os.path.exists(res):
        return res
    if isinstance(res, dict):
        for k in ("value", "path", "name"):
            v = res.get(k)
            if isinstance(v, str) and os.path.exists(v):
                return v
    if isinstance(res, (list, tuple)):
        for item in res:
            fp = _extract_filepath(item)
            if fp:
                return fp
    return None


def _generate_meshy(prompt: str, api_key: str) -> str:
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    r = requests.post(
        "https://api.meshy.ai/openapi/v2/text-to-3d",
        headers=headers,
        json={"mode": "preview", "prompt": prompt, "art_style": "realistic", "should_remesh": True},
        timeout=30,
    )
    r.raise_for_status()
    task_id = r.json()["result"]
    for _ in range(45):
        time.sleep(2.5)
        st = requests.get(f"https://api.meshy.ai/openapi/v2/text-to-3d/{task_id}", headers=headers, timeout=20).json()
        if st.get("status") == "SUCCEEDED":
            glb_url = st["model_urls"]["glb"]
            dst = os.path.join(OUT_DIR, f"{_slug(prompt)}.glb")
            with requests.get(glb_url, stream=True, timeout=60) as resp:
                resp.raise_for_status()
                with open(dst, "wb") as f:
                    shutil.copyfileobj(resp.raw, f)
            return dst
        if st.get("status") in ("FAILED", "EXPIRED"):
            raise RuntimeError(f"Meshy task failed: {st.get('task_error') or st.get('status')}")
    raise TimeoutError("Meshy Text-to-3D timed out")


def _generate_hf_hunyuan(prompt: str) -> str:
    from gradio_client import Client

    client = Client("tencent/Hunyuan3D-2", verbose=False)
    res = client.predict(
        caption=prompt,
        image=None,
        mv_image_front=None,
        mv_image_back=None,
        mv_image_left=None,
        mv_image_right=None,
        steps=20,
        guidance_scale=5.0,
        seed=1234,
        octree_resolution=128,
        check_box_rembg=True,
        num_chunks=8000,
        randomize_seed=True,
        api_name="/shape_generation",
    )
    src = _extract_filepath(res)
    if not src:
        raise RuntimeError("Hunyuan3D-2 did not return a mesh file")
    ext = os.path.splitext(src)[1] or ".glb"
    dst = os.path.join(OUT_DIR, f"{_slug(prompt)}{ext}")
    shutil.copyfile(src, dst)
    return dst


def _generate_hf_shape(prompt: str) -> str:
    from gradio_client import Client

    client = Client("hysts/Shap-E", verbose=False)
    res = client.predict(
        prompt=prompt,
        seed=0,
        guidance_scale=15.0,
        num_inference_steps=32,
        api_name="/text-to-3d",
    )
    src = _extract_filepath(res)
    if not src:
        raise RuntimeError("Shap-E did not return a mesh file")
    ext = os.path.splitext(src)[1] or ".glb"
    dst = os.path.join(OUT_DIR, f"{_slug(prompt)}{ext}")
    shutil.copyfile(src, dst)
    return dst


def generate_3d_mesh(prompt: str) -> dict[str, Any]:
    """Generate a real 3D .glb mesh from a text prompt."""
    t0 = time.perf_counter()
    errors: list[str] = []

    meshy_key = os.environ.get("MESHY_API_KEY", "").strip()
    if meshy_key:
        try:
            dst = _generate_meshy(prompt, meshy_key)
            fname = os.path.basename(dst)
            return {
                "ok": True,
                "provider": "Meshy v2 API",
                "filename": fname,
                "glb_url": f"/api/generated-3d/{fname}",
                "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
            }
        except Exception as e:
            errors.append(f"Meshy: {e}")

    for name, fn in (("HuggingFace Hunyuan3D-2", _generate_hf_hunyuan), ("HuggingFace Shap-E", _generate_hf_shape)):
        try:
            dst = fn(prompt)
            fname = os.path.basename(dst)
            return {
                "ok": True,
                "provider": name,
                "filename": fname,
                "glb_url": f"/api/generated-3d/{fname}",
                "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
            }
        except Exception as e:
            errors.append(f"{name}: {e}")

    return {
        "ok": False,
        "error": " | ".join(errors) or "All Text-to-3D providers failed",
        "hint": "Public HuggingFace GPU quota may be busy. Retry in 30s or set MESHY_API_KEY in your environment.",
        "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
    }
