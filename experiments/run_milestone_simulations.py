"""
Milestone experiments — validation and benchmark suite (UR2627GEN317).

1. Lid-driven cavity at Re = 100 vs Ghia, Ghia & Shin (1982): centreline
   u(y) and v(x) of the *converged steady state*.
2. Grid convergence: the same comparison on 21^2, 41^2, 61^2 grids, with the
   observed order of accuracy.
3. The "ai" mode's cavity preview — the Stokes (Re -> 0) solution from one
   sparse biharmonic solve, not a trained model — vs the CFD solution:
   error map and latency.

Usage:
    python experiments/run_milestone_simulations.py [output_dir]

Figures and results JSON go to experiments/output/ by default.
"""

import json
import os
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.ai_predictor import predict_cavity_stokes  # noqa: E402
from backend.mesh import Mesh2D  # noqa: E402
from backend.solver import AcceleratedSolver, CasePhysics  # noqa: E402
from experiments.ghia_benchmark import (  # noqa: E402
    GHIA_U_RE100, GHIA_V_RE100, GHIA_X, GHIA_Y,
)

STEADY_TOL = 1e-6  # max |du| per step; Ghia's data is a steady solution
MAX_STEPS = 50_000


def run_cavity(n: int, Re: float = 100.0, dt: float = 0.005) -> dict:
    """March the cavity to steady state and return the solver + history."""
    mesh = Mesh2D(nx=n, ny=n)
    solver = AcceleratedSolver(
        mesh, CasePhysics(reynolds=Re, inlet_velocity=1.0), archetype="cavity"
    )
    residuals = []
    t0 = time.perf_counter()
    for _ in range(MAX_STEPS):
        residuals.append(float(solver.step(dt)))
        if residuals[-1] < STEADY_TOL or solver.diverged:
            break
    return {
        "mesh": mesh,
        "solver": solver,
        "residuals": residuals,
        "wall_time": time.perf_counter() - t0,
        "converged": residuals[-1] < STEADY_TOL and not solver.diverged,
    }


def centrelines(mesh: Mesh2D, u: np.ndarray, v: np.ndarray):
    """u(y) on x = 0.5 and v(x) on y = 0.5, wall values included."""
    u_c = np.array([np.interp(0.5, mesh.xc, u[:, j]) for j in range(mesh.ny)])
    v_c = np.array([np.interp(0.5, mesh.yc, v[i, :]) for i in range(mesh.nx)])
    y = np.r_[0.0, mesh.yc, 1.0]
    x = np.r_[0.0, mesh.xc, 1.0]
    return y, np.r_[0.0, u_c, 1.0], x, np.r_[0.0, v_c, 0.0]


def ghia_rmse(mesh, u, v):
    y, u_c, x, v_c = centrelines(mesh, u, v)
    rmse_u = float(np.sqrt(np.mean((np.interp(GHIA_Y, y, u_c) - GHIA_U_RE100) ** 2)))
    rmse_v = float(np.sqrt(np.mean((np.interp(GHIA_X, x, v_c) - GHIA_V_RE100) ** 2)))
    return rmse_u, rmse_v


def main(out_dir: str) -> None:
    fig_dir = os.path.join(out_dir, "figures")
    os.makedirs(fig_dir, exist_ok=True)
    print("=" * 70)
    print(" Milestone experiments (UR2627GEN317)")
    print("=" * 70)

    # 1. Validation at Re = 100, 41 x 41
    print("\n[1/3] Lid-driven cavity, Re = 100, 41x41, marching to steady state...")
    exp1 = run_cavity(41)
    s1, m1 = exp1["solver"], exp1["mesh"]
    rmse_u, rmse_v = ghia_rmse(m1, s1.u, s1.v)
    print(f"      steps={len(exp1['residuals'])} converged={exp1['converged']} "
          f"wall={exp1['wall_time']:.2f}s")
    print(f"      RMSE vs Ghia (1982): u = {rmse_u:.4f}, v = {rmse_v:.4f}")

    t0 = time.perf_counter()
    u_a, v_a, p_a = predict_cavity_stokes(m1, lid_velocity=1.0, nu=0.01)
    analytic_ms = (time.perf_counter() - t0) * 1000.0
    rmse_u_a, rmse_v_a = ghia_rmse(m1, u_a, v_a)
    print(f"      Stokes (Re->0) approximation: {analytic_ms:.2f} ms, "
          f"RMSE u = {rmse_u_a:.4f}, v = {rmse_v_a:.4f}")

    y, u_c, x, v_c = centrelines(m1, s1.u, s1.v)
    ya, u_ca, xa, v_ca = centrelines(m1, u_a, v_a)
    plt.figure(figsize=(10, 4.5), dpi=200)
    plt.subplot(1, 2, 1)
    plt.plot(GHIA_U_RE100, GHIA_Y, "ro", label="Ghia et al. (1982)")
    plt.plot(u_c, y, "b-", lw=2, label="OpenZess CFD (41x41)")
    plt.plot(u_ca, ya, "g--", lw=1.5, label="Stokes (Re$\\to$0) solution")
    plt.xlabel("$u / U_{lid}$"); plt.ylabel("$y / L$")
    plt.title("Vertical centreline ($x = 0.5$, Re = 100)")
    plt.grid(True, ls=":", alpha=0.6); plt.legend()
    plt.subplot(1, 2, 2)
    plt.plot(GHIA_X, GHIA_V_RE100, "ro", label="Ghia et al. (1982)")
    plt.plot(x, v_c, "b-", lw=2, label="OpenZess CFD (41x41)")
    plt.plot(xa, v_ca, "g--", lw=1.5, label="Closed-form approximation")
    plt.xlabel("$x / L$"); plt.ylabel("$v / U_{lid}$")
    plt.title("Horizontal centreline ($y = 0.5$, Re = 100)")
    plt.grid(True, ls=":", alpha=0.6); plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "fig1_ghia_validation.png"))
    plt.close()

    # 2. Grid convergence against the benchmark
    print("\n[2/3] Grid convergence (21x21, 41x41, 61x61)...")
    grids = [21, 41, 61]
    grid_results = {}
    plt.figure(figsize=(7, 4.5), dpi=200)
    for n in grids:
        out = exp1 if n == 41 else run_cavity(n)
        ru, rv = ghia_rmse(out["mesh"], out["solver"].u, out["solver"].v)
        grid_results[f"{n}x{n}"] = {
            "h": 1.0 / n,
            "rmse_u_vs_ghia": ru,
            "rmse_v_vs_ghia": rv,
            "steps": len(out["residuals"]),
            "wall_time_s": out["wall_time"],
            "converged": out["converged"],
        }
        print(f"      {n}x{n}: RMSE u = {ru:.4f}, v = {rv:.4f}, "
              f"{len(out['residuals'])} steps, {out['wall_time']:.2f}s")
        plt.semilogy(out["residuals"], label=f"{n}x{n}")
    plt.xlabel("Time step"); plt.ylabel("max |du| per step")
    plt.title("Transient decay to steady state")
    plt.grid(True, which="both", ls=":", alpha=0.6); plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "fig2_residual_convergence.png"))
    plt.close()

    # Observed order p from the two finest grids: e ~ C h^p
    e = [grid_results[f"{n}x{n}"]["rmse_u_vs_ghia"] for n in grids]
    h = [1.0 / n for n in grids]
    order = float(np.log(e[1] / e[2]) / np.log(h[1] / h[2]))
    print(f"      observed order of accuracy (u, 41->61): {order:.2f} "
          "(first-order upwind advection => ~1 expected)")

    # 3. Closed-form approximation vs CFD
    print("\n[3/3] Stokes approximation vs CFD error map...")
    speed_cfd = np.sqrt(s1.u**2 + s1.v**2).T
    speed_ana = np.sqrt(u_a**2 + v_a**2).T
    abs_diff = np.abs(speed_cfd - speed_ana)
    mae, max_err = float(np.mean(abs_diff)), float(np.max(abs_diff))
    print(f"      speed MAE = {mae:.4f}, max error = {max_err:.4f}")

    fig, axes = plt.subplots(1, 3, figsize=(13, 3.8), dpi=200)
    for ax, field, title, cmap in (
        (axes[0], speed_cfd, "CFD |U|", "turbo"),
        (axes[1], speed_ana, "Stokes (Re->0) |U|", "turbo"),
        (axes[2], abs_diff, f"|difference| (MAE {mae:.3f})", "inferno"),
    ):
        im = ax.contourf(m1.X.T, m1.Y.T, field, levels=25, cmap=cmap)
        ax.set_title(title, fontsize=10); ax.set_aspect("equal")
        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "fig3_cfd_vs_stokes.png"))
    plt.close()

    plt.figure(figsize=(6, 4), dpi=200)
    times = [exp1["wall_time"], analytic_ms / 1000.0]
    bars = plt.bar(["Navier-Stokes CFD\n(41x41, steady)", "Stokes solve\n(one sparse LU)"],
                   times, color=["#1967d2", "#9aa0a6"], width=0.5)
    plt.yscale("log"); plt.ylabel("Wall time [s] (log)")
    plt.title(f"Latency (Stokes vs CFD speed MAE {mae:.3f})")
    for bar, t in zip(bars, times):
        plt.text(bar.get_x() + bar.get_width() / 2, t * 1.3, f"{t:.4f} s", ha="center")
    plt.grid(True, axis="y", ls=":", alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(fig_dir, "fig4_computational_latency.png"))
    plt.close()

    results = {
        "project": "UR2627GEN317",
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "validation_benchmark": {
            "test_case": "2D lid-driven cavity",
            "Re": 100.0,
            "grid": "41x41",
            "steady_tolerance": STEADY_TOL,
            "steps": len(exp1["residuals"]),
            "converged": exp1["converged"],
            "wall_time_seconds": exp1["wall_time"],
            "rmse_u_vs_ghia_1982": rmse_u,
            "rmse_v_vs_ghia_1982": rmse_v,
        },
        "grid_convergence": grid_results,
        "observed_order_u": order,
        "stokes_approximation": {
            "note": "Re -> 0 biharmonic streamfunction solve, not a trained model",
            "latency_ms": analytic_ms,
            "rmse_u_vs_ghia_1982": rmse_u_a,
            "rmse_v_vs_ghia_1982": rmse_v_a,
            "speed_mae_vs_cfd": mae,
            "speed_max_error_vs_cfd": max_err,
        },
    }
    with open(os.path.join(out_dir, "simulation_results.json"), "w") as fh:
        json.dump(results, fh, indent=2)
    print(f"\nResults: {os.path.join(out_dir, 'simulation_results.json')}")
    print(f"Figures: {fig_dir}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "experiments", "output"))
