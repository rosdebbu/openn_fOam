# OpenZess Studio — Comprehensive Step-by-Step Engineering Changelog

**Project:** OpenZess Studio (UR2627GEN317)  
**System:** Web-based OpenFOAM CFD Platform & AI Co-Engineer  
**Architecture:** FastAPI (Python) + Rust SIMD Sidecar + Vue 3 (TypeScript) + Three.js WebGL  
**Date:** October 5, 2026  
**Status:** Phase 1 (100% Complete) | Phase 2 (Tasks 2.3 & 2.4 Complete) | Production Build Verified  

---

## 1. Executive Summary

This document records all architectural updates, bug fixes, simulation upgrades, and UI refactorings completed across the OpenZess Studio codebase. 

### Core Problems Solved:
1. **Localhost Stale Caching Bug:** Resolved an issue where frontend code changes were not reflected in the browser upon refresh due to browser caching and mismatched build directory paths.
2. **Left Sidebar Cramped Layout:** Replaced a cramped 2-column sidebar with a 4-tab full-width responsive control center.
3. **OpenFOAM Physical Parity:** Enhanced physical fidelity with ocean seawater density ($\rho = 1025\ \text{kg/m}^3$), hydrostatic pressure gradients ($\rho g h$), cavitation index calculations ($\sigma$), and live aerodynamic force integrations.
4. **Interactive Custom Geometry Builder:** Added an interactive solid obstacle builder allowing users to design and simulate custom obstacles (cylinder, square, plate, NACA 4-digit airfoil) with real-time parameter adjustment.
5. **Project Persistence:** Added server-side JSON storage (`/api/projects`) combined with client-side `localStorage` caching to save, name, and load simulation cases.
6. **Rust vs. Python Division of Work:** Defined clear boundaries between Python (orchestration, OpenFOAM case file generation, AI Copilot) and Rust (SIMD Rayon numerical solver, 3D Poisson equation, streamline tracing).

---

## 2. File-by-File Detailed Breakdown

### A. Backend Architecture

#### 1. [`backend/app.py`](file:///c:/Users/ROSHNI/OneDrive/Documents/GitHub/openn_fOam/backend/app.py)
* **Frontend Auto-Build Validation (`_ensure_fresh_frontend_build`):**
  * Automatically detects if files in `frontend/src` have been modified more recently than `frontend/dist`.
  * Runs `npm run build` synchronously at startup if stale to ensure the latest bundle is always served.
* **Aggressive Anti-Caching HTTP Headers:**
  * Implemented an ASGI middleware injecting:
    * `Cache-Control: no-cache, no-store, must-revalidate, max-age=0`
    * `Pragma: no-cache`
    * `Expires: 0`
    * `X-OpenZess-Build-Time: <timestamp>`
  * Guarantees developers and users never load cached scripts or styles on `localhost:8000`.
* **Path Resolution Priority:**
  * Fixed path precedence to serve directly from the workspace's local `frontend/dist` rather than any external `C:\gitwork` directory.
* **Router Expansion:**
  * Mounted the project persistence router (`app.include_router(projects_router)`).
* **PINN AI Mode Force Integration:**
  * Replaced hardcoded forces with live dynamic force integration using `AcceleratedSolver.compute_forces()` across custom obstacle boundaries.
* **Dictionary Override Ingestion:**
  * Integrated `parse_dict_overrides()` to apply user-edited OpenFOAM dictionary parameters directly to active simulation states.

#### 2. [`backend/solver.py`](file:///c:/Users/ROSHNI/OneDrive/Documents/GitHub/openn_fOam/backend/solver.py)
* **Fluid Database Expansion:**
  * Added `seawater`: Density $\rho = 1025.0\ \text{kg/m}^3$, Kinematic Viscosity $\nu = 1.05 \times 10^{-6}\ \text{m}^2/\text{s}$.
* **Submarine & Ocean Hydrodynamics:**
  * Implemented Cavitation Index calculation:
    $$\sigma = \frac{p_\infty - p_v}{\frac{1}{2} \rho U_\infty^2}$$
  * Implemented Hydrostatic Pressure Gradient:
    $$\Delta p_{\text{hydro}} = \rho g h$$
