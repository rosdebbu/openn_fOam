# 🏛️ OpenZess 3D Studio — Complete Project Structure & System Architecture

This document provides a detailed breakdown of the entire **OpenZess 3D** codebase, explaining the role of every directory, module, physical solver, and AI layer.

---

## 📂 Directory Tree & File Inventory

```
openn_fOam/
│
├── main.py                     # 🚀 Launcher: Starts FastAPI & auto-opens Web Studio
├── requirements.txt            # 📦 Python backend dependencies
├── README.md                   # 📖 GitHub landing page & quick-start guide
├── .gitignore                  # 🧹 Ignores bytecode, tool caches, builds & secrets
│
├── backend/                    # 🧠 Python Aerothermal & AI Physics Engine
│   ├── app.py                  # FastAPI REST routes & WebSocket simulation streaming
│   ├── mesh.py                 # Structured Cartesian grid generator & obstacle masks
│   ├── solver.py               # Navier-Stokes, Pressure Poisson & Thermal solver (SciPy sparse-accelerated)
│   ├── ai_predictor.py         # ⚡ Instant PINN surrogate physics prediction
│   └── vtk_writer.py           # ParaView legacy structured-points (.vtk) exporter
│
├── frontend/                   # 🌐 Vue 3 + TypeScript + Three.js + Tailwind Web Studio
│   ├── index.html              # HTML5 application root entry
│   ├── package.json            # Frontend packages (Vue 3, Three.js, Chart.js, Lucide)
│   ├── vite.config.ts          # Vite bundling configuration
│   │
│   ├── public/
│   │   ├── favicon.svg         # App favicon
│   │   └── icons.svg           # Shared SVG icon sprite
│   │
│   └── src/
│       ├── main.ts             # Vue application bootstrap
│       ├── App.vue             # 🎛️ Master application coordinator (Split-Screen Studio)
│       ├── style.css           # Global styles & OKLCH design tokens
│       ├── types/cfd.ts        # 📐 TypeScript interfaces for CFD cases & 3D physics
│       │
│       ├── components/
│       │   ├── HeaderNavbar.vue      # Top bar: brand, runtime widget, playback & export controls
│       │   ├── SidebarControls.vue   # Side panel: simulation parameters & mode toggles
│       │   ├── CfdCanvas2D.vue       # 🖼️ 2D HTML5 Canvas viewport renderer
│       │   ├── CfdThree3D.vue        # 🌌 Three.js WebGL 3D viewport renderer
│       │   ├── ResidualChart.vue     # 📈 Logarithmic convergence residual monitor (Chart.js)
│       │   ├── AiAssistant.vue       # 🤖 AI Co-Pilot conversational assistant panel
│       │   ├── OpenFoamDictEditor.vue# 📑 OpenFOAM dictionary code editor
│       │   └── HelloWorld.vue        # Vite scaffold placeholder component
│       │
│       └── utils/
│           ├── colormaps.ts      # 🎨 Scientific colormaps (thermal plume, Turbo, Viridis)
│           └── openfoamDicts.ts  # 📑 OpenFOAM dictionary case templates
│
├── docs/                       # 📚 Architecture, physics & design documentation
│   └── assets/                 # Documentation images
│
├── saved_chats/                # 💾 Simulation session archives & design mockups
│   └── assets/                 # UI mockup images & visual references
│
└── graphify-out/               # 🕸️ Codebase dependency-graph reports (agent tooling output)
```

---

## 🧩 Architectural Breakdown by Layer

### Layer 1: Launcher & Server (`main.py` & `backend/app.py`)
- **`main.py`**:
  - Initializes the application.
  - Spawns a background thread to launch the user's default browser at `http://localhost:8000/studio/index.html`.
  - Runs the `uvicorn` server hosting `backend.app:app`.
- **`backend/app.py`**:
  - **`POST /api/ai/vision-analyze`**: Takes an uploaded image (or hint), extracts the 2D silhouette, detects the object class, and computes bounding box dimensions ($L \times W \times H$).
  - **`POST /api/ai/chat`**: Natural language processing endpoint for the AI Co-Pilot.
  - **`GET /api/presets`**: Returns catalog of pre-configured 3D cases (Submarine, Table, Chair, Car, Radiator, Server Rack).
  - **`GET /api/export/vtk`**: Generates and streams a 3D `.vtk` file for ParaView.
  - **`GET /api/export/openfoam-zip`**: Generates and streams a complete OpenFOAM case `.zip` folder.
  - **`WebSocket /ws/simulate_3d`**: Real-time streaming channel for 3D simulation frames, residuals, and cross-section slices.

---

