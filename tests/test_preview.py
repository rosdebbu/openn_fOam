"""Tests for the instant "ai" preview (potential flow + Stokes cavity).

The preview used to be a hand-written vortex formula labelled a "PINN":
it returned the same lid-driven-cavity vortex for every geometry, and that
vortex spun the wrong way (RMSE 0.65 vs Ghia, worse than an all-zero field).
"""

import numpy as np
import pytest

from backend.ai_predictor import predict_cavity_stokes, predict_potential_flow
from backend.mesh import Mesh2D
from backend.solver import AcceleratedSolver, CasePhysics, build_obstacle_mask
from experiments.run_milestone_simulations import ghia_rmse


def test_empty_channel_is_exact_uniform_stream():
    m = Mesh2D(82, 41, 2.0, 1.0)
    u, v, p = predict_potential_flow(m, np.zeros((82, 41), bool), U=0.7)
    assert np.allclose(u, 0.7) and np.allclose(v, 0.0) and np.allclose(p, 0.0)


def test_cylinder_peak_speed_matches_potential_theory():
    # Unconfined theory: |u|max = 2U, Cp_min = -3 (small blockage here)
    m = Mesh2D(300, 300, 4.0, 4.0)
    mask = (m.X - 1.5) ** 2 + (m.Y - 2.0) ** 2 <= 0.15**2
    u, v, p = predict_potential_flow(m, mask, U=1.0)
    assert np.sqrt(u**2 + v**2).max() == pytest.approx(2.0, rel=0.05)
    assert p.min() / 0.5 == pytest.approx(-3.0, rel=0.08)


def test_venturi_conserves_mass_and_speeds_up_at_throat():
    m = Mesh2D(120, 120, 1.0, 1.0)
    mask = build_obstacle_mask(m, "venturi")
    u, _, _ = predict_potential_flow(m, mask, U=1.0)
    fluxes = [u[i, ~mask[i]].sum() * m.dy for i in range(0, 120, 10)]
    assert np.ptp(fluxes) < 1e-6 * max(fluxes)
    i_th = np.argmin(np.abs(m.xc - 0.5))
    expected = (~mask[0]).sum() / (~mask[i_th]).sum()  # 1-D continuity
    assert u[i_th, ~mask[i_th]].mean() == pytest.approx(expected, rel=1e-6)


def test_potential_flow_has_no_drag():
    # d'Alembert's paradox: an inviscid, attached flow exerts no drag
    m = Mesh2D(82, 41, 2.0, 1.0)
    s = AcceleratedSolver(m, CasePhysics(reynolds=100), "cylinder")
    s.u, s.v, s.p = predict_potential_flow(m, s.obstacle_mask, s.lid_velocity)
    cd, cl, _ = s.compute_forces(include_viscous=False)
    assert abs(cd) < 0.05 and abs(cl) < 0.05


def test_stokes_cavity_matches_ghia_re100_and_spins_clockwise():
    m = Mesh2D(41, 41)
    u, v, _ = predict_cavity_stokes(m, lid_velocity=1.0, nu=0.01)
    rmse_u, rmse_v = ghia_rmse(m, u, v)
    assert rmse_u < 0.035 and rmse_v < 0.035
    assert u[20, 33] > 0 and u[20, 8] < 0  # lid-driven: clockwise vortex
    assert u[20].min() == pytest.approx(-0.207, abs=0.01)  # Stokes u_min


def test_stokes_pressure_is_antisymmetric():
    m = Mesh2D(41, 41)
    _, _, p = predict_cavity_stokes(m, 1.0, 0.01)
    assert np.abs(p + p[::-1, :]).max() < 1e-9 * np.abs(p).max()
    assert p[-3, -3] > 0 > p[2, -3]  # high downstream corner, low upstream


def test_stokes_rejects_non_square_grid():
    with pytest.raises(ValueError):
        predict_cavity_stokes(Mesh2D(40, 20, 2.0, 1.0))