* **Custom Solid Obstacle Generator (`build_obstacle_mask`):**
  * Added parametric shape builders for:
    * **Circle/Cylinder:** Mask defined by $(X - c_x)^2 + (Y - c_y)^2 \le r^2$.
    * **Square & Rectangle:** Bounded box masks with aspect ratio scaling.
    * **Airfoil (NACA 4-digit):** Evaluates chord rotation, angle of attack $\alpha$, and thickness distribution:
      $$y_t = 0.6 c \left( 0.2969\sqrt{x/c} - 0.1260(x/c) - 0.3516(x/c)^2 + 0.2843(x/c)^3 - 0.1015(x/c)^4 \right)$$
* **OpenFOAM Dictionary Scalar Parser (`parse_dict_overrides`):**
  * Regular expressions parse standard OpenFOAM dimensioned scalars:
    * `deltaT [0 0 1 0 0 0 0] <val>;`
    * `nu [0 2 -1 0 0 0 0] <val>;`
    * `internalField uniform (<ux> <uy> <uz>);`
  * Overrides the solver's internal timestep, viscosity, and inflow conditions in real time.

#### 3. [`backend/projects.py`](file:///c:/Users/ROSHNI/OneDrive/Documents/GitHub/openn_fOam/backend/projects.py) *(New File)*
* **Persistent Storage Architecture:**
  * Disk-backed JSON case files stored in `backend/saved_projects/`.
* **REST Endpoints:**
  * `POST /api/projects/save`: Saves simulation parameters, custom obstacle specs, OpenFOAM dictionary overrides, and metadata.
  * `GET /api/projects/load/{project_id}`: Loads and validates a saved simulation snapshot.
  * `GET /api/projects`: Lists all saved projects sorted by modification date.

#### 4. [`backend/rust_bridge.py`](file:///c:/Users/ROSHNI/OneDrive/Documents/GitHub/openn_fOam/backend/rust_bridge.py) *(New File)*
* **Subprocess Management & Fallback:**
  * Manages IPC communication with the compiled Rust SIMD binary (`rust-sidecar/target/release/cfd_core.exe`).
  * Features an automatic fallback to Python's SciPy sparse linear solver (`scipy.sparse.linalg.spsolve`) if the Rust binary is missing or blocked by host policy.

#### 5. [`backend/vtk_writer.py`](file:///c:/Users/ROSHNI/OneDrive/Documents/GitHub/openn_fOam/backend/vtk_writer.py)
* **Export Standards:**
  * Generates structured legacy VTK files for velocity ($U$), pressure ($p$), and vorticity ($\omega$).
  * Fully compatible with ParaView and OpenFOAM post-processing pipelines.

#### 6. [`main.py`](file:///c:/Users/ROSHNI/OneDrive/Documents/GitHub/openn_fOam/main.py)
* **Hot Reloading:**
  * Enabled `reload=True` for Uvicorn during local development so backend updates take effect immediately without manual server restarts.

---

### B. Frontend Architecture

