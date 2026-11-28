"""
OpenZess RL + Qwen3-0.6B Training Pipeline (GRPO with Verifiable CFD Physics Rewards)

Trains Qwen/Qwen3-0.6B with QLoRA + GRPOTrainer so it outputs physically stable,
OpenZess-compatible CFD simulation parameters (archetype, substance, turbulenceModel,
reynoldsNumber, gridResolution, dt, tolerance) verified by an actual 2D Navier-Stokes
projection solver.

Usage:
  1. Test physics verifier & dataset locally (no GPU required):
       python scripts/train_openzess_grpo.py --dry-run

  2. Run full GRPO RL training (Google Colab T4 16GB or local CUDA GPU):
       pip install torch transformers trl peft datasets accelerate bitsandbytes numpy
       python scripts/train_openzess_grpo.py --steps 300 --output ./openzess_qwen3_0.6b_rl
"""

import argparse
import json
import math
import re
from typing import Any

import numpy as np

# Exact OpenZess schema (mirrors backend/solver.py & frontend/src/types/cfd.ts)
ARCHETYPES = (
    "airfoil", "cylinder", "venturi", "f1", "drone", "submarine",
    "plume", "cavity", "water_dam", "weather_plume", "obstacle", "cad",
    "house", "tower", "box",  # routed to archetype "cad" + shape by backend/ai_simulate.py
)
SUBSTANCES = ("air", "water", "seawater", "co2", "oil", "ethanol")
TURBULENCE_MODELS = ("laminar", "k-epsilon", "k-omega-sst", "spalart-allmaras")

SYSTEM_PROMPT = (
    "You are OpenZess CFD Engineer. Given a fluid simulation request, output ONLY a valid JSON object "
    "with keys: archetype, substance, turbulenceModel, reynoldsNumber, gridResolution, dt, tolerance.\n"
    f"Allowed archetypes: {', '.join(ARCHETYPES)}.\n"
    f"Allowed substances: {', '.join(SUBSTANCES)}.\n"
    f"Allowed turbulenceModel: {', '.join(TURBULENCE_MODELS)}.\n"
    "Choose gridResolution between 32 and 128 and dt so Courant number Co = U*dt/dx < 0.8 and "
    "viscous diffusion number nu*dt/dx^2 <= 0.25."
)

SEED_PROMPTS = [
    "Simulate laminar airflow past a cylinder at Reynolds number 100 on a 41x41 mesh.",
    "Simulate wind around a simple house with pitched roof at Re=200 on a 48x48 grid.",
    "Run a 120 km/h wind load simulation on a 20m glass tower at Re=300.",
    "Run a lid-driven cavity benchmark with water at Re=400 on a 64x64 grid.",
    "Simulate Bernoulli pressure drop in a Venturi tube with air at Re=250.",
    "High-speed airflow over a NACA 0012 airfoil at Re=1000 using k-omega-sst turbulence.",
    "Oil flowing through an obstacle channel at Re=50 with tight convergence tolerance.",
    "Simulate rising thermal plume in air at Re=150 on a 48x48 grid.",
    "Seawater flow past a submarine hull at Re=800 with k-epsilon turbulence.",
    "F1 car aerodynamics in air at Re=1200 on a 64x64 mesh with safe timestep.",
    "Drone rotor downwash in air at Re=300 on a 41x41 grid.",
    "Ethanol flow around a bluff obstacle at Re=200.",
    "simple house in wind",
    "20m glass tower in a gale",
    "box in a channel",
    "water in a pipe",
]

# (prompt template, archetype, substance, Re) -> exact-JSON targets for the SFT warm-up
SFT_TEMPLATES = [
    ("simple house in wind", "house", "air", 150), ("a simple house", "house", "air", 100),
    ("wind blowing on a small house", "house", "air", 200), ("20m glass tower", "tower", "air", 300),
    ("tall building in wind", "tower", "air", 300), ("box in channel", "box", "air", 100),
    ("water in pipe", "venturi", "water", 250), ("airfoil", "airfoil", "air", 1000),
    ("cavity", "cavity", "air", 100), ("cylinder wake", "cylinder", "air", 100),
    ("Formula 1 front wing", "f1", "air", 1200), ("submarine hull in seawater", "submarine", "water", 800),
]

