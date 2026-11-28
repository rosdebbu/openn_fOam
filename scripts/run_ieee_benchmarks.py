"""
Runs real quantitative experiments for the OpenZess Studio IEEE Research Paper:
  1. Grid Independence Study (21x21, 31x31, 41x41, 51x51) against Ghia et al. (1982) at Re = 100.
  2. RL Ablation Study: Base Qwen/Qwen3-0.6B vs. Retrained SFT+GRPO LoRA (openzess_qwen3_0.6b_rl)
     on a 6-prompt CFD benchmark using the exact Navier-Stokes + Ghia verifier.

Writes real measured tables to docs/IEEE_BENCHMARK_RESULTS.md.
"""

import os
import sys
import time
import json
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from train_openzess_grpo import verify_cfd_physics, score_completion, render_prompt, safe_dt

EVAL_PROMPTS = [
    "Run a lid-driven cavity benchmark at Re=100 on a 41x41 grid.",
    "Simulate airflow around a simple house in wind with safe CFL.",
    "Simulate 120 km/h wind on a 20m glass tower with FSI.",
    "Simulate water flow through a Venturi pipe constriction.",
    "Run a Karman vortex shedding simulation behind a cylinder at Re=100.",
    "Simulate airflow over a NACA airfoil at Re=300.",
]


def run_grid_independence():
    rows = []
    for n in (21, 31, 41, 51):
        dt = safe_dt(n, 100.0)
        t0 = time.perf_counter()
        res = verify_cfd_physics({"reynoldsNumber": 100.0, "dt": dt, "gridResolution": n, "archetype": "cavity"})
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        rows.append({
            "grid": f"{n}x{n}",
            "cells": (n - 1) * (n - 1),
            "stable": bool(res.get("stable", False)),
            "max_cfl": float(res.get("cfl", 0.0)),
            "ghia_rmse": float(res.get("ghia_rmse", 1.0)),
            "runtime_ms": elapsed_ms,
        })
    return rows


def evaluate_model(model, tok, label):
    import torch
    valid_json = 0
    cfl_stable = 0
    rewards = []
    for p in EVAL_PROMPTS:
        prompt_text = render_prompt(tok, p)
        inputs = tok(prompt_text, return_tensors="pt").to(model.device)
        with torch.no_grad():
            out = model.generate(**inputs, max_new_tokens=160, do_sample=False)
        gen = tok.decode(out[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True).strip()
        r = score_completion(gen)
        rewards.append(r)
        if r > -3.0:
            valid_json += 1
        if r >= 2.0:
            cfl_stable += 1
    n = len(EVAL_PROMPTS)
    return {
        "model": label,
        "valid_json_pct": 100.0 * valid_json / n,
        "cfl_stable_pct": 100.0 * cfl_stable / n,
        "mean_reward": float(np.mean(rewards)),
    }


def run_rl_ablation():
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    from peft import PeftModel

    model_id = "Qwen/Qwen3-0.6B"
    adapter_dir = os.path.join(ROOT, "openzess_qwen3_0.6b_rl")
    tok = AutoTokenizer.from_pretrained(model_id)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    base = AutoModelForCausalLM.from_pretrained(
        model_id,
        dtype=torch.bfloat16 if device == "cuda" else torch.float32,
    ).to(device)
    base.eval()

    print("Evaluating Base Qwen3-0.6B...", flush=True)
    base_res = evaluate_model(base, tok, "Base Qwen3-0.6B (No RL)")

    rl_res = None
    if os.path.isdir(adapter_dir):
        print("Evaluating OpenZess SFT + GRPO LoRA...", flush=True)
        rl_model = PeftModel.from_pretrained(base, adapter_dir)
        rl_model.eval()
        rl_res = evaluate_model(rl_model, tok, "OpenZess SFT + GRPO (RTX 5050)")

    return [r for r in (base_res, rl_res) if r is not None]


def main():
    print("Running Grid Independence Study (Ghia 1982, Re=100)...")
    grid_rows = run_grid_independence()
    for r in grid_rows:
        print(" ", r)

    print("Running RL Ablation Study on RTX 5050...")
    rl_rows = run_rl_ablation()
    for r in rl_rows:
        print(" ", r)

    md = [
        "# OpenZess Studio — Verified IEEE Research Benchmark Results\n",
        "Generated automatically by `scripts/run_ieee_benchmarks.py`.\n",
        "## 1. Grid Independence Study (Lid-Driven Cavity, Re = 100, Ghia et al. 1982)\n",
        "| Grid | Cells | Stable | Max CFL | Ghia Centerline RMSE | Verifier Runtime (ms) |",
        "| :--- | :---: | :---: | :---: | :---: | :---: |",
    ]
    for r in grid_rows:
        md.append(f"| {r['grid']} | {r['cells']} | {'Yes' if r['stable'] else 'No'} | {r['max_cfl']:.3f} | {r['ghia_rmse']:.4f} | {r['runtime_ms']:.1f} |")

    md += [
        "\n## 2. RL Ablation Study (6-Prompt CFD Suite on RTX 5050 Laptop GPU)\n",
        "| Model Variant | Valid JSON (%) | CFL-Stable Specs (%) | Mean Physics Reward |",
        "| :--- | :---: | :---: | :---: |",
    ]
    for r in rl_rows:
        md.append(f"| {r['model']} | {r['valid_json_pct']:.1f}% | {r['cfl_stable_pct']:.1f}% | {r['mean_reward']:+.2f} |")

    out_path = os.path.join(ROOT, "docs", "IEEE_BENCHMARK_RESULTS.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print("Saved:", out_path)


if __name__ == "__main__":
    main()
