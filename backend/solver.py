"""
OpenZess Solver Engine — 2-D incompressible Navier-Stokes (projection method)
The pressure Poisson matrix is LU-factorized once (SciPy SuperLU) and reused
every time step.

Fractional-step incompressible Navier-Stokes on a uniform collocated grid:
  * explicit predictor: first-order upwind advection, central diffusion
  * approximate projection: Neumann walls, Dirichlet p = 0 outlet for open
    channels, compatible RHS + gauge cell for sealed boxes
  * substance-aware SI physics via `CasePhysics` (nu, rho, beta, gravity, temps)
  * Boussinesq thermal buoyancy + passive heavy-fluid (dam-break) transport
  * automatic CFL + diffusion limited timestep; divergence is detected and
    reported instead of being clipped away
  * Cd/Cl integrated from the computed pressure and wall shear
  * staircase immersed boundaries for every archetype (venturi, airfoil,
    custom CAD primitives, ...)

Accuracy: first-order in space (upwind), validated against Ghia et al.
(1982) — see experiments/run_milestone_simulations.py and tests/.
"""

import re

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

from .mesh import Mesh2D

# ---------------------------------------------------------------------------
# Fluid substance database (SI units) — mirrors frontend/src/types/cfd.ts
# ---------------------------------------------------------------------------
FLUID_DATABASE = {
    "air":      {"rho": 1.225,  "nu": 1.5e-5,   "cp": 1005.0, "beta": 0.0034},
    "water":    {"rho": 998.0,  "nu": 1.0e-6,   "cp": 4182.0, "beta": 0.00021},
    "seawater": {"rho": 1025.0, "nu": 1.05e-6,  "cp": 3993.0, "beta": 0.00024},
    "co2":      {"rho": 1.980,  "nu": 8.3e-6,   "cp": 844.0,  "beta": 0.0037},
    "oil":      {"rho": 890.0,  "nu": 4.5e-5,   "cp": 1900.0, "beta": 0.0007},
    "ethanol":  {"rho": 789.0,  "nu": 1.52e-6,  "cp": 2440.0, "beta": 0.0011},
}

# Every scenario archetype the platform understands (mirrors frontend types)
ARCHETYPES = (
    "airfoil", "cylinder", "venturi", "f1", "drone", "submarine",
    "plume", "cavity", "water_dam", "weather_plume", "obstacle", "cad",
)

# Flows partly driven by gravity / buoyancy
BUOYANT_ARCHETYPES = frozenset({"plume", "weather_plume", "water_dam"})

# Sealed boxes (no inflow/outflow): pressure is Neumann on every wall, so it is
# only defined up to a constant and the Poisson RHS must be made compatible.
# Every other archetype is an inlet(left) -> outlet(right) channel/tunnel with a
# Dirichlet p = 0 outlet, which is what makes the open-flow projection well posed.
CLOSED_ARCHETYPES = frozenset({"cavity", "water_dam"})

# Bodies whose force coefficients are conventionally referenced to the chord
# (x-extent); bluff bodies use the frontal height (y-extent) instead.
CHORD_REFERENCED_ARCHETYPES = frozenset({"airfoil", "f1"})