#### 1. [`frontend/src/components/SidebarControls.vue`](file:///c:/Users/ROSHNI/OneDrive/Documents/GitHub/openn_fOam/frontend/src/components/SidebarControls.vue)
* **Full Sidebar Redesign:**
  * Replaced the previous 2-column sidebar layout with 4 full-width dedicated tabs:
    1. **`🌊 Physics & Water`:**
       * Inflow Velocity ($U_\infty$), Angle of Attack ($\alpha$), Domain Vorticity Core, Fluid Temperature.
       * Fluid Medium Selection: Air, Water, Seawater, CO2, Oil, Ethanol.
       * Fluid Physical Property Cards displaying $\rho$ ($\text{kg/m}^3$), $\nu$ ($\text{m}^2/\text{s}$), and description.
       * Gravity Presets: Earth ($9.81\ \text{m/s}^2$), Zero-$g$, Mars ($3.72\ \text{m/s}^2$).
    2. **`🧱 Geometry & Custom Builder`:**
       * Archetype selector: Submarine, Drone, Airfoil, F1 Front Wing, Venturi, Dam Break, Cylinder.
       * **Interactive Custom Obstacle Builder:**
         * Shape selector: Cylinder, Square, Plate, NACA Airfoil.
         * Sliders for Center X ($0.1 - 0.9$), Center Y ($0.1 - 0.9$), Scale ($0.05 - 0.50$), Angle of Attack ($-45^\circ$ to $+45^\circ$).
         * `▶ Run Simulation with This Geometry` button updating simulation state instantly.
         * 3D STL CAD Drag-and-Drop Dropzone.
    3. **`📁 Case Tree`:**
       * Full OpenFOAM directory tree inspection (`system/controlDict`, `fvSchemes`, `fvSolution`, `constant/transportProperties`, `0/U`, `0/p`).
       * Syntax-highlighted OpenFOAM dictionary editor.
       * "Check & Repair" syntax diagnostic tool.
       * 1-Click "Export ZIP" generating official OpenFOAM case directories.
    4. **`📝 History & Save`:**
       * Custom Simulation Project naming input and Save button.
       * Chronological modification timeline tracking AI Copilot interventions vs. Manual slider adjustments.
* **Layout Isolation:**
  * Styled with scoped CSS and custom scrollbars to prevent any text clipping or horizontal layout overflow.

#### 2. [`frontend/src/utils/projectStore.ts`](file:///c:/Users/ROSHNI/OneDrive/Documents/GitHub/openn_fOam/frontend/src/utils/projectStore.ts) *(New File)*
* **Hybrid Storage Architecture:**
  * Communicates with `/api/projects` for cloud/disk storage.
  * Maintains an offline fallback in browser `localStorage` (`openzess_projects_backup`) so simulations are preserved even without network access.

#### 3. [`frontend/src/types/cfd.ts`](file:///c:/Users/ROSHNI/OneDrive/Documents/GitHub/openn_fOam/frontend/src/types/cfd.ts)
* **Type Safety Additions:**
  * Added `SolidObstacleSpec` interface (`shape`, `cx`, `cy`, `size`, `aoa`).
  * Added `FluidMedium` type union and database properties (`seawater`, `water`, `air`, `co2`, `oil`, `ethanol`).
  * Added `SavedProjectSnapshot` contract.

#### 4. [`frontend/src/App.vue`](file:///c:/Users/ROSHNI/OneDrive/Documents/GitHub/openn_fOam/frontend/src/App.vue)
* **HUD & Viewport Layout:**
  * Updated top-level container styles, responsive flexbox layout, and active tab state synchronization.

#### 5. [`frontend/src/components/CfdThree3D.vue`](file:///c:/Users/ROSHNI/OneDrive/Documents/GitHub/openn_fOam/frontend/src/components/CfdThree3D.vue)
* **Three.js WebGL Flow Canvas:**
  * Real-time 3D scalar colormap surfaces, streamline particles, vorticity isosurfaces, and camera orbit controls.

---

### C. Build & Launch Tooling

#### 1. [`sync_and_launch.py`](file:///c:/Users/ROSHNI/OneDrive/Documents/GitHub/openn_fOam/sync_and_launch.py) *(New File)*
* Automatically synchronizes build artifacts between local folders and the server directory, eliminating manual file copies.

#### 2. [`LAUNCH_STUDIO.bat`](file:///c:/Users/ROSHNI/OneDrive/Documents/GitHub/openn_fOam/LAUNCH_STUDIO.bat) *(New File)*
* 1-click batch script for Windows users to launch backend, check dependencies, and open OpenZess Studio in the default browser.

#### 3. [`docs/tasks/PRD.md`](file:///c:/Users/ROSHNI/OneDrive/Documents/GitHub/openn_fOam/docs/tasks/PRD.md) & [`docs/tasks/progress.txt`](file:///c:/Users/ROSHNI/OneDrive/Documents/GitHub/openn_fOam/docs/tasks/progress.txt)
* Comprehensive task tracker and inter-agent synchronization protocol.

---

## 3. Step-by-Step Execution Journey

