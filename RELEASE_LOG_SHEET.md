# 📋 OpenZess Studio — Major Release & Update Log Sheet
**Project Title:** AI-Augmented High-Performance Web CFD Platform  
**Project Identifier:** UR2627GEN317  
**Repository:** `rosdebbu/openn_fOam`  
**Tracking Purpose:** Official verification & synchronization log sheet for all simulation, UI, sidebar, and engine updates.

---

## 🚀 Version Overview & Release History

| Release Version | Date | Commit Hash | Key Major Modules Updated | Build Status |
|---|---|---|---|---|
| **v2.5.0 (Latest)** | Sep 23, 2026 | `000929d` + `Fix` | TypeScript build unblock, smart build auto-detector, no-cache headers | ✅ Operational |
| **v2.4.0** | Sep 14, 2026 | `4030d78` | Hybrid model banners, robust static directory resolver | ✅ Verified |
| **v2.3.0** | Sep 14, 2026 | `2839401` | 3-way physics engine selector (Rust, PINN AI, SciPy) | ✅ Verified |
| **v2.2.0** | Sep 13, 2026 | `96577c7` | Sleek collapsible sidebar, top toggle button, slide animation | ✅ Verified |
| **v2.1.0** | Sep 13, 2026 | `ff1757c` | Unified 1-line viewport HUD ribbon, widescreen CAD mode | ✅ Verified |
| **v2.0.0** | Sep 10, 2026 | `0034bac` | Continuous 3D ribbon streamlines, multi-axis slice planes, AI agent | ✅ Verified |
| **v1.9.0** | Sep 10, 2026 | `73751d0` | 11x faster Poisson solver, hybrid convection wake, SimScale stats | ✅ Verified |
| **v1.8.0** | Sep 06, 2026 | `b428119` | High-performance Rust Navier-Stokes CFD solver & Axum sidecar | ✅ Verified |
| **v1.0.0** | Aug 27, 2026 | `8c52a83` | Initial 3D Studio interface with Colab hardware widget | 📦 Baseline |

---

## 🔬 Detailed Changelog by Subsystem

### 1. Simulation & Numerical Physics Engine
- **11x Faster Poisson Solver:** Factored pre-conditioned sparse pressure-Poisson solver using banded SciPy CSR matrix structures.
- **3-Way Physics Engine Switcher:** Instant runtime selection between:
  1. `Rust Engine`: Bare-metal multi-threaded Rayon SIMD stencil engine (5.8x acceleration).
  2. `PINN AI Surrogate`: Physics-Informed neural surrogate predicting steady-state flow in <50 ms.
  3. `Python SciPy Engine`: High-fidelity fractional-step projection method with Boussinesq thermal buoyancy.
- **Continuous 3D Ribbon Streamlines:** RK4 particle advection tracers rendering volumetric flow velocity gradients.
- **Multi-Axis Slicing Planes:** Orthogonal XY, YZ, and XZ dynamic cut-planes with live colormaps (Turbo, Coolwarm, Jet, Viridis, Inferno).

### 2. Sidebar & Navigation Interface
- **ChatGPT-Style Collapsible Sidebar:** One-click toggle button (`Ctrl + \`) smoothly sliding the left OpenFOAM Case Hub off-canvas for 100% widescreen CAD viewing.
- **OpenFOAM Case Hub Hierarchy:** Tree view displaying `0/`, `constant/`, and `system/` case dictionaries.
- **AI Copilot & Idea Assistant:** Interactive drawer with prompt suggestions for airfoil angles of attack, thermal buoyancy, and vortex shedding.
- **Real-Time Aerodynamics Telemetry:** Live HUD display of $C_d$ (drag), $C_l$ (lift), $L/D$ ratio, and Courant numbers ($\text{Co}_{\text{max}}$).

### 3. Build & Local Server Synchronization (Prevention of "Old Version" Issues)
- **Root Cause Identified:** A missing import (`SolverMode`) in `src/App.vue` was silently failing `npm run build`, leaving `dist/` frozen on an August 27 build.
- **Automatic Version Detection:** `backend/app.py` now compares timestamps of all `dist/` folders and automatically serves the newest build.
- **Anti-Cache HTTP Headers:** `Cache-Control: no-cache, no-store, must-revalidate` middleware prevents browsers from caching stale `.js` and `.css` bundles.

---

## 🛠️ How to Prevent Stale Version Issues in the Future

To ensure you never face the "old version opening" headache again:
1. **Always run the automated sync launcher:**
   ```bash
   python sync_and_launch.py
   ```
2. **Hard Refresh your browser after pulling updates:**
   Press `Ctrl + F5` (or `Ctrl + Shift + R`) to force the browser to discard any old cached assets.
