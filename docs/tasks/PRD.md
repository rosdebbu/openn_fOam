# OpenZess Studio — Product Requirements Document (PRD)

**Project Identifier:** UR2627GEN317  
**Platform:** High-Performance Web-Based OpenFOAM CFD Platform & AI Co-Engineer  
**Benchmark Target:** OpenFOAM Foundation v2406 (`simpleFoam`, `buoyantBoussinesqSimpleFoam`, `interFoam`)  
**Status:** In Active Sprint & Overnight Autonomous Development

---

## 🏛️ Architectural Division: Rust vs. Python Division of Work

To compete directly with native OpenFOAM while maintaining fluid 60 FPS in a web browser without bottlenecks:

| Component / Layer | Engine | Implementation Rationale |
| :--- | :--- | :--- |
| **High-Speed Numerical Inner Loop** | **Rust Sidecar (`rust-sidecar/`)** | Bare-metal CPU execution using Rayon SIMD, multi-threaded Red-Black Gauss-Seidel / Conjugate Gradient Poisson pressure solvers, 3D upwind advection, and fast stencil updates with zero GIL interruptions. |
| **Real-Time Streamline & Vortex Engine** | **Rust + Three.js WebGL** | RK4 particle tracer advection, Q-Criterion vortex core identification, and binary WebSocket streaming to the browser (`/ws/simulate_3d`). |
| **High Reynolds Turbulence Models** | **Rust Core** | $k$-$\epsilon$ and Smagorinsky sub-grid scale (LES) eddy viscosity $\nu_t$ calculation to prevent artificial damping and enable realistic flow separation over submarines, airfoils, and drones. |
| **API & Session Orchestrator** | **Python (FastAPI)** | High-level HTTP/WebSocket orchestration, client connection pools, parameter validation, and process watchdog. |
| **OpenFOAM Case Generation & Packaging** | **Python (`backend/openfoam_export.py`)** | Exact file synthesis for `system/controlDict`, `system/fvSchemes`, `system/fvSolution`, `constant/transportProperties`, `0/U`, `0/p`, and `snappyHexMeshDict` into downloadable `.zip` bundles ready for Linux HPC clusters. |
| **AI Simulation Copilot & LLM Reasoning** | **Python (`backend/ai_predictor.py` + Frontend Copilot)** | Natural-language prompt parsing, automated boundary condition assignment, CFD sanity checking, and multi-provider LLM integrations (Gemini, Claude, DeepSeek). |
| **CAD Mesh Ingestion & Voxelization** | **Python + Rust Hybrid** | Python parses incoming `.stl` and `.obj` geometry triangles; Rust generates high-resolution 3D immersed boundary voxel masks. |

---

## 🎯 Epics & Task Backlog

### Phase 1: Core Foundation & Stability (Completed)
- [x] Implement 3D incompressible Navier–Stokes solver with Chorin's fractional-step projection method.
- [x] Integrate SciPy banded CSR sparse linear algebra for accelerated Poisson pressure solving.
- [x] Implement Rayon-accelerated bare-metal Rust sidecar with Axum WebSocket micro-service on port 8081.
- [x] Three.js 3D WebGL viewport with continuous streamlines, vector glyphs, and orthogonal slicing (XY, XZ, YZ).
- [x] Fix localhost caching bug: prioritize local `frontend/dist` and inject strict `no-cache` / `no-store` headers.

---

### Phase 2: OpenFOAM-Calibrated Physics Realism & Turbulence
- [ ] **Task 2.1: Sub-Grid Turbulence Modeling ($k$-$\epsilon$ & Turbulent Viscosity $\nu_t$)**
  - Add eddy viscosity $\nu_t$ to the momentum equations: $\nu_{\text{eff}} = \nu_{\text{laminar}} + \nu_t$.
  - Compute vorticity and velocity gradients for separation wakes behind submarines, drone rotors, and airfoils.
  - Acceptance Criteria: Bluff body wake produces oscillating von Kármán vortex shedding rather than creeping laminar flow.

- [ ] **Task 2.2: Realistic Submarine Hydrodynamics & Cavitation Physics**
  - Implement cavitation index $\sigma = \frac{p_\infty - p_v}{\frac{1}{2}\rho U^2}$ field display where $p_v \approx 2338\text{ Pa}$ (water vapor pressure).
  - Add ocean salinity / seawater density ($\rho = 1025\text{ kg/m}^3$) and hydrostatic pressure gradients ($p(z) = \rho g z$).
  - Acceptance Criteria: Submarine hull shows localized low-pressure cavitation warning hotspots around the sail and propeller tips.

- [x] **Task 2.3: Left Sidebar Layout Restructuring (Manageable Physics Tabs)**
  - Reorganized `SidebarControls.vue` into four clean, full-width tabs:
    1. **Medium & Environment**: Fluid substance (Water, Air, Seawater, Oil), Gravity, Inflow speed, and fluid properties.
    2. **Geometry & Archetype**: Direct 1-click archetype selector (Submarine, Drone, Airfoil, F1, Venturi, Dam, Cylinder) + 3D STL dropzone.
    3. **OpenFOAM Files & Export**: Clean directory tree with `system/`, `constant/`, `0/` and 1-click Case ZIP export.
    4. **History & Save**: Custom simulation naming, AI vs. manual modification timeline, and snapshot restore.
  - Acceptance Criteria: Left sidebar removes cluttered nested scrollbars and enables instant 1-click physics navigation.

- [x] **Task 2.4: Dual AI + Manual Simulation Generation (The Drone / Custom Workflow)**
  - Implemented bidirectional synchronization between AI Copilot and Manual OpenFOAM controls.
  - Added Custom Geometry Builder allowing users to build and parameterize their own solid obstacles (Cylinder, Square, Plate, Airfoil) with position, scale, and AoA controls.
  - Added `parse_dict_overrides()` to parse OpenFOAM dimensioned scalar syntax from user-edited dictionaries (`deltaT`, `nu`, `inlet_velocity`) and apply them to the running solver.
  - Implemented Project Persistence REST API (`/api/projects/save`, `/api/projects/load`) in `backend/projects.py` with offline `localStorage` fallback in `projectStore.ts`.
  - Upgraded PINN AI mode to compute real integrated aerodynamic forces ($C_d$, $C_l$) and dynamic obstacle masking.
  - Acceptance Criteria: Users can create custom geometries manually or via AI, edit dictionary parameters, and persist named project snapshots.

---

### Phase 3: CAD Ingestion & Cluster Deployment
- [ ] **Task 3.1: 3D STL CAD Upload & SnappyHexMesh Automation**
  - Allow users to drop `.stl` surface CAD files onto the viewport.
  - Automatically write OpenFOAM `system/snappyHexMeshDict` with surface refinement levels.
  - Acceptance Criteria: Dropping an STL produces an immersed 3D solid obstacle and exportable OpenFOAM mesh scripts.

- [ ] **Task 3.2: Full Rust Sidecar Integration & Binary Buffer Exchange**
  - Enable direct binary Float32Array streaming over WebSockets from Rust to Three.js for 60 FPS performance on $64^3$ grids.
