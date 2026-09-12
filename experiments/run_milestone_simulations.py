"""
Milestone 30% — Experimentation and Simulation Benchmark Suite
Project: UR2627GEN317 (OpenZess Platform)

Runs automated simulations:
1. Lid-Driven Cavity Validation against Ghia et al. (1982)
2. Grid Independence & Residual Convergence Study (21x21, 41x41, 61x61)
3. Instant PINN AI Surrogate vs Numerical CFD Comparison (Accuracy & Latency)
4. Exports publication-grade figures and metrics JSON to artifact directory.
"""

import sys
import os
import time
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Ensure parent directory is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from backend.mesh import Mesh2D
from backend.solver import AcceleratedSolver
from backend.ai_predictor import predict_pinn_flow
from experiments.ghia_benchmark import (
    GHIA_Y, GHIA_U_RE100, GHIA_U_RE400,
    GHIA_X, GHIA_V_RE100, GHIA_V_RE400
)

# Output directory for figures (relative to this file, portable across machines)
ARTIFACTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts")
FIG_DIR = os.path.join(ARTIFACTS_DIR, "figures")
os.makedirs(FIG_DIR, exist_ok=True)
RESULTS_FILE = os.path.join(ARTIFACTS_DIR, "simulation_results.json")


def run_cfd_simulation(nx=41, ny=41, Re=100.0, max_iter=600, tol=5e-4, dt=0.005):
    """Run fractional-step CFD simulation and record convergence."""
    mesh = Mesh2D(nx=nx, ny=ny)
    solver = AcceleratedSolver(mesh=mesh, Re=Re, lid_velocity=1.0)
    
    residuals = []
    t_start = time.perf_counter()
    
    for it in range(1, max_iter + 1):
        res = solver.step(dt=dt)
        residuals.append(float(res))
        if res < tol:
            break
            
    wall_time = time.perf_counter() - t_start
    return {
        "mesh": mesh,
        "solver": solver,
        "residuals": residuals,
        "iterations": len(residuals),
        "wall_time": wall_time,
        "converged": bool(residuals[-1] < tol)
    }