class CasePhysics:
    """Normalized physical case configuration.

    Bridges what the user selects in the UI (substance, inlet velocity,
    gravity, temperatures) into solver quantities. The Reynolds number is
    derived from real SI viscosity, so switching water <-> air actually
    changes the physics, and real-world equivalents stay reportable.
    """

    def __init__(
        self,
        substance: str = "air",
        inlet_velocity: float = 1.0,
        reynolds=None,
        gravity=None,
        ambient_temp: float = 293.15,
        hot_temp=None,
        characteristic_length=None,
        nu=None,
        rho=None,
        beta=None,
    ):
        key = str(substance or "air").lower()
        fluid = FLUID_DATABASE.get(key, FLUID_DATABASE["air"])
        self.substance = key if key in FLUID_DATABASE else "air"
        self.rho = float(rho) if rho is not None else fluid["rho"]
        self.beta = float(beta) if beta is not None else fluid["beta"]
        self.gravity = (
            np.asarray(gravity, dtype=float).reshape(3)
            if gravity is not None else np.zeros(3)
        )
        self.ambient_temp = float(ambient_temp)
        self.hot_temp = (
            float(hot_temp) if hot_temp is not None else self.ambient_temp + 80.0
        )

        if nu is not None:
            # Explicit viscosity override wins
            self.nu = max(float(nu), 1e-9)
        elif reynolds is not None and float(reynolds) > 0:
            # UI Reynolds slider: classic nondimensional mapping nu = U*L/Re
            L = float(characteristic_length) if characteristic_length else 1.0
            self.nu = max(float(inlet_velocity) * L / float(reynolds), 1e-9)
        else:
            # Pure substance physics: real SI kinematic viscosity
            self.nu = fluid["nu"]

        self.inlet_velocity = max(float(inlet_velocity), 1e-3)
        self.characteristic_length = (
            float(characteristic_length) if characteristic_length else None
        )

    # -- derived quantities --------------------------------------------------
    @property
    def reynolds_real(self) -> float:
        """Reynolds number from the actual march viscosity (U*L/nu)."""
        L = self.characteristic_length if self.characteristic_length else 1.0
        return self.inlet_velocity * L / self.nu

    @property
    def g_mag(self) -> float:
        return float(np.linalg.norm(self.gravity))

    @property
    def buoyancy_active(self) -> bool:
        return self.g_mag > 1e-6 and self.beta > 0.0

    @property
    def delta_t_ref(self) -> float:
        """Signed temperature difference (K) driving the plume.

        Both temperatures are Kelvin. A negative value is a cold, sinking
        plume — no artificial floor (a former max(.., 10 K) floor silently
        masked a frontend that sent Celsius).
        """
        return self.hot_temp - self.ambient_temp

    def to_dict(self) -> dict:
        return {
            "substance": self.substance,
            "inletVelocity": float(np.round(self.inlet_velocity, 4)),
            "nu": self.nu,
            "rho": self.rho,
            "beta": self.beta,
            "reynoldsReal": float(np.round(self.reynolds_real, 1)),
            "gravity": self.gravity.tolist(),
            "ambientTemp": self.ambient_temp,
            "hotTemp": self.hot_temp,
        }


def _naca_symmetric_mask(X, Y, xc, yc, chord, aoa_deg, thickness):
    """Solid mask of a symmetric NACA 00xx section.

    (xc, yc) is the mid-chord point. Positive `aoa_deg` is nose-UP relative
    to the +x freestream (leading edge raised), the standard aerodynamic
    convention. World -> body coordinates rotate by +aoa, which is the same
    as the body being rotated clockwise by aoa.
    """
    a = np.radians(aoa_deg)
    dx_c, dy_c = X - xc, Y - yc
    x_rot = dx_c * np.cos(a) - dy_c * np.sin(a) + 0.5 * chord
    y_rot = dx_c * np.sin(a) + dy_c * np.cos(a)
    xn = np.clip(x_rot / chord, 0.0, 1.0)
    yt = 5.0 * thickness * chord * (
        0.2969 * np.sqrt(xn) - 0.1260 * xn - 0.3516 * xn**2
        + 0.2843 * xn**3 - 0.1015 * xn**4
    )
    return (x_rot >= 0.0) & (x_rot <= chord) & (np.abs(y_rot) <= yt)