# Honest refusal targets so Qwen3-0.6B learns to say "cannot simulate" on unsupported physics or non-CFD input
REFUSAL_TEMPLATES = [
    ("tell me a joke", "Not a CFD simulation request."),
    ("qwerty zzz", "Unrecognized object or fluid prompt."),
    ("supersonic Mach 3 shockwave", "OpenZess only solves subsonic incompressible Navier-Stokes."),
    ("jet engine combustion flame", "OpenZess does not solve reacting combustion chemistry."),
    ("electromagnetic plasma field", "OpenZess only solves incompressible fluid dynamics."),
]


def safe_dt(n: int, re_num: float) -> float:
    dx = 1.0 / (n - 1)
    return round(min(0.005, 0.5 * dx, 0.2 * dx * dx * re_num), 6)


def build_sft_pairs(copies: int = 40, seed: int = 0) -> list[tuple[str, str]]:
    """Synthetic (prompt, exact_json) pairs; Re/grid jitter so the model learns the schema, not strings."""
    import random

    rng = random.Random(seed)
    pairs = []
    for _ in range(copies):
        for prompt, arch, sub, re_num in SFT_TEMPLATES:
            n = rng.choice((32, 41, 48, 64))
            re_j = max(10, int(re_num * rng.choice((0.5, 1, 1, 2))))
            pairs.append((prompt, json.dumps({
                "archetype": arch, "substance": sub, "turbulenceModel": "laminar" if re_j < 500 else "k-omega-sst",
                "reynoldsNumber": re_j, "gridResolution": n, "dt": safe_dt(n, re_j), "tolerance": "1e-06",
            })))
        for bad_prompt, reason in REFUSAL_TEMPLATES:
            pairs.append((bad_prompt, json.dumps({"error": "unsupported", "reason": reason})))
    return pairs


def extract_json(text: str) -> dict[str, Any] | None:
    """Extract the first JSON object from model completion."""
    match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        obj = json.loads(match.group(0))
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        return None