def main():
    print("=" * 70)
    print(" 🚀 RUNNING 30% MILESTONE EXPERIMENTS & BENCHMARKS (UR2627GEN317)")
    print("=" * 70)
    
    # -------------------------------------------------------------
    # Experiment 1: Validation Against Ghia et al. (1982) at Re=100
    # -------------------------------------------------------------
    print("\n[1/3] Running Validation Benchmark at Re = 100 (41x41)...")
    exp1 = run_cfd_simulation(nx=41, ny=41, Re=100.0, max_iter=500, tol=5e-4, dt=0.005)
    solver1 = exp1["solver"]
    mesh1 = exp1["mesh"]
    print(f"      -> Iterations: {exp1['iterations']} | Wall Time: {exp1['wall_time']:.2f}s | Final Residual: {exp1['residuals'][-1]:.2e}")
    
    # Centerline extractions
    mid_i = mesh1.nx // 2
    mid_j = mesh1.ny // 2
    u_center_cfd = solver1.u[mid_i, :]
    y_coords = mesh1.yc
    
    v_center_cfd = solver1.v[:, mid_j]
    x_coords = mesh1.xc
    
    # PINN Surrogate evaluation
    t_ai_start = time.perf_counter()
    u_pinn, v_pinn, p_pinn = predict_pinn_flow(mesh1, Re=100.0)
    ai_time = (time.perf_counter() - t_ai_start) * 1000.0  # ms
    u_center_pinn = u_pinn[mid_i, :]
    v_center_pinn = v_pinn[:, mid_j]
    print(f"      -> PINN AI Surrogate Inference Time: {ai_time:.2f} ms")
    
    # Interpolate CFD onto Ghia points to compute RMSE
    u_interp = np.interp(GHIA_Y, y_coords, u_center_cfd)
    rmse_u = np.sqrt(np.mean((u_interp - GHIA_U_RE100)**2))
    print(f"      -> Centerline u-velocity RMSE vs Ghia (1982): {rmse_u:.4f}")
    
    # Plot Figure 1: Ghia Validation
    plt.figure(figsize=(10, 4.5), dpi=300)
    plt.subplot(1, 2, 1)
    plt.plot(GHIA_U_RE100, GHIA_Y, 'ro', markersize=6, label='Ghia et al. (1982)')
    plt.plot(u_center_cfd, y_coords, 'b-', linewidth=2, label='OpenZess Numerical CFD')
    plt.plot(u_center_pinn, y_coords, 'g--', linewidth=1.5, label='OpenZess PINN Surrogate')
    plt.xlabel('u-velocity ($u / U_{lid}$)', fontsize=10)
    plt.ylabel('Normalized Height ($y / L$)', fontsize=10)
    plt.title('Vertical Centerline ($x = 0.5$, Re=100)', fontsize=11, fontweight='bold')
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(frameon=True, facecolor='white', framealpha=0.9)
    
    plt.subplot(1, 2, 2)
    plt.plot(GHIA_X, GHIA_V_RE100, 'ro', markersize=6, label='Ghia et al. (1982)')
    plt.plot(x_coords, v_center_cfd, 'b-', linewidth=2, label='OpenZess Numerical CFD')
    plt.plot(x_coords, v_center_pinn, 'g--', linewidth=1.5, label='OpenZess PINN Surrogate')
    plt.xlabel('Normalized Width ($x / L$)', fontsize=10)
    plt.ylabel('v-velocity ($v / U_{lid}$)', fontsize=10)
    plt.title('Horizontal Centerline ($y = 0.5$, Re=100)', fontsize=11, fontweight='bold')
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(frameon=True, facecolor='white', framealpha=0.9)
    
    plt.tight_layout()
    fig1_path = os.path.join(FIG_DIR, "fig1_ghia_validation.png")
    plt.savefig(fig1_path)
    plt.close()
    print(f"      -> Saved: {fig1_path}")
    
    # -------------------------------------------------------------
    # Experiment 2: Grid Independence & Residual Convergence Study
    # -------------------------------------------------------------
    print("\n[2/3] Running Grid Independence Study (21x21, 41x41, 61x61)...")
    grid_tests = [21, 41, 61]
    grid_results = {}
    
    plt.figure(figsize=(7, 4.5), dpi=300)
    for n in grid_tests:
        print(f"      -> Solving on {n}x{n} grid...")
        out = run_cfd_simulation(nx=n, ny=n, Re=100.0, max_iter=300, tol=5e-4, dt=0.005)
        grid_results[f"{n}x{n}"] = {
            "iterations": out["iterations"],
            "wall_time": out["wall_time"],
            "final_res": out["residuals"][-1]
        }
        plt.semilogy(out["residuals"], label=f'{n}x{n} Grid (Time: {out["wall_time"]:.2f}s)')
        
    plt.xlabel('Iteration Number', fontsize=10)
    plt.ylabel('Max Residual ($L_\\infty$ norm)', fontsize=10)
    plt.title('Logarithmic Residual Convergence vs. Grid Resolution', fontsize=11, fontweight='bold')
    plt.grid(True, which='both', linestyle=':', alpha=0.6)
    plt.legend(frameon=True, facecolor='white', framealpha=0.9)
    plt.tight_layout()
    fig2_path = os.path.join(FIG_DIR, "fig2_residual_convergence.png")
    plt.savefig(fig2_path)
    plt.close()
    print(f"      -> Saved: {fig2_path}")
    
    # -------------------------------------------------------------
    # Experiment 3: CFD vs PINN Surrogate Flowfield & Error Map
    # -------------------------------------------------------------
    print("\n[3/3] Generating CFD vs PINN Contour & Absolute Error Field...")
    speed_cfd = np.sqrt(solver1.u**2 + solver1.v**2).T
    speed_pinn = np.sqrt(u_pinn**2 + v_pinn**2).T
    abs_diff = np.abs(speed_cfd - speed_pinn)
    
    mae = np.mean(abs_diff)
    max_err = np.max(abs_diff)
    print(f"      -> Mean Absolute Error (MAE): {mae:.4f} | Max Error: {max_err:.4f}")
    
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.8), dpi=300)
    im0 = axes[0].contourf(mesh1.X.T, mesh1.Y.T, speed_cfd, levels=25, cmap='turbo')
    axes[0].set_title('Numerical CFD Field |U|', fontsize=10, fontweight='bold')
    axes[0].set_aspect('equal')
    plt.colorbar(im0, ax=axes[0], fraction=0.046, pad=0.04)
    
    im1 = axes[1].contourf(mesh1.X.T, mesh1.Y.T, speed_pinn, levels=25, cmap='turbo')
    axes[1].set_title('AI PINN Surrogate Field |U|', fontsize=10, fontweight='bold')
    axes[1].set_aspect('equal')
    plt.colorbar(im1, ax=axes[1], fraction=0.046, pad=0.04)
    
    im2 = axes[2].contourf(mesh1.X.T, mesh1.Y.T, abs_diff, levels=25, cmap='inferno')
    axes[2].set_title(f'Absolute Difference Map (MAE: {mae:.3f})', fontsize=10, fontweight='bold')
    axes[2].set_aspect('equal')
    plt.colorbar(im2, ax=axes[2], fraction=0.046, pad=0.04)
    
    plt.tight_layout()
    fig3_path = os.path.join(FIG_DIR, "fig3_cfd_vs_pinn_contours.png")
    plt.savefig(fig3_path)
    plt.close()
    print(f"      -> Saved: {fig3_path}")
    
    # -------------------------------------------------------------
    # Performance Speedup Bar Chart
    # -------------------------------------------------------------
    cfd_sec = exp1["wall_time"]
    ai_sec = ai_time / 1000.0
    speedup = cfd_sec / max(ai_sec, 1e-6)
    
    plt.figure(figsize=(6, 4), dpi=300)
    categories = ['Numerical CFD\n(SciPy Sparse)', 'AI PINN Surrogate\n(Instant Inference)']
    times = [cfd_sec, ai_sec]
    colors = ['#1967d2', '#34a853']
    bars = plt.bar(categories, times, color=colors, width=0.5)
    plt.yscale('log')
    plt.ylabel('Execution Time (seconds, log-scale)', fontsize=10)
    plt.title(f'Computational Latency & Speedup ({speedup:.1f}x Faster)', fontsize=11, fontweight='bold')
    for bar, t_val in zip(bars, times):
        plt.text(bar.get_x() + bar.get_width()/2.0, t_val * 1.3, f"{t_val:.4f} s", ha='center', fontweight='bold')
    plt.grid(True, axis='y', linestyle=':', alpha=0.6)
    plt.tight_layout()
    fig4_path = os.path.join(FIG_DIR, "fig4_computational_latency.png")
    plt.savefig(fig4_path)
    plt.close()
    print(f"      -> Saved: {fig4_path}")
    
    # Save structured results
    results = {
        "project": "UR2627GEN317",
        "milestone": "30% Experimentation & Simulation",
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "validation_benchmark": {
            "test_case": "2D Lid-Driven Cavity",
            "Re": 100.0,
            "cfd_grid": "41x41",
            "iterations": exp1["iterations"],
            "wall_time_seconds": exp1["wall_time"],
            "rmse_vs_ghia_1982": float(rmse_u),
            "pinn_inference_ms": float(ai_time),
            "speedup_factor": float(speedup)
        },
        "grid_independence": grid_results,
        "error_metrics": {
            "mae": float(mae),
            "max_error": float(max_err)
        }
    }
    
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)
        
    print(f"\n✅ All simulation experiments completed successfully!")
    print(f"   Results data written to: {RESULTS_FILE}")
    print(f"   Figures generated in: {FIG_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()