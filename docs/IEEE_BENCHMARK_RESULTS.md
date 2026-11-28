# OpenZess Studio — Verified IEEE Research Benchmark Results

Generated automatically by `scripts/run_ieee_benchmarks.py`.

## 1. Grid Independence Study (Lid-Driven Cavity, Re = 100, Ghia et al. 1982)

| Grid | Cells | Stable | Max CFL | Ghia Centerline RMSE | Verifier Runtime (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| 21x21 | 400 | Yes | 0.000 | 0.2200 | 3.9 |
| 31x31 | 900 | Yes | 0.000 | 0.2325 | 3.2 |
| 41x41 | 1600 | Yes | 0.000 | 0.2381 | 3.7 |
| 51x51 | 2500 | Yes | 0.000 | 0.2378 | 4.6 |

## 2. RL Ablation Study (6-Prompt CFD Suite on RTX 5050 Laptop GPU)

| Model Variant | Valid JSON (%) | CFL-Stable Specs (%) | Mean Physics Reward |
| :--- | :---: | :---: | :---: |
| Base Qwen3-0.6B (No RL) | 33.3% | 33.3% | -1.66 |
| OpenZess SFT + GRPO (RTX 5050) | 100.0% | 100.0% | +5.36 |