def verify_cfd_physics(cfg: dict[str, Any]) -> dict[str, float | bool]:
    """
    Fast 2D incompressible Navier-Stokes (projection method) physics verifier.
    Checks explicit CFL stability, diffusion stability, residual decrease, and
    continuity conservation in ~5 ms per candidate.
    """
    nx = int(np.clip(cfg["gridResolution"], 24, 96))
    ny = nx
    re_num = float(cfg["reynoldsNumber"])
    dt = float(cfg["dt"])
    dx = 1.0 / (nx - 1)
    nu = 1.0 / max(re_num, 1.0)

    # Analytical CFL & viscous diffusion numbers for U_ref = 1.0
    cfl_init = 1.0 * dt / dx
    diff_num = nu * dt / (dx * dx)

    # Reject immediately if mathematically unstable for explicit advection/diffusion
    if dt <= 0 or re_num <= 0 or cfl_init >= 1.0 or diff_num > 0.25:
        return {
            "stable": False,
            "cfl_max": cfl_init,
            "diff_num": diff_num,
            "continuity_err": 1.0,
            "converged": False,
        }

    # Run 12 steps of 2D lid-driven cavity / channel projection
    u = np.zeros((ny, nx), dtype=np.float64)
    v = np.zeros((ny, nx), dtype=np.float64)
    p = np.zeros((ny, nx), dtype=np.float64)
    u[-1, :] = 1.0  # Moving lid / reference velocity

    init_div = None
    final_div = 1.0
    cfl_max = cfl_init

    for _ in range(12):
        un = u.copy()
        vn = v.copy()

        # First-order upwind advection + central diffusion on interior cells
        u_c = un[1:-1, 1:-1]
        v_c = vn[1:-1, 1:-1]
        du_dx = np.where(u_c > 0, (u_c - un[1:-1, :-2]) / dx, (un[1:-1, 2:] - u_c) / dx)
        du_dy = np.where(v_c > 0, (u_c - un[:-2, 1:-1]) / dx, (un[2:, 1:-1] - u_c) / dx)
        dv_dx = np.where(u_c > 0, (v_c - vn[1:-1, :-2]) / dx, (vn[1:-1, 2:] - v_c) / dx)
        dv_dy = np.where(v_c > 0, (v_c - vn[:-2, 1:-1]) / dx, (vn[2:, 1:-1] - v_c) / dx)

        lap_u = (un[1:-1, 2:] + un[1:-1, :-2] + un[2:, 1:-1] + un[:-2, 1:-1] - 4.0 * u_c) / (dx * dx)
        lap_v = (vn[1:-1, 2:] + vn[1:-1, :-2] + vn[2:, 1:-1] + vn[:-2, 1:-1] - 4.0 * v_c) / (dx * dx)

        u[1:-1, 1:-1] = u_c + dt * (-u_c * du_dx - v_c * du_dy + nu * lap_u)
        v[1:-1, 1:-1] = v_c + dt * (-u_c * dv_dx - v_c * dv_dy + nu * lap_v)

        # Divergence RHS
        div = ((u[1:-1, 2:] - u[1:-1, :-2]) + (v[2:, 1:-1] - v[:-2, 1:-1])) / (2.0 * dx)
        div_norm = float(np.mean(np.abs(div)))
        if init_div is None:
            init_div = div_norm

        # Pressure Poisson Jacobi sweeps
        rhs = div / dt
        for _ in range(15):
            p[1:-1, 1:-1] = 0.25 * (
                p[1:-1, 2:] + p[1:-1, :-2] + p[2:, 1:-1] + p[:-2, 1:-1] - dx * dx * rhs
            )
            p[0, :] = p[1, :]
            p[-1, :] = p[-2, :]
            p[:, 0] = p[:, 1]
            p[:, -1] = p[:, -2]

        # Velocity projection
        u[1:-1, 1:-1] -= dt * (p[1:-1, 2:] - p[1:-1, :-2]) / (2.0 * dx)
        v[1:-1, 1:-1] -= dt * (p[2:, 1:-1] - p[:-2, 1:-1]) / (2.0 * dx)

        # Enforce walls & moving lid
        u[0, :] = 0.0
        v[0, :] = 0.0
        u[:, 0] = 0.0
        v[:, 0] = 0.0
        u[:, -1] = 0.0
        v[:, -1] = 0.0
        u[-1, :] = 1.0
        v[-1, :] = 0.0

        if not (np.all(np.isfinite(u)) and np.all(np.isfinite(v)) and np.all(np.isfinite(p))):
            return {
                "stable": False,
                "cfl_max": 99.0,
                "diff_num": diff_num,
                "continuity_err": 99.0,
                "converged": False,
            }

        speed_max = float(np.max(np.hypot(u, v)))
        cfl_max = max(cfl_max, speed_max * dt / dx)
        final_div = float(
            np.mean(np.abs(((u[1:-1, 2:] - u[1:-1, :-2]) + (v[2:, 1:-1] - v[:-2, 1:-1])) / (2.0 * dx)))
        )

    y_grid = np.linspace(0.0, 1.0, nx)
    u_centerline = u[:, nx // 2]
    ghia_y = np.array([1.0, 0.9766, 0.9688, 0.9609, 0.9531, 0.8516, 0.7344, 0.6172, 0.5, 0.4531, 0.2813, 0.1719, 0.1016, 0.0703, 0.0625, 0.0547, 0.0])
    ghia_u100 = np.array([1.0, 0.84123, 0.78871, 0.73722, 0.68717, 0.23151, 0.00332, -0.13641, -0.20581, -0.21090, -0.15662, -0.10150, -0.06434, -0.04775, -0.04192, -0.03717, 0.0])
    u_interp = np.interp(ghia_y, y_grid, u_centerline)
    ghia_rmse = float(np.sqrt(np.mean((u_interp - ghia_u100) ** 2)))

    return {
        "stable": cfl_max < 1.0 and math.isfinite(final_div),
        "cfl_max": cfl_max,
        "diff_num": diff_num,
        "continuity_err": final_div,
        "converged": (init_div is not None) and (final_div <= init_div + 1e-6),
        "ghia_rmse": ghia_rmse,
    }


def score_completion(text: str) -> float:
    """Verifiable physics reward function for GRPOTrainer."""
    cfg = extract_json(text)
    if cfg is None:
        return -3.0

    required = ("archetype", "substance", "turbulenceModel", "reynoldsNumber", "gridResolution", "dt")
    if any(k not in cfg for k in required):
        return -2.0

    score = 0.0
    if cfg["archetype"] in ARCHETYPES:
        score += 0.5
    if cfg["substance"] in SUBSTANCES:
        score += 0.25
    if cfg["turbulenceModel"] in TURBULENCE_MODELS:
        score += 0.25

    try:
        res = verify_cfd_physics(cfg)
    except Exception:
        return -4.0

    if not res["stable"]:
        return -5.0

    score += 2.0  # CFL & diffusion stable
    if res["converged"]:
        score += 1.5
    if float(res["continuity_err"]) < 0.05:
        score += 1.0
    # Prefer efficient timesteps (not absurdly tiny dt=1e-9, not unstable dt)
    cfl = float(res["cfl_max"])
    if 0.05 <= cfl <= 0.75:
        score += 0.5
    # Benchmark-verified accuracy reward against Ghia et al. (1982) centerline profile
    ghia_rmse = float(res.get("ghia_rmse", 1.0))
    if ghia_rmse < 0.65:
        score += round(1.5 * max(0.0, 1.0 - ghia_rmse / 0.65), 2)
    return score


def grpo_reward_fn(completions: list[Any], **kwargs: Any) -> list[float]:
    """Adapter compatible with trl.GRPOTrainer (handles both string and chat-message completions)."""
    rewards = []
    for comp in completions:
        if isinstance(comp, list) and comp and isinstance(comp[0], dict):
            text = comp[0].get("content", "")
        else:
            text = str(comp)
        rewards.append(score_completion(text))
    return rewards


def run_dry_run() -> None:
    print("=== OpenZess GRPO Physics Reward Verifier Dry-Run ===")
    samples = [
        (
            "Valid & Stable Cylinder",
            json.dumps({
                "archetype": "cylinder",
                "substance": "air",
                "turbulenceModel": "laminar",
                "reynoldsNumber": 100,
                "gridResolution": 41,
                "dt": 0.005,
                "tolerance": "1e-06",
            }),
        ),
        (
            "Unstable Huge dt (Should get -5.0)",
            json.dumps({
                "archetype": "cavity",
                "substance": "water",
                "turbulenceModel": "laminar",
                "reynoldsNumber": 400,
                "gridResolution": 64,
                "dt": 0.5,
                "tolerance": "1e-06",
            }),
        ),
        ("Broken JSON (Should get -3.0)", "not valid json"),
    ]
    for label, text in samples:
        print(f"  [{label}] -> reward = {score_completion(text):+.2f}")
    pairs = build_sft_pairs(copies=2)
    bad = [p for p, t in pairs if score_completion(t) <= 0]
    print(f"  SFT targets: {len(pairs)} pairs, {len(bad)} with non-positive reward {sorted(set(bad))}")


def render_prompt(tok: Any, user: str) -> str:
    """Pre-render the chat template with thinking OFF so <think> never eats the completion budget."""
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user}]
    try:
        return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    except TypeError:  # templates without an enable_thinking switch (e.g. Qwen2.5)
        return tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)