def build_obstacle_mask(
    mesh: Mesh2D,
    archetype: str = "cavity",
    aoa_deg: float = 0.0,
    obstacle_spec: dict | None = None,
) -> np.ndarray:
    """Construct the discrete solid-body mask for ANY supported archetype.

    `obstacle_spec` enables fully custom geometry straight from the UI:
        {"shape": "circle"|"square"|"rectangle"|"airfoil",
         "cx": 0..1, "cy": 0..1, "size": 0..1, "aoa": degrees}
    This is the pathway that lets users build their OWN simulations.
    """
    arch = str(archetype or "cavity").lower()
    nx, ny = mesh.nx, mesh.ny
    X, Y = mesh.X, mesh.Y
    lx, ly = mesh.lx, mesh.ly
    mask = np.zeros((nx, ny), dtype=bool)

    if arch == "airfoil":
        # NACA 0012 at mid-chord (0.30 lx, 0.50 ly)
        mask = _naca_symmetric_mask(X, Y, 0.30 * lx, 0.50 * ly, 0.45 * lx, aoa_deg, 0.12)

    elif arch == "f1":
        # Ground-effect front-wing section near the floor (NACA 0011). A
        # negative AoA (nose down) produces downforce.
        mask = _naca_symmetric_mask(X, Y, 0.35 * lx, 0.22 * ly, 0.50 * lx, aoa_deg, 0.11)

    elif arch == "drone":
        y_rotor = 0.55 * ly
        r_arm = 0.18 * lx
        rotor1 = (np.abs(X - 0.35 * lx) <= r_arm) & (np.abs(Y - y_rotor) <= 0.03 * ly)
        rotor2 = (np.abs(X - 0.65 * lx) <= r_arm) & (np.abs(Y - y_rotor) <= 0.03 * ly)
        center_pod = (
            (X - 0.50 * lx) ** 2 / (0.08 * lx) ** 2
            + (Y - (y_rotor - 0.05 * ly)) ** 2 / (0.06 * ly) ** 2
        ) <= 1.0
        mask = rotor1 | rotor2 | center_pod

    elif arch == "submarine":
        # Hydrodynamic teardrop hull + conning tower
        x_c, y_c = 0.45 * lx, 0.50 * ly
        hull = ((X - x_c) ** 2 / (0.35 * lx) ** 2 + (Y - y_c) ** 2 / (0.10 * ly) ** 2) <= 1.0
        sail = (
            (X >= x_c - 0.08 * lx) & (X <= x_c + 0.04 * lx)
            & (Y >= y_c) & (Y <= y_c + 0.18 * ly)
        )
        mask = hull | sail

    elif arch == "cylinder":
        cx, cy = 0.30 * lx, 0.50 * ly
        r = 0.08 * ly
        mask = (X - cx) ** 2 + (Y - cy) ** 2 <= r ** 2

    elif arch == "obstacle":
        mask = (X >= 0.3 * lx) & (X <= 0.45 * lx) & (Y >= 0.35 * ly) & (Y <= 0.65 * ly)

    elif arch == "venturi":
        # Converging-diverging nozzle: walls block outside the throat profile
        r_wall = 0.42 * ly * (
            1.0 - 0.55 * np.exp(-((X - 0.5 * lx) ** 2) / (0.12 * lx) ** 2)
        )
        mask = np.abs(Y - 0.5 * ly) >= r_wall

    elif arch == "water_dam":
        # Thin dam wall with a gate gap at the bottom — the reservoir
        # (initialized in the solver) collapses through the gap.
        dam_x = 0.45 * lx
        mask = (np.abs(X - dam_x) <= 0.02 * lx) & (Y >= 0.35 * ly)

    elif arch == "cad":
        if obstacle_spec:
            shape = str(obstacle_spec.get("shape", "circle")).lower()
            cx = float(obstacle_spec.get("cx", 0.4)) * lx
            cy = float(obstacle_spec.get("cy", 0.5)) * ly
            size = max(float(obstacle_spec.get("size", 0.15)), 0.02)
            spec_aoa = float(obstacle_spec.get("aoa", 0.0))
            if shape == "circle":
                mask = (X - cx) ** 2 + (Y - cy) ** 2 <= (size * ly) ** 2
            elif shape == "square":
                half = size * ly
                mask = (np.abs(X - cx) <= half) & (np.abs(Y - cy) <= half)
            elif shape == "rectangle":
                mask = (np.abs(X - cx) <= 1.6 * size * lx) & (np.abs(Y - cy) <= 0.6 * size * ly)
            elif shape == "airfoil":
                mask = _naca_symmetric_mask(X, Y, cx, cy, 3.0 * size * lx, spec_aoa, 0.12)
        # No spec yet -> no geometry (user has not chosen a shape)

    # plume / weather_plume / cavity -> no solid obstacle (thermal or lid driven)

    # Safety: never let the mask seal the whole domain
    if mask.all():
        return np.zeros((nx, ny), dtype=bool)
    return mask


