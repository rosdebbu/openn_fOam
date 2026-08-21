# 🔬 3D Aerothermal Physics & CFD Solver Engine

This document details the governing equations, numerical methods, and boundary condition formulations implemented in `backend/solver_3d.py`.

---

## 📐 1. Governing Mathematical Equations

OpenZess solves the coupled **3D Incompressible Navier-Stokes Equations** and **Thermal Energy Convection-Diffusion Equation**:

### 1. Incompressibility (Continuity):
$$\nabla \cdot \vec{u} = \frac{\partial u}{\partial x} + \frac{\partial v}{\partial y} + \frac{\partial w}{\partial z} = 0$$

### 2. 3D Momentum Equations with Boussinesq Thermal Buoyancy:
$$\frac{\partial \vec{u}}{\partial t} + (\vec{u} \cdot \nabla) \vec{u} = -\frac{1}{\rho}\nabla p + \nu \nabla^2 \vec{u} + \vec{g} \beta (T - T_{amb})$$
- $\vec{u} = (u, v, w)$ is the 3D velocity vector.
- $p$ is the scalar kinematic pressure field ($\text{Pa}$).
- $\nu$ is kinematic viscosity ($\text{m}^2/\text{s}$).
- $\vec{g} = (0, 0, -9.81\text{ m/s}^2)$ is the gravity vector.
- $\beta = 1 / T_{amb}$ is the thermal expansion coefficient.
- $(T - T_{amb})$ drives the vertical buoyancy updraft ($+w$) when heat sources exist.

### 3. 3D Thermal Energy Transport Equation:
$$\frac{\partial T}{\partial t} + (\vec{u} \cdot \nabla) T = \alpha \nabla^2 T + S_T$$
- $T$ is temperature field ($\text{K}$).
- $\alpha = \nu / Pr$ is the thermal diffusivity ($Pr \approx 0.71$ for air).
- $S_T$ represents heat sources (e.g. heated radiator surfaces).

---

## ⚙️ 2. Numerical Discretization (Fractional-Step Method)

Each time step $\Delta t$ executes the following sequence:

1. **Predictor Step (Advection & Diffusion)**:
   $$\vec{u}^* = \vec{u}^n + \Delta t \left[ \nu \nabla^2 \vec{u}^n - (\vec{u}^n \cdot \nabla) \vec{u}^n + \vec{g} \beta (T^n - T_{amb}) \right]$$
   - Convection terms $(\vec{u} \cdot \nabla)\vec{u}$ use 1st-order upwind differencing for unconditional numerical stability.
   - Diffusion terms $\nabla^2 \vec{u}$ use 2nd-order central differences across $(dx, dy, dz)$.

2. **3D Pressure Poisson Solution**:
   $$\nabla^2 p = \frac{\rho}{\Delta t} \nabla \cdot \vec{u}^*$$
   - Solved via a vectorized 3D iterative Poisson solver enforcing Dirichlet outlet ($p = 0$) and Neumann wall boundary conditions.

3. **Velocity Correction**:
   $$\vec{u}^{n+1} = \vec{u}^* - \Delta t \nabla p$$

4. **Thermal Energy Update**:
   $$T^{n+1} = T^n + \Delta t \left[ \alpha \nabla^2 T^n - (\vec{u}^n \cdot \nabla) T^n \right]$$

---

## ⚡ 3. Instant 3D PINN AI Surrogate Mode

For interactive exploratory design, the engine includes a Physics-Informed surrogate model that provides instant steady-state solutions in under **50 ms**:
- **Stagnation Front**: Calculates pressure rise $p_{stag} = \frac{1}{2}\rho U_{in}^2$ on upstream obstacle surfaces.
- **Wake Recirculation**: Generates downstream velocity deficit and trailing vortex structures.
- **Thermal Plume Dynamics**: Convects rising thermal cones $(\beta g \Delta T)$ upward towards the domain ceiling.