### Layer 2: Mesh Generation (`backend/mesh.py`)
- Constructs structured Cartesian meshes across the computational domain.
- **Image-to-3D Extrusion**: Takes 2D image silhouettes and depth maps, extrudes them through the transverse $Y$-axis, and generates a 3D boolean obstacle mask (`obstacle_mask[i, j, k]`).
- **Geometric Primitives**: Built-in 3D solid constructors for:
  - `table`: Tabletop plate with 4 cylindrical legs.
  - `chair`: Seat pan, backrest, and 4 legs.
  - `submarine`: Streamlined ellipsoid hull, conning tower sail, and rudder planes.
  - `car`: Aerodynamic body with windshield slope and cabin.
  - `radiator`: Heat-emitting wall/floor radiator.
  - `server_rack`: High-density electronics cabinet with thermal heat flux.

---

### Layer 3: Aerothermal CFD Physics (`backend/solver.py`)
Solves the coupled Navier-Stokes and thermal convection-diffusion equations:

1. **3D Momentum (Navier-Stokes)**:
   $$\frac{\partial \vec{u}}{\partial t} + (\vec{u} \cdot \nabla) \vec{u} = -\frac{1}{\rho}\nabla p + \nu \nabla^2 \vec{u} + \vec{g} \beta (T - T_0)$$
2. **3D Pressure Poisson Equation**:
   $$\nabla^2 p = \frac{\rho}{\Delta t} \nabla \cdot \vec{u}^*$$
3. **3D Thermal Energy Transport**:
   $$\frac{\partial T}{\partial t} + (\vec{u} \cdot \nabla) T = \alpha \nabla^2 T + S_T$$

- **Dual Execution Modes**:
  - **⚡ Instant 3D PINN AI**: Solves steady-state potential flow with stagnation pressure, wake vortex deflection, and thermal buoyancy plume in $<50$ ms.
  - **🔬 3D Iterative CFD Solver**: High-precision fractional-step time-marching with boundary condition enforcement.

---

### Layer 4: AI Surrogate Physics (`backend/ai_predictor.py`)
- Provides instant (<50 ms) PINN-based flow-field prediction as an alternative to iterative solving.
- Translates simulation inputs into pre-trained surrogate physics solutions used by `backend/app.py` endpoints.
- Eliminates long solver wait times for quick design iteration directly in the Web Studio UI.

---

### Layer 5: Production Exporters (`backend/vtk_writer.py` & `frontend/src/utils/openfoamDicts.ts`)
- **ParaView VTK Writer**: Produces legacy `.vtk` files containing velocity vectors $(u, v)$, pressure $p$, temperature $T$, speed magnitude $\|U\|$, and solid obstacle masks via the `/api/export/vtk` endpoint.
- **OpenFOAM Case Templates**: Complete OpenFOAM dictionary suites (`system/controlDict`, `system/fvSchemes`, `constant/transportProperties`, `0/U`, `0/T`, `0/p`, etc.) generated by `openfoamDicts.ts` in the frontend for one-click OpenFOAM case export.

---

### Layer 6: 3D Web Studio UI (`frontend/src/`)
- **`App.vue`**: Coordinates WebSocket communication, manages global state, and coordinates the Split-Screen layout.
- **`HeaderNavbar.vue`**:
  - Brand Logo with isometric cube gradient (`linear-gradient(135deg, oklch(43.8% 0.218 303.724), oklch(40.5% 0.101 131.063))`).
  - Google Colab-style runtime widget (`✓ RAM [===] Disk [===] ▾`) with `oklch(20.5% 0 none)` button surface and dropdown connection menu.
  - Simulation playback controls (`▶ Run`, `⏸ Pause`, `↺ Reset`) and one-click **Export OpenFOAM Case (`.ZIP` / `.VTK`)**.
- **`OpenFoamCaseHub.vue`**:
  - Left panel: Dual mode toggle (`[ 🤖 AI Copilot ]` vs `[ ⚙️ Manual OpenFOAM ]`).
  - Full OpenFOAM case tree (`system/`, `constant/`, `0/`), boundary patches, and physical property sliders.
  - Photo dropzone for instant 2D image-to-3D voxelization and contextual OpenFOAM.org documentation tooltips.
- **`CfdViewport3D.vue`**:
  - Right 3D Viewport: Hardware-accelerated Three.js WebGL scene.
  - 3D Volumetric thermal plume (translucent sapphire billowing edges $\to$ golden core) and animated velocity streamlines.
  - Moveable 2D Cut-Plane slice heatmaps on $XY/XZ/YZ$ and interactive **Flow Probe HUD tooltip**.
- **`ResidualMonitor.vue`**: Real-time logarithmic residual convergence plot ($Ux, Uy, Uz, p, T$) powered by Chart.js.