class AcceleratedSolver:
    """Fractional-step incompressible Navier-Stokes with a CasePhysics layer."""

    def __init__(
        self,
        mesh: Mesh2D,
        physics: CasePhysics | None = None,
        archetype: str = "airfoil",
        aoa_deg: float = 0.0,
        obstacle_spec: dict | None = None,
    ):
        self.mesh = mesh
        self.physics = physics or CasePhysics()
        self.archetype = str(archetype or "cavity").lower()
        self.aoa_deg = float(aoa_deg)

        # March viscosity comes from real physics (SI nu or derived Re mapping)
        self.nu = self.physics.nu
        self.Re = max(self.physics.reynolds_real, 1.0)
        self.lid_velocity = self.physics.inlet_velocity
        self.alpha_s = self.nu  # scalar diffusivity (nu/Pr with Pr ~ 1)

        self.u = np.zeros((mesh.nx, mesh.ny))
        self.v = np.zeros((mesh.nx, mesh.ny))
        self.p = np.zeros((mesh.nx, mesh.ny))
        # Scalar transport: temperature (plume) or heavy-fluid fraction (dam)
        self.s = np.zeros((mesh.nx, mesh.ny))
        self.time = 0.0
        self.cfl = 0.0
        self.last_dt = 0.0
        # dt * mean|div u| over interior fluid cells after the projection
        # (the quantity OpenFOAM prints as "time step continuity errors").
        self.continuity_error = 0.0
        # Set when the explicit march blows up (non-finite values or the
        # velocity safety clamp engaging) — the run must not be reported
        # as a valid solution after that.
        self.diverged = False
        self.closed_domain = self.archetype in CLOSED_ARCHETYPES
        self.obstacle_shape = str((obstacle_spec or {}).get("shape", "")).lower()

        self.obstacle_mask = build_obstacle_mask(
            mesh, self.archetype, self.aoa_deg, obstacle_spec
        )
        self._init_scalar_field()
        self._build_poisson_matrix()
        self.apply_bc()

    def _init_scalar_field(self):
        """Initialize transported scalars: hot plume strip or dam-break reservoir."""
        nx, ny = self.mesh.nx, self.mesh.ny
        X, Y = self.mesh.X, self.mesh.Y
        lx, ly = self.mesh.lx, self.mesh.ly
        self.s = np.zeros((nx, ny))

        if self.archetype == "water_dam":
            # Heavy fluid column left of the dam, below the gate gap height
            self.s = ((X < 0.45 * lx) & (Y < 0.35 * ly)).astype(float)
        elif self.archetype in ("plume", "weather_plume"):
            # Heated strip on the bottom wall — the buoyancy source
            strip = (np.abs(X - 0.5 * lx) <= 0.10 * lx) & (Y <= 0.06 * ly)
            self.s = strip.astype(float)
        elif self.archetype == "venturi":
            # Passive smoke tracer seeded at the inlet for flow visualization
            self.s = (X <= 0.08 * lx).astype(float) * 0.8

        # Never seed scalars inside solid bodies
        self.s[self.obstacle_mask] = 0.0

    def _build_poisson_matrix(self):
        """Assemble and LU-factorize the 5-point pressure Laplacian once.

        Neumann (dp/dn = 0) is applied by boundary reflection on every wall.
        Open channel/tunnel archetypes then pin the outlet column to p = 0
        (Dirichlet), so mass imbalance leaves through the outlet. Closed
        boxes pin a single gauge cell instead and get a compatible RHS in
        step(). (The previous all-Neumann + corner pin for *open* flows was
        ill-posed: the incompatible RHS piled up into a singularity at the
        pinned corner, giving p ~ 260 and |div u| ~ 255 at U = 1.)

        The matrix never changes during a run, so it is factorized here and
        reused every step instead of re-running spsolve's factorization.
        """
        nx, ny = self.mesh.nx, self.mesh.ny
        dx, dy = self.mesh.dx, self.mesh.dy

        def neumann_1d(n: int, h: float) -> sp.spmatrix:
            main = np.full(n, -2.0)
            main[0] = main[-1] = -1.0  # ghost cell mirrors the boundary cell
            off = np.ones(n - 1)
            return sp.diags([off, main, off], [-1, 0, 1]) / h**2

        # Row-major (i, j) -> k = i*ny + j ordering, matching ndarray.ravel()
        lap = (
            sp.kron(neumann_1d(nx, dx), sp.identity(ny))
            + sp.kron(sp.identity(nx), neumann_1d(ny, dy))
        )

        pinned = np.zeros(nx * ny, dtype=bool)
        if self.closed_domain:
            pinned[0] = True                   # gauge: p = 0 at one cell
        else:
            pinned[(nx - 1) * ny:] = True      # Dirichlet outlet column
        self._pinned = pinned

        keep = sp.diags((~pinned).astype(float))
        self.A_poisson = (keep @ lap + sp.diags(pinned.astype(float))).tocsc()
        self._poisson_lu = spla.splu(self.A_poisson)

    def _apply_velocity_bc(self, u: np.ndarray, v: np.ndarray) -> None:
        """Apply the archetype's velocity BCs in place.

        Used for BOTH the predictor (u*, v*) and the corrected field, so the
        two can never disagree (they previously did for the plume cases).
        """
        U = self.lid_velocity
        if self.archetype == "cavity":
            u[:, 0] = 0.0;  v[:, 0] = 0.0    # bottom wall
            u[0, :] = 0.0;  v[0, :] = 0.0    # left wall
            u[-1, :] = 0.0; v[-1, :] = 0.0   # right wall
            u[:, -1] = U;   v[:, -1] = 0.0   # moving lid
        elif self.archetype == "water_dam":
            # Sealed tank: no-slip on all four walls, flow is purely
            # gravity-driven (no inlet "wind" blowing through a dam break).
            u[:, 0] = 0.0;  v[:, 0] = 0.0
            u[:, -1] = 0.0; v[:, -1] = 0.0
            u[0, :] = 0.0;  v[0, :] = 0.0
            u[-1, :] = 0.0; v[-1, :] = 0.0
        else:
            # Channel / wind tunnel: inlet left, zero-gradient outlet right
            u[0, :] = U;       v[0, :] = 0.0
            u[-1, :] = u[-2, :]; v[-1, :] = v[-2, :]
            if self.archetype in ("plume", "weather_plume"):
                # Free-slip (impermeable, shear-free) floor and lid
                u[:, 0] = u[:, 1];   v[:, 0] = 0.0
                u[:, -1] = u[:, -2]; v[:, -1] = 0.0
            else:
                # Freestream far-field top/bottom (moving ground for f1)
                u[:, 0] = U;  v[:, 0] = 0.0
                u[:, -1] = U; v[:, -1] = 0.0

        # Immersed body no-slip (staircase mask)
        if np.any(self.obstacle_mask):
            u[self.obstacle_mask] = 0.0
            v[self.obstacle_mask] = 0.0

    def apply_bc(self):
        """Apply velocity boundary conditions to the current solution."""
        self._apply_velocity_bc(self.u, self.v)

    def compute_forces(self, include_viscous: bool = True):
        """Integrate pressure + viscous forces on the immersed body.

        Staircase immersed boundary: every solid-cell face that touches a
        fluid cell is a surface element. Pressure is read on the fluid side
        of the face; wall shear uses the one-cell gradient to the no-slip
        solid cell (u = 0), tau/rho = nu * u_fluid / h, consistent with the
        solver's viscous stencil.

        Force on the body per unit depth (kinematic, rho = 1 as in the
        solver):  F = -sum (p - p_ref) n dA + sum tau dA.
        Coefficients divide by 0.5 U^2 L_ref, with L_ref = chord (x-extent)
        for airfoil-type bodies and frontal height (y-extent) otherwise.

        Returns (cd, cl, extra). Signs are physical: drag is +x, lift is +y,
        and nothing is clamped (a negative Cd is reported as such).
        Pass include_viscous=False for inviscid (slip-wall) fields such as
        the potential-flow preview, where a no-slip shear estimate is wrong.
        """
        extra = {}
        mask = self.obstacle_mask
        if not np.any(mask):
            return 0.0, 0.0, extra

        dx, dy = self.mesh.dx, self.mesh.dy
        rho = self.physics.rho
        U_ref = max(self.lid_velocity, 1e-6)
        p, u, v = self.p, self.u, self.v
        fluid = ~mask

        # Venturi: report the inlet -> throat pressure drop (Pa) instead of
        # body forces (the "body" is the nozzle wall).
        if self.archetype == "venturi":
            i_th = int(np.argmin(np.abs(self.mesh.xc - 0.5 * self.mesh.lx)))
            p_in = float(np.mean(p[1, fluid[1]]))
            p_th = float(np.mean(p[i_th, fluid[i_th]]))
            extra["pressureDrop"] = float(np.round((p_in - p_th) * rho, 4))
            return 0.0, 0.0, extra

        def shifted(f, axis, step):
            """Value of f at the neighbour (i-1 / i+1 / j-1 / j+1), aligned."""
            out = np.zeros_like(f)
            if axis == 0 and step == -1:
                out[1:, :] = f[:-1, :]
            elif axis == 0:
                out[:-1, :] = f[1:, :]
            elif step == -1:
                out[:, 1:] = f[:, :-1]
            else:
                out[:, :-1] = f[:, 1:]
            return out

        # Body faces, flagged on the solid cell (domain edges are not faces)
        front = mask & shifted(fluid, 0, -1)   # -x face, fluid at i-1
        rear = mask & shifted(fluid, 0, +1)    # +x face, fluid at i+1
        bot = mask & shifted(fluid, 1, -1)     # -y face, fluid at j-1
        top = mask & shifted(fluid, 1, +1)     # +y face, fluid at j+1

        p_ref = float(np.mean(p[fluid]))
        fx = (np.sum(shifted(p, 0, -1)[front] - p_ref)
              - np.sum(shifted(p, 0, +1)[rear] - p_ref)) * dy
        fy = (np.sum(shifted(p, 1, -1)[bot] - p_ref)
              - np.sum(shifted(p, 1, +1)[top] - p_ref)) * dx

        # Viscous wall shear: x-friction on top/bottom faces, y on front/rear
        if include_viscous:
            fx += self.nu * (np.sum(shifted(u, 1, +1)[top])
                             + np.sum(shifted(u, 1, -1)[bot])) / dy * dx
            fy += self.nu * (np.sum(shifted(v, 0, -1)[front])
                             + np.sum(shifted(v, 0, +1)[rear])) / dx * dy

        chord = max(np.count_nonzero(np.any(mask, axis=1)) * dx, dx)   # x-extent
        height = max(np.count_nonzero(np.any(mask, axis=0)) * dy, dy)  # y-extent
        chord_based = (
            self.archetype in CHORD_REFERENCED_ARCHETYPES
            or (self.archetype == "cad" and self.obstacle_shape == "airfoil")
        )
        q_ref = 0.5 * U_ref**2
        L_ref = chord if chord_based else height
        cd = float(fx) / (q_ref * L_ref)
        cl = float(fy) / (q_ref * L_ref)

        # --- Illustrative full-scale conversions (SI) -----------------------
        # These map the 2-D coefficients onto an ASSUMED operating point
        # (speed scale, reference area, depth). They are presentation
        # helpers, not independent predictions.
        if self.archetype == "f1":
            v_real = 80.0 * U_ref                  # assume 80 m/s at U = 1
            planform = 1.2 * self.mesh.lx          # assumed wing area [m^2]
            # Positive = downforce (Cl < 0); negative means the wing lifts.
            downforce = -cl * 0.5 * rho * v_real**2 * planform
            extra["downforce"] = float(np.round(downforce, 1))
        elif self.archetype == "drone":
            v_real = 15.0 * U_ref                  # assume 15 m/s at U = 1
            rotor_area = 0.05                      # assumed disk area [m^2]
            # Vertical force on the 2-D rotor-arm section in cross-flow
            thrust = cl * 0.5 * rho * v_real**2 * rotor_area
            extra["thrust"] = float(np.round(thrust, 2))
        elif self.archetype == "submarine":
            v_real = 10.0 * U_ref                  # assume 10 m/s at U = 1
            p_amb = 101325.0 + rho * 9.81 * 10.0   # assumed 10 m depth
            p_vapour = 2340.0                      # water at ~20 C [Pa]
            sigma = (p_amb - p_vapour) / max(0.5 * rho * v_real**2, 1.0)
            extra["cavitationIndex"] = float(np.round(sigma, 2))

        return float(np.round(cd, 4)), float(np.round(cl, 4)), extra

    def _stable_timestep(self, dt: float) -> float:
        """CFL + diffusion limited timestep keeps the explicit march stable."""
        dx, dy = self.mesh.dx, self.mesh.dy
        u_max = min(
            max(float(np.max(np.abs(self.u))), float(np.max(np.abs(self.v)))),
            50.0,
        )
        cfl_dt = 0.4 * min(dx, dy) / max(u_max, 1e-6)
        diff_dt = 0.2 * min(dx, dy) ** 2 / max(self.nu, 1e-12)
        return max(min(dt, cfl_dt, diff_dt), 1e-6)

    def step(self, dt: float):
        nx, ny = self.mesh.nx, self.mesh.ny
        dx, dy = self.mesh.dx, self.mesh.dy
        dt = self._stable_timestep(dt)
        
        u_old = self.u.copy()
        v_old = self.v.copy()
        
        # 1. Predictor (convection + diffusion)
        lap_u = np.zeros_like(self.u)
        lap_v = np.zeros_like(self.v)
        lap_u[1:-1, 1:-1] = (
            (self.u[2:, 1:-1] - 2*self.u[1:-1, 1:-1] + self.u[:-2, 1:-1])/dx**2 +
            (self.u[1:-1, 2:] - 2*self.u[1:-1, 1:-1] + self.u[1:-1, :-2])/dy**2
        )
        lap_v[1:-1, 1:-1] = (
            (self.v[2:, 1:-1] - 2*self.v[1:-1, 1:-1] + self.v[:-2, 1:-1])/dx**2 +
            (self.v[1:-1, 2:] - 2*self.v[1:-1, 1:-1] + self.v[1:-1, :-2])/dy**2
        )
        
        conv_u = np.zeros_like(self.u)
        conv_v = np.zeros_like(self.v)
        
        i, j = slice(1, -1), slice(1, -1)
        du_dx = np.where(self.u[i,j] > 0, (self.u[i,j] - self.u[:-2,j])/dx, (self.u[2:,j] - self.u[i,j])/dx)
        du_dy = np.where(self.v[i,j] > 0, (self.u[i,j] - self.u[i,:-2])/dy, (self.u[i,2:] - self.u[i,j])/dy)
        conv_u[i,j] = self.u[i,j] * du_dx + self.v[i,j] * du_dy
        
        dv_dx = np.where(self.u[i,j] > 0, (self.v[i,j] - self.v[:-2,j])/dx, (self.v[2:,j] - self.v[i,j])/dx)
        dv_dy = np.where(self.v[i,j] > 0, (self.v[i,j] - self.v[i,:-2])/dy, (self.v[i,2:] - self.v[i,j])/dy)
        conv_v[i,j] = self.u[i,j] * dv_dx + self.v[i,j] * dv_dy
        
        u_star = self.u.copy()
        v_star = self.v.copy()
        
        u_star[1:-1, 1:-1] += dt * (self.nu * lap_u[1:-1, 1:-1] - conv_u[1:-1, 1:-1])
        v_star[1:-1, 1:-1] += dt * (self.nu * lap_v[1:-1, 1:-1] - conv_v[1:-1, 1:-1])

        # 1b. Buoyancy (Boussinesq) / gravity-driven heavy fluid
        if self.archetype in BUOYANT_ARCHETYPES and self.physics.g_mag > 1e-6:
            g_y = self.physics.gravity[1]
            if self.archetype == "water_dam":
                # Heavy fraction falls WITH gravity
                v_star[1:-1, 1:-1] += dt * g_y * self.s[1:-1, 1:-1]
            else:
                # Hot fluid rises: force OPPOSES gravity (-g * beta * dT)
                v_star[1:-1, 1:-1] += (
                    -dt * g_y * self.physics.beta
                    * self.physics.delta_t_ref * self.s[1:-1, 1:-1]
                )

        # 1c. Scalar transport (temperature / dye / heavy-fluid fraction)
        lap_s = np.zeros_like(self.s)
        lap_s[1:-1, 1:-1] = (
            (self.s[2:, 1:-1] - 2*self.s[1:-1, 1:-1] + self.s[:-2, 1:-1])/dx**2 +
            (self.s[1:-1, 2:] - 2*self.s[1:-1, 1:-1] + self.s[1:-1, :-2])/dy**2
        )
        ds_dx = np.where(u_star[1:-1, 1:-1] > 0,
                         (self.s[1:-1, 1:-1] - self.s[:-2, 1:-1])/dx,
                         (self.s[2:, 1:-1] - self.s[1:-1, 1:-1])/dx)
        ds_dy = np.where(v_star[1:-1, 1:-1] > 0,
                         (self.s[1:-1, 1:-1] - self.s[1:-1, :-2])/dy,
                         (self.s[1:-1, 2:] - self.s[1:-1, 1:-1])/dy)
        s_star = self.s.copy()
        s_star[1:-1, 1:-1] += dt * (
            self.alpha_s * lap_s[1:-1, 1:-1]
            - u_star[1:-1, 1:-1] * ds_dx - v_star[1:-1, 1:-1] * ds_dy
        )
        s_star = np.clip(np.nan_to_num(s_star, nan=0.0), 0.0, 1.5)

        # Safety clamp against overflow. A healthy run never comes near 10x
        # the reference speed; if it does, the march has diverged and is
        # flagged instead of being silently clipped into plausible numbers.
        u_cap = 10.0 * max(abs(self.lid_velocity), 1.0)
        for field in (u_star, v_star):
            if not np.all(np.isfinite(field)) or np.max(np.abs(field)) >= u_cap:
                self.diverged = True
        u_star = np.clip(np.nan_to_num(u_star, nan=0.0, posinf=u_cap, neginf=-u_cap), -u_cap, u_cap)
        v_star = np.clip(np.nan_to_num(v_star, nan=0.0, posinf=u_cap, neginf=-u_cap), -u_cap, u_cap)

        # Same BCs as the corrected field (single source of truth)
        self._apply_velocity_bc(u_star, v_star)

        # Scalar boundary conditions: keep steady sources alive
        if self.archetype in ("plume", "weather_plume"):
            strip = (
                (np.abs(self.mesh.X - 0.5 * self.mesh.lx) <= 0.10 * self.mesh.lx)
                & (self.mesh.Y <= 0.06 * self.mesh.ly)
            )
            s_star[strip] = 1.0
        elif self.archetype == "water_dam":
            reservoir = (
                (self.mesh.X < 0.03 * self.mesh.lx)
                & (self.mesh.Y < 0.35 * self.mesh.ly)
            )
            s_star[reservoir] = 1.0
        elif self.archetype == "venturi":
            s_star[0, :] = 0.8
        s_star[self.obstacle_mask] = 0.0

        # 2. Pressure Poisson RHS: (1/dt) * div(u_star)
        div_ustar = np.zeros_like(self.u)
        div_ustar[1:-1, 1:-1] = (
            (u_star[2:, 1:-1] - u_star[:-2, 1:-1]) / (2 * dx) +
            (v_star[1:-1, 2:] - v_star[1:-1, :-2]) / (2 * dy)
        )
        rhs = (div_ustar / dt).ravel()
        if self.closed_domain:
            # Pure-Neumann box: the Laplacian's range is the mean-zero
            # vectors, so remove the discretization's net divergence before
            # pinning the gauge cell (otherwise it piles up at that cell).
            free = ~self._pinned
            rhs[free] -= rhs[free].mean()
        rhs[self._pinned] = 0.0

        # Sparse solve, reusing the LU factorization built once in __init__
        p_flat = self._poisson_lu.solve(rhs)
        self.p = np.clip(np.nan_to_num(p_flat.reshape((nx, ny)), nan=0.0), -1e4, 1e4)

        # 3. Correct velocity
        dp_dx = np.zeros_like(self.p)
        dp_dy = np.zeros_like(self.p)
        dp_dx[1:-1, :] = (self.p[2:, :] - self.p[:-2, :]) / (2 * dx)
        dp_dy[:, 1:-1] = (self.p[:, 2:] - self.p[:, :-2]) / (2 * dy)

        self.u[1:-1, 1:-1] = np.clip(np.nan_to_num(u_star[1:-1, 1:-1] - dt * dp_dx[1:-1, 1:-1]), -u_cap, u_cap)
        self.v[1:-1, 1:-1] = np.clip(np.nan_to_num(v_star[1:-1, 1:-1] - dt * dp_dy[1:-1, 1:-1]), -u_cap, u_cap)
        self.s = s_star

        self.apply_bc()
        self.time += dt
        self.last_dt = dt
        u_max = float(np.max(np.abs(self.u)))
        self.cfl = u_max * dt / self.mesh.dx
        self.continuity_error = self._continuity_error(dt)

        # Residual
        res_u = float(np.max(np.nan_to_num(np.abs(self.u - u_old), nan=0.0)))
        res_v = float(np.max(np.nan_to_num(np.abs(self.v - v_old), nan=0.0)))
        return max(res_u, res_v)

    def divergence(self) -> np.ndarray:
        """Central-difference div(u) on interior nodes (zero on the boundary)."""
        dx, dy = self.mesh.dx, self.mesh.dy
        div = np.zeros_like(self.u)
        div[1:-1, 1:-1] = (
            (self.u[2:, 1:-1] - self.u[:-2, 1:-1]) / (2 * dx)
            + (self.v[1:-1, 2:] - self.v[1:-1, :-2]) / (2 * dy)
        )
        return div

    def _continuity_error(self, dt: float) -> float:
        """dt * mean |div u| over interior fluid cells (measured, not assumed)."""
        interior = ~self.obstacle_mask
        interior[[0, -1], :] = False
        interior[:, [0, -1]] = False
        if not np.any(interior):
            return 0.0
        return float(dt * np.mean(np.abs(self.divergence()[interior])))