def lora_config():
    from peft import LoraConfig

    return LoraConfig(
        r=16, lora_alpha=32, lora_dropout=0.05, bias="none", task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    )


def train_sft(model_id: str, output_dir: str) -> None:
    """Stage A: 2 epochs of QLoRA SFT so schema accuracy is high before any RL."""
    from datasets import Dataset
    from transformers import AutoTokenizer
    from trl import SFTConfig, SFTTrainer

    tok = AutoTokenizer.from_pretrained(model_id)
    data = Dataset.from_list([
        {"prompt": render_prompt(tok, p), "completion": t + (tok.eos_token or "")} for p, t in build_sft_pairs()
    ])
    trainer = SFTTrainer(
        model=model_id, train_dataset=data, peft_config=lora_config(),
        args=SFTConfig(output_dir=output_dir, num_train_epochs=2, per_device_train_batch_size=8,
                       learning_rate=2e-4, logging_steps=10, save_strategy="no", bf16=_bf16()),
    )
    trainer.train()
    trainer.save_model(output_dir)
    print(f"Saved SFT adapter to: {output_dir}")


def _bf16() -> bool:
    import torch

    return torch.cuda.is_available() and torch.cuda.is_bf16_supported()


def train_grpo(model_id: str, max_steps: int, output_dir: str, sft_adapter: str | None = None) -> None:
    import torch
    from datasets import Dataset
    from transformers import AutoModelForCausalLM, AutoTokenizer, TrainerCallback
    from trl import GRPOConfig, GRPOTrainer

    tok = AutoTokenizer.from_pretrained(model_id)
    dataset = Dataset.from_list([{"prompt": render_prompt(tok, p)} for p in SEED_PROMPTS * 20])

    class FailFast(TrainerCallback):
        """Zero learning signal when most completions are truncated (the Qwen3 <think> failure)."""

        def on_log(self, args, state, control, logs=None, **kw):
            if logs and state.global_step >= 10 and logs.get("completions/clipped_ratio", 0) > 0.2:
                print(f"[FailFast] clipped_ratio={logs['completions/clipped_ratio']:.2f} > 0.2 - stopping")
                control.should_training_stop = True

    model: Any = model_id
    peft_config = lora_config()
    if sft_adapter:  # resume from Stage-A adapter instead of a fresh LoRA
        from peft import PeftModel

        base = AutoModelForCausalLM.from_pretrained(model_id, dtype="auto")
        model = PeftModel.from_pretrained(base, sft_adapter, is_trainable=True)
        peft_config = None

    trainer = GRPOTrainer(
        model=model,
        reward_funcs=grpo_reward_fn,
        args=GRPOConfig(
            output_dir=output_dir, learning_rate=5e-6, per_device_train_batch_size=2,
            gradient_accumulation_steps=4, num_generations=4, max_completion_length=256,
            max_steps=max_steps, logging_steps=5, save_steps=100,
            bf16=_bf16(), fp16=torch.cuda.is_available() and not _bf16(),
        ),
        train_dataset=dataset,
        peft_config=peft_config,
        callbacks=[FailFast()],
    )
    trainer.train()
    trainer.save_model(output_dir)
    print(f"Saved RL-tuned Qwen model adapter to: {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Qwen3-0.6B with GRPO for OpenZess CFD.")
    parser.add_argument("--model", default="Qwen/Qwen3-0.6B", help="Base Hugging Face model ID")
    parser.add_argument("--steps", type=int, default=300, help="Total GRPO optimization steps")
    parser.add_argument("--output", default="./openzess_qwen3_0.6b_rl", help="Output adapter directory")
    parser.add_argument("--stage", choices=("sft", "grpo", "both"), default="both",
                        help="sft = schema warm-up, grpo = RL (optionally from --sft-adapter), both = SFT then GRPO")
    parser.add_argument("--sft-adapter", default=None, help="Existing SFT adapter dir to resume GRPO from")
    parser.add_argument("--dry-run", action="store_true", help="Test physics reward function without GPU")
    args = parser.parse_args()

    if args.dry_run:
        run_dry_run()
    else:
        sft_dir = args.sft_adapter or args.output + "_sft"
        if args.stage in ("sft", "both"):
            train_sft(args.model, sft_dir)
        if args.stage in ("grpo", "both"):
            train_grpo(args.model, args.steps, args.output, sft_dir if args.stage == "both" else args.sft_adapter)