```mermaid
flowchart TD
    A[Step 1: Stale Cache Invalidation] --> B[Step 2: Sidebar UI Overhaul]
    B --> C[Step 3: CFD Physical Realism Upgrades]
    C --> D[Step 4: Custom Geometry & Obstacle Builder]
    D --> E[Step 5: Project Persistence & Disk Save]
    E --> F[Step 6: Rust vs Python Architecture Clarity]
    F --> G[Step 7: Production Build & Health Verification]
```

### Step 1: Solving the Localhost Stale Caching Bug
* **Symptom:** Edits saved to Vue components did not appear when refreshing `http://localhost:8000/studio/index.html`.
* **Root Cause:** Browser aggressive asset caching coupled with backend serving from a secondary path.
* **Resolution:**
  1. Updated `backend/app.py` to check modification times on startup and run `npm run build` if `src` is newer than `dist`.
  2. Injected strict `no-cache, no-store, must-revalidate` HTTP headers on all static routes.
  3. Locked `local_dist` as priority #1 over any external folders.

### Step 2: Sidebar Controls UI Overhaul
* **Symptom:** Sliders and case tree were squeezed into a narrow 2-column layout causing overlapping text.
* **Resolution:**
  1. Redesigned `SidebarControls.vue` with 4 full-width tabs: `🌊 Physics`, `🧱 Geometry`, `📁 Case Tree`, `📝 History`.
  2. Added responsive cards with fluid physical properties ($\rho, \nu$).
  3. Created an isolated, non-colliding layout with dedicated scrolling.

### Step 3: Upgrading Physical Realism to OpenFOAM Standards
* **Implementation:**
  1. Added `seawater` medium ($\rho = 1025\ \text{kg/m}^3$) for maritime/submarine simulation.
  2. Implemented cavitation index $\sigma$ computation for high-speed underwater archetypes.
  3. Added hydrostatic pressure gradient calculation $\rho g h$.
  4. Connected dynamic aerodynamic force calculation ($C_L, C_D$) to the PINN AI solver.

### Step 4: Adding the Custom Geometry & Obstacle Builder
* **Implementation:**
  1. Created UI controls for Cylinder, Square, Plate, and NACA Airfoil in the Geometry tab.
  2. Added position ($X, Y$), scale, and angle of attack sliders.
  3. Built `build_obstacle_mask` in `backend/solver.py` with NACA 4-digit analytical curves.
  4. Implemented `parse_dict_overrides` so direct text edits to OpenFOAM dictionary files override solver parameters live.

### Step 5: Implementing Project Persistence
* **Implementation:**
  1. Created `backend/projects.py` with REST endpoints (`/api/projects/save`, `/api/projects/load`).
  2. Implemented disk-backed JSON storage in `backend/saved_projects/`.
  3. Created `frontend/src/utils/projectStore.ts` with automatic `localStorage` mirror.

### Step 6: Clarifying Rust vs. Python Division of Work
* **Division Established:**
  * **Rust Sidecar (`rust-sidecar/`):** High-speed SIMD Rayon Navier-Stokes inner loop, 3D Poisson pressure solver, $k$-$\epsilon$ eddy viscosity calculation, streamline particle integration.
  * **Python FastAPI (`backend/`):** HTTP API, OpenFOAM case synthesis, `snappyHexMeshDict` generation, AI Copilot reasoning, SciPy sparse fallback solver.
  * **Vue 3 Frontend (`frontend/`):** WebGL Three.js rendering, interactive controls, project management.

---

## 4. System Verification Status

| Component | Status | Verification Detail |
| :--- | :---: | :--- |
| **Frontend Compilation** | ✅ PASS | Vite v8.2.0 build succeeded in 1.07s; 0 TypeScript errors |
| **Backend API Server** | ✅ PASS | FastAPI running on `http://127.0.0.1:8000` with hot-reload |
| **Anti-Cache Headers** | ✅ PASS | Verified `no-cache, no-store, must-revalidate` in HTTP response |
| **Project Endpoints** | ✅ PASS | `/api/projects` responding with 200 OK |
| **Solver Fallback** | ✅ PASS | SciPy sparse solver active and ready |

---

*Authored by Antigravity Agent for OpenZess Studio (UR2627GEN317).*
