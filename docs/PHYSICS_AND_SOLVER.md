# 🔬 Physics & CFD Solver

This document describes what `backend/solver.py` (Python), `rust-sidecar/src/cfd_solver.rs`
(Rust) and `backend/ai_predictor.py` (instant preview) actually compute. All three are
**two-dimensional**; the 3-D viewport shows the 2-D solution extruded along the span.

> An earlier version of this page described a 3-D solver (`backend/solver_3d.py`) and a
> "PINN AI surrogate". Neither existed. The numbers in section 5 were measured on the
> current code.

---

## 1. Governing equations

Incompressible Navier–Stokes in kinematic form (p is pressure / ρ) with a Boussinesq
buoyancy term, plus transport of one passive or active scalar `s`:

$$\nabla \cdot \vec{u} = 0$$

$$\frac{\partial \vec{u}}{\partial t} + (\vec{u} \cdot \nabla) \vec{u} = -\nabla p + \nu \nabla^2 \vec{u} + \vec{f}(s)$$

$$\frac{\partial s}{\partial t} + (\vec{u} \cdot \nabla) s = \nu \nabla^2 s \qquad (\text{Pr} = 1)$$

| Case | Meaning of `s` | Body force $\vec f(s)$ |
| --- | --- | --- |
| `plume`, `weather_plume` | normalized temperature, $T = T_{amb} + \Delta T\, s$ | $-\vec g\, \beta\, \Delta T\, s$ (hot fluid rises, cold sinks) |
| `water_dam` | heavy-fluid fraction | $\vec g\, s$ |
| `venturi` | passive dye tracer | none |

$\nu$ comes from the Reynolds slider as $\nu = U L / Re$ with $L = 1$ m (the domain height),
unless a `nu` value is set in the dictionary editor. Fluid density, $\beta$ and $c_p$ come
from the substance table and only enter through buoyancy and the conversion of kinematic
pressure to pascals.

## 2. Discretization (Python solver)

Uniform collocated grid, `nx × ny` cells over `lx × ly` (2 × 1 m for `airfoil`, `cylinder`,
`obstacle`; 1 × 1 m otherwise). Each time step:

1. **Time step**: $\Delta t = \min(\Delta t_{user},\ 0.4\, h / |u|_{max},\ 0.2\, h^2/\nu)$.
   The explicit scheme is only *conditionally* stable; these CFL and diffusion limits are
   what keep it stable.
2. **Predictor**: first-order upwind advection, second-order central diffusion, body force.
3. **Pressure Poisson**: $\nabla^2 p = \nabla \cdot \vec u^* / \Delta t$ with the 5-point
   Laplacian. Walls and inlet are Neumann ($\partial p/\partial n = 0$).
   - Open channels (inlet left, outlet right): **Dirichlet $p = 0$ on the outlet column**.
   - Sealed boxes (`cavity`, `water_dam`): pure Neumann, so the RHS is made mean-zero and
     one gauge cell is pinned.
   The matrix is LU-factorized once (SciPy SuperLU) and reused every step.
4. **Correction**: $\vec u^{n+1} = \vec u^* - \Delta t\, \nabla p$ (central differences).
   This is an *approximate* projection (compact Laplacian vs. wide divergence/gradient),
   so $\nabla \cdot \vec u$ is small but not zero; the measured value is reported as
   `continuityError` = $\Delta t \cdot \overline{|\nabla \cdot \vec u|}$ every frame.
5. **Boundary conditions**: inlet $u = U$; zero-gradient outlet; freestream $u = U$ on
   floor and lid (free-slip for plumes); no-slip walls for sealed boxes and a moving lid
   for the cavity. Bodies are **staircase immersed boundaries**: $\vec u = 0$ in masked cells.
6. **Divergence guard**: if any velocity is non-finite or exceeds 10× the reference speed,
   the run stops and reports divergence instead of clipping the field.

Residual = $\max |\vec u^{n+1} - \vec u^n|$ per step; "converged" means residual < 1e-5.

## 3. Forces

Pressure and wall shear are integrated over every solid-cell face that touches fluid:

$$\vec F = -\sum (p - p_{ref})\, \vec n\, \Delta A + \sum \nu \frac{u_t}{h}\, \Delta A$$

$C_D = F_x / (\tfrac12 U^2 L_{ref})$, $C_L = F_y / (\tfrac12 U^2 L_{ref})$ per unit depth, with
$L_{ref}$ = chord for airfoil-type bodies and frontal height for bluff bodies. Positive
angle of attack is nose-up. The downforce / thrust / cavitation-number readouts convert
these coefficients at an *assumed* full-scale operating point (see `compute_forces`).

## 4. Instant preview ("ai" mode) — not machine learning

* **Bodies, channels, venturi**: inviscid **potential flow** around the actual obstacle mask
  (one sparse Laplace solve for the velocity potential, Bernoulli pressure). Exactly
  divergence-free; captures blockage and throat speed-up; by d'Alembert's paradox it has
  ~zero drag and no circulation lift.
* **Cavity**: the **Stokes (Re → 0) solution**, one sparse biharmonic solve for the
  streamfunction. Misses the inertial asymmetry that grows with Re.
* **Buoyant cases**: no instant approximation exists; the server runs the CFD solver.

## 5. Validation (measured, `python experiments/run_milestone_simulations.py`)

Lid-driven cavity, Re = 100, steady state vs. Ghia, Ghia & Shin (1982), centreline RMSE:

| Grid | RMSE u(y) | RMSE v(x) |
| --- | --- | --- |
| 21 × 21 | 0.0785 | 0.0467 |
| 41 × 41 | 0.0385 | 0.0251 |
| 61 × 61 | 0.0261 | 0.0168 |

Observed order of accuracy ≈ 0.98 — first order, as expected from upwind advection.
The Stokes preview scores RMSE ≈ 0.03 at Re = 100 in ~25 ms. The Rust kernel (a different
scheme, Barba's pressure-Poisson form with Jacobi sweeps) agrees with the Python solver to
~1–3 % on C_D, C_L and venturi pressure drop.

## 6. Limitations

* 2-D only; laminar only (no turbulence model). High Reynolds numbers on these grids are
  dominated by first-order numerical diffusion, so the effective Re is far lower than the
  slider value.
* Staircase bodies resolve curved surfaces to within one cell.
* Time accuracy is first order; transient phenomena (e.g. vortex shedding) are not
  validated.
