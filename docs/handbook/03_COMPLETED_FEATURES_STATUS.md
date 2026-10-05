# ✅ Completed Features & Current Status

This document summarizes all modules, physical equations, and UI components that are fully implemented and verified in the current build.

---

## 1. Feature Status Dashboard

| Module | Sub-Feature | Status | Verification Detail |
| :--- | :--- | :---: | :--- |
| **Pipeline** | Stale Cache Prevention | ✅ 100% | Injected `no-cache, no-store, must-revalidate` HTTP headers + auto-build check on startup. |
| **Pipeline** | Path Resolution | ✅ 100% | Local `frontend/dist` prioritised over any external folders. |
| **UI / UX** | 4-Tab Sidebar Controls | ✅ 100% | Full-width tabs for Physics, Geometry, Case Tree, and History. |
| **Physics** | Fluid Medium Database | ✅ 100% | Air, Water, Seawater ($\rho = 1025$), CO2, Oil, Ethanol. |
| **Physics** | Ocean Hydrodynamics | ✅ 100% | Hydrostatic gradient $\rho g h$ and Cavitation Index $\sigma$ computed. |
| **Physics** | Dynamic Force Integration | ✅ 100% | $C_L$ and $C_D$ computed across obstacle surface cells in PINN mode. |
| **Geometry** | Archetype Selector | ✅ 100% | Submarine, Drone, Airfoil, F1, Venturi, Dam, Cylinder. |
| **Geometry** | Custom Obstacle Builder | ✅ 100% | Cylinder, Square, Plate, NACA Airfoil with live $X, Y, \text{scale}, \alpha$ controls. |
| **OpenFOAM** | Dictionary Ingestion | ✅ 100% | `parse_dict_overrides` applies user dictionary edits to solver timestep, $\nu$, and inflow. |
| **OpenFOAM** | 1-Click ZIP Exporter | ✅ 100% | Bundles complete OpenFOAM case directories for Linux cluster execution. |
| **Persistence**| Project Save & Load | ✅ 100% | `/api/projects` disk storage in `backend/saved_projects/` + `localStorage` backup. |
| **Fallback** | SciPy Sparse Solver | ✅ 100% | Automatically handles simulation when Rust sidecar is offline. |

---

## 2. Key Highlights of Completed Work

### 1. Invalidation of Localhost Stale Caching
* **Problem:** When editing Vue components in `frontend/src`, saving the file and refreshing the browser on `http://localhost:8000` often displayed the old version due to browser disk caching and asynchronous build sync.
* **Fix:** 
  * Added `_ensure_fresh_frontend_build()` in `backend/app.py` that checks modification timestamps and re-runs `npm run build` if source files are newer.
  * Added ASGI middleware adding `Cache-Control: no-cache, no-store, must-revalidate, max-age=0` and unique `X-OpenZess-Build-Time` headers to every static file response.

### 2. Full Sidebar Restructuring
* **Problem:** Previous layout crammed sliders, fluid options, and the OpenFOAM file tree into a 2-column sidebar that caused text truncation and overlapping sliders.
* **Fix:**
  * Rebuilt `SidebarControls.vue` with 4 full-width dedicated tabs:
    1. **`🌊 Physics & Water`:** Velocity, AoA, Vorticity, Temperature, Fluid cards with density and viscosity, Gravity presets.
    2. **`🧱 Geometry & Custom Builder`:** 7 archetype templates + interactive custom obstacle designer (Cylinder, Square, Plate, NACA Airfoil) + STL dropzone.
    3. **`📁 Case Tree`:** Syntax-highlighted OpenFOAM dictionary editor, syntax validator, and ZIP export.
    4. **`📝 History & Save`:** Project naming, save snapshot, and modification timeline.

### 3. OpenFOAM Physical Parity & Maritime Realism
* Added `seawater` fluid medium ($\rho = 1025\ \text{kg/m}^3$, $\nu = 1.05 \times 10^{-6}\ \text{m}^2/\text{s}$).
* Implemented the **Cavitation Index** $\sigma = \frac{p_\infty - p_v}{0.5 \rho U_\infty^2}$ to predict vapor bubble formation around submarine hulls and hydrofoils.
* Implemented **Hydrostatic Pressure Gradients** $\Delta p = \rho g h$ for depth-dependent pressure distribution.
* Added dynamic aerodynamic/hydrodynamic force calculation ($C_L$ and $C_D$) to the PINN solver.

### 4. Interactive Custom Geometry Builder
* Users can position and size custom shapes on the fly:
  * Adjust center coordinates $X$ and $Y$ ($10\%$ to $90\%$ of domain).
  * Scale the object from $0.05$ to $0.50$ of domain height.
  * Adjust angle of attack $\alpha$ from $-45^\circ$ to $+45^\circ$.
* Implemented analytical NACA 4-digit airfoil equation in `backend/solver.py` for cambered/symmetric aerodynamic profiles.

### 5. Disk Project Persistence
* Implemented `/api/projects/save` and `/api/projects/load` in `backend/projects.py`.
* Stores complete case setups (medium, inflow speed, custom obstacle specs, dictionary overrides, notes) as JSON files in `backend/saved_projects/`.
* Mirrored on the client via `frontend/src/utils/projectStore.ts` using `localStorage` for offline protection.
