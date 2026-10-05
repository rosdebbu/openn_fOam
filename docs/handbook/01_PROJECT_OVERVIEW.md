# 🧭 OpenZess Studio — Project Overview & Vision

> **Target Audience:** Engineering Collaborators, CFD Researchers, and Developers  
> **Project Code:** UR2627GEN317  
> **Repository:** [openn_fOam](https://github.com/rosdebbu/openn_fOam)  

---

## 1. What is OpenZess Studio?

**OpenZess Studio** is a modern, web-native Computational Fluid Dynamics (CFD) engineering platform and AI Co-Engineer designed to bridge the gap between heavy industrial solvers like **OpenFOAM** and real-time interactive browser environments.

Traditional OpenFOAM workflows require:
* Navigating complex Linux command-line environments.
* Manually writing and editing tens of obscure C++ dictionary files (`controlDict`, `fvSchemes`, `fvSolution`, `snappyHexMeshDict`, `0/U`, `0/p`).
* Lengthy compile-mesh-solve-postprocess cycles before spotting mesh or boundary condition errors.

**OpenZess Studio solves this by providing:**
1. **Interactive In-Browser Simulation:** Real-time 2D/3D Navier-Stokes flow visualization powered by Three.js WebGL and accelerated numerical solvers.
2. **True OpenFOAM Parity:** Bi-directional synchronization between interactive UI sliders and standard OpenFOAM dictionary files.
3. **1-Click OpenFOAM Export:** Instantly packages cases into production-ready OpenFOAM directory trees for high-performance cluster computing (`simpleFoam`, `pimpleFoam`, `buoyantBoussinesqSimpleFoam`).
4. **AI CFD Co-Engineer:** An embedded Physics-Informed reasoning agent capable of diagnosing convergence issues, repairing boundary condition syntax, and computing aerodynamic/hydrodynamic forces.

---

## 2. Core Problem Domains

OpenZess Studio is built to handle complex multi-physics scenarios:

| Domain | Representative Archetypes | Physical Challenges Addressed |
| :--- | :--- | :--- |
| **Maritime & Defense** | Submarine, Hydrofoil, Torpedo | Ocean seawater density ($\rho = 1025\ \text{kg/m}^3$), hydrostatic pressure gradients ($\rho g h$), cavitation index ($\sigma$), hydrodynamic drag. |
| **Aerospace & UAVs** | Quadcopter Drone, NACA Airfoil | Rotor downwash, ground effect, boundary layer separation, angle-of-attack stall. |
| **Automotive** | Formula 1 Front Wing, Venturi Duct | Ground-effect venturi channels, vortex generation, downforce-to-drag ratios. |
| **Civil & Environmental** | Dam Break, Thermal Chimney Plume | Gravity-driven free-surface sloshing, thermal buoyancy, Rayleigh-Bénard convection. |

---

## 3. Technology Stack at a Glance

* **Frontend:** Vue 3 (Composition API) + TypeScript + Three.js WebGL (custom GLSL shaders for pressure/velocity contours).
* **Backend:** FastAPI (Python 3.10+) with Uvicorn ASGI server.
* **Inner Loop Numerical Solvers:**
  * **Rust SIMD Sidecar (`rust-sidecar/`):** Multi-threaded Rayon Poisson pressure solver and high-speed advection-diffusion loop.
  * **Python SciPy Solver:** Robust sparse linear solver (`scipy.sparse.linalg.spsolve`) fallback ensuring 100% operational uptime across all operating systems.
* **Storage & Persistence:** Disk-backed simulation snapshots (`backend/saved_projects/`) paired with client-side `localStorage` caching.
