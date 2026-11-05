"""Physics regression tests for backend/solver.py.

Several of these pin down bugs that previously shipped:
  * open-flow pressure solve was ill-posed (p ~ 260, |div u| ~ 255 at U = 1)
  * venturi force evaluation raised IndexError
  * Cd and Cl had flipped signs (negative drag was hidden by a clamp)
  * positive angle of attack rotated the airfoil nose-DOWN
  * the temperature slider had no effect (Celsius sent as Kelvin, 10 K floor)
"""

import numpy as np
import pytest

from backend.mesh import Mesh2D
from backend.solver import (
    ARCHETYPES,
    CLOSED_ARCHETYPES,
    AcceleratedSolver,
    CasePhysics,
    build_obstacle_mask,
    parse_dict_overrides,
)
from experiments.ghia_benchmark import (
    GHIA_U_RE100,
    GHIA_V_RE100,
    GHIA_V_RE400,
    GHIA_X,
    GHIA_Y,
)
from experiments.run_milestone_simulations import ghia_rmse

WIDE = ("cylinder", "obstacle", "airfoil")  # 2:1 channel, as in app.py


def make(arch, n=41, aoa_deg=0.0, **physics):
    lx = 2.0 if arch in WIDE else 1.0
    mesh = Mesh2D(2 * n if arch in WIDE else n, n, lx, 1.0)
    spec = {"shape": "circle", "cx": 0.4, "cy": 0.5, "size": 0.1} if arch == "cad" else None
    phys = dict(reynolds=100, hot_temp=358.15, gravity=[0, -9.81, 0])
    phys.update(physics)
    return AcceleratedSolver(mesh, CasePhysics(**phys), arch, aoa_deg=aoa_deg, obstacle_spec=spec)


def march(solver, steps, tol=1e-5):
    res = np.inf
    for _ in range(steps):
        res = solver.step(0.005)
        if solver.diverged or res < tol:
            break
    return res


@pytest.mark.parametrize("arch", ARCHETYPES)
def test_every_archetype_stays_bounded_and_incompressible(arch):
    s = make(arch)
    march(s, 300)
    U = s.lid_velocity
    speed = np.sqrt(s.u**2 + s.v**2)
    assert not s.diverged
    assert np.isfinite(speed).all() and np.isfinite(s.p).all()
    assert speed.max() < 4 * U            # used to sit at the 10x safety clamp
    assert np.abs(s.p).max() < 10 * U**2  # used to reach ~260 at the pinned corner
    assert s.continuity_error < 5e-3
    cd, cl, extra = s.compute_forces()    # venturi used to raise IndexError
    assert np.isfinite([cd, cl]).all()
    assert all(np.isfinite(v) for v in extra.values())


def test_open_flow_pressure_has_dirichlet_outlet():
    s = make("cylinder")
    pinned = s._pinned.reshape(s.mesh.nx, s.mesh.ny)
    assert pinned[-1].all() and pinned.sum() == s.mesh.ny


@pytest.mark.parametrize("arch", sorted(CLOSED_ARCHETYPES))
def test_closed_box_pins_one_gauge_cell(arch):
    assert make(arch)._pinned.sum() == 1


def test_cavity_matches_ghia_re100():
    s = make("cavity")
    march(s, 20_000, tol=1e-6)
    rmse_u, rmse_v = ghia_rmse(s.mesh, s.u, s.v)
    assert rmse_u < 0.045 and rmse_v < 0.03


def test_positive_aoa_is_nose_up():
    m = Mesh2D(400, 200, 2.0, 1.0)
    mask = build_obstacle_mask(m, "airfoil", 10.0)
    xs, ys = m.X[mask], m.Y[mask]
    assert ys[np.argmin(xs)] > ys[np.argmax(xs)] + 0.05  # leading edge raised


def test_airfoil_lift_follows_aoa_and_is_antisymmetric():
    up, down = make("airfoil", aoa_deg=8.0), make("airfoil", aoa_deg=-8.0)
    march(up, 3000)
    march(down, 3000)
    cd_up, cl_up, _ = up.compute_forces()
    cd_down, cl_down, _ = down.compute_forces()
    assert cl_up > 0.3 and cl_down < -0.3
    assert cl_up == pytest.approx(-cl_down, rel=0.05)
    assert cd_up > 0 and cd_up == pytest.approx(cd_down, rel=0.05)


def test_cylinder_has_drag_and_no_lift():
    s = make("cylinder")
    march(s, 3000)
    cd, cl, _ = s.compute_forces()
    assert 1.0 < cd < 6.0
    assert abs(cl) < 0.05


def test_f1_wing_nose_down_makes_downforce():
    s = make("f1", aoa_deg=-6.9)
    march(s, 3000)
    _, cl, extra = s.compute_forces()
    assert cl < 0 and extra["downforce"] > 0


def test_venturi_pressure_drops_into_throat():
    s = make("venturi")
    march(s, 3000)
    _, _, extra = s.compute_forces()
    assert extra["pressureDrop"] > 0


def test_divergence_is_flagged_not_hidden():
    s = make("cavity")
    s.u[5, 5] = np.nan
    s.step(0.005)
    assert s.diverged


def test_temperature_difference_is_signed_kelvin():
    assert CasePhysics(ambient_temp=293.15, hot_temp=358.15).delta_t_ref == pytest.approx(65.0)
    assert CasePhysics(ambient_temp=293.15, hot_temp=283.15).delta_t_ref == pytest.approx(-10.0)


@pytest.mark.parametrize("hot_temp, sign", [(358.15, +1), (228.15, -1)])
def test_hot_fluid_rises_cold_fluid_sinks(hot_temp, sign):
    s = make("plume", inlet_velocity=0.2, hot_temp=hot_temp)
    march(s, 600)
    weighted_v = (s.v * s.s).sum() / s.s.sum()
    assert sign * weighted_v > 0.01


def test_dict_overrides():
    parsed = parse_dict_overrides({
        "controlDict": {"name": "controlDict", "content": "deltaT 0.002;\nendTime 10;"},
        "transportProperties": {"content": "nu [0 2 -1 0 0 0 0] 1.5e-05;"},
    })
    assert parsed == {"dt": 0.002, "nu": 1.5e-05}
    assert parse_dict_overrides({"deltaT": "0.01", "bogus": 3}) == {"dt": 0.01}
    assert parse_dict_overrides(None) == {}


def test_ghia_tables_are_the_published_values():
    # Entries a previous version had altered (Table II, Re = 400)
    assert GHIA_V_RE400[GHIA_X == 0.1563][0] == pytest.approx(0.28124)
    assert GHIA_V_RE400[GHIA_X == 0.0625][0] == pytest.approx(0.18360)
    assert GHIA_V_RE400[GHIA_X == 0.9063][0] == pytest.approx(-0.23827)
    assert len(GHIA_Y) == len(GHIA_U_RE100) == len(GHIA_X) == len(GHIA_V_RE100) == 17