# ---------------------------------------------------------------------------
# OpenFOAM dictionary override parsing
# ---------------------------------------------------------------------------
# Matches `key value;` and `key [0 2 -1 ...] value;` (dimensioned scalars)
_DICT_ENTRY_RE = re.compile(
    r"\b([A-Za-z_]\w*)\s+(?:\[[^\]]*\]\s*)?([-+0-9.eE]+)\s*;"
)

# Dict keys we honor when the user edits a dictionary file
_OVERRIDE_KEY_MAP = {
    "deltat": "dt",
    "dt": "dt",
    "nu": "nu",
    "viscosity": "nu",
    "inletvelocity": "inlet_velocity",
    "uinf": "inlet_velocity",
    "lidvelocity": "inlet_velocity",
}


def parse_dict_overrides(overrides: dict | None) -> dict:
    """Extract user-edited numeric values from OpenFOAM dict content.

    Accepts two shapes (both from the UI dict editor):
      * {fileName: {name, content}} — parsed via _DICT_ENTRY_RE from content
      * {deltaT: 0.002, nu: 1.5e-5, ...} — direct numeric overrides

    Returns {param: value} with keys mapped onto solver/CasePhysics
    parameters (deltaT -> dt, nu -> nu, UInlet/lidVelocity -> inlet_velocity).
    """
    result: dict = {}
    if not overrides or not isinstance(overrides, dict):
        return result
    for key, entry in overrides.items():
        if isinstance(entry, dict):
            # Dict-editor format: {fileName: {name, content}}
            content = str(entry.get("content", ""))
            for dict_key, raw_value in _DICT_ENTRY_RE.findall(content):
                mapped = _OVERRIDE_KEY_MAP.get(dict_key.lower())
                if not mapped:
                    continue
                try:
                    result[mapped] = float(raw_value)
                except (ValueError, TypeError):
                    continue
        else:
            # Flat numeric format: {deltaT: 0.002}
            mapped = _OVERRIDE_KEY_MAP.get(str(key).lower())
            if not mapped:
                continue
            try:
                result[mapped] = float(entry)
            except (ValueError, TypeError):
                continue
    return result
