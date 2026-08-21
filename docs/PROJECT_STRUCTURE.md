# 🏛️ OpenZess 3D Studio — Complete Project Structure & System Architecture

This document provides a detailed breakdown of the entire **OpenZess 3D** codebase, explaining the role of every directory, module, physical solver, and AI layer.

---

## 📂 Directory Tree & File Inventory

```
openn_fOam/
│
├── main.py                         # 🚀 Launcher: Starts FastAPI & auto-opens Web Studio
├── requirements.txt                # 📦 Python backend dependencies
├── README.md                       # 📖 General overview & GitHub landing page
├── PROJECT_STRUCTURE.md            # 🏛️ Full architectural map (This file)
│
├── backend/                        # 🧠 Python Aerothermal & AI Physics Engine
│   ├── app.py                      # FastAPI REST routes & WebSocket (/ws/simulate_3d)
│   ├── mesh_3d.py                  # 3D Cartesian Grid & 2D Image-to-3D Voxelizer
│   ├── solver_3d.py                # 3D Navier-Stokes, Pressure Poisson & Thermal Energy Solver
│   ├── ai_vision_engine.py         # AI Vision classifier, preset catalog & NLP Co-Pilot
│   ├── openfoam_generator_3d.py    # OpenFOAM v2312 Case Generator & ZIP Exporter
│   └── vtk_writer_3d.py            # ParaView 3D Legacy Structured Points (.vtk) Exporter
│
└── frontend/                       # 🌐 Vue 3 + TypeScript + Three.js Web Studio
    ├── index.html                  # HTML5 application root entry
    ├── package.json                # Frontend packages (Vue 3, Three.js, Chart.js)
    ├── vite.config.ts              # Vite bundling & development server configuration
    │
    └── src/
        ├── App.vue                 # 🎛️ Master application state & WebSocket coordinator
        ├── types/cfd.ts            # 📐 TypeScript interfaces for 3D physics & AI models
        │
        ├── components/
        │   ├── HeaderNavbar.vue    # Top bar: Field selector, colormaps & export buttons
        │   ├── SidebarControls.vue # Left panel: Tabs for AI Co-Pilot, Physics, & Dicts
        │   ├── AiCopilotChat.vue   # 🤖 Photo dropzone, presets & conversational AI chat
        │   ├── CfdThree3D.vue      # 🌌 3D Three.js scene: Streamlines, Cut-planes & Probing
        │   ├── OpenFoamDictEditor.vue # 📄 Live OpenFOAM dictionary inspector & editor
        │   └── ResidualChart.vue   # 📈 Logarithmic convergence residual monitor
        │
        └── utils/
            ├── colormaps.ts        # 🎨 Palettes: Turbo, Coolwarm, Inferno, Jet, Viridis
            └── openfoamDicts3d.ts  # 📑 OpenFOAM v2312 3D dictionary templates
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

### Layer 2: 3D Geometry & Voxelizer (`backend/mesh_3d.py`)
- Constructs structured 3D Cartesian meshes of size $(N_x \times N_y \times N_z)$ across domain spans $(L_x, L_y, L_z)$.
- **Image-to-3D Extrusion**: Takes 2D image silhouettes and depth maps, extrudes them through the transverse $Y$-axis, and generates a 3D boolean obstacle mask (`obstacle_mask[i, j, k]`).
- **Geometric Primitives**: Built-in 3D solid constructors for:
  - `table`: Tabletop plate with 4 cylindrical legs.
  - `chair`: Seat pan, backrest, and 4 legs.
  - `submarine`: Streamlined ellipsoid hull, conning tower sail, and rudder planes.
  - `car`: Aerodynamic body with windshield slope and cabin.
  - `radiator`: Heat-emitting wall/floor radiator.
  - `server_rack`: High-density electronics cabinet with thermal heat flux.

---

### Layer 3: 3D Aerothermal CFD Physics (`backend/solver_3d.py`)
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

### Layer 4: AI Vision & Conversational Co-Pilot (`backend/ai_vision_engine.py`)
- Analyzes uploaded user photos or preset choices.
- Translates natural language requests into physical parameter updates (*"Increase inlet speed to 4 m/s"*, *"Make the heater 60°C"*).
- Eliminates manual OpenFOAM dictionary coding by auto-synchronizing domain boundary conditions and meshing parameters.

---

### Layer 5: Production Exporters (`backend/openfoam_generator_3d.py` & `backend/vtk_writer_3d.py`)
- **OpenFOAM Generator**: Produces a valid, ready-to-run OpenFOAM directory suite (`system/controlDict`, `system/blockMeshDict`, `system/fvSchemes`, `system/fvSolution`, `constant/transportProperties`, `constant/g`, `0/U`, `0/T`, `0/p_rgh`) and bundles it into `openfoam_case_3d.zip`.
- **ParaView VTK Writer**: Produces `openzess_3d_simulation.vtk` containing 3D Velocity vectors $(u, v, w)$, Pressure $p$, Temperature $T$, Speed magnitude $\|U\|$, and solid obstacle masks.

---

### Layer 6: 3D Web Studio UI (`frontend/src/`)
- **`App.vue`**: Coordinates WebSocket communication, manages global state, and connects the sidebar and 3D viewport.
- **`AiCopilotChat.vue`**: Photo upload dropzone, quick preset chips, detection summary cards, and interactive AI chat.
- **`CfdThree3D.vue`**: Three.js WebGL viewport rendering:
  - 3D Room / Tunnel wireframe box with floor grid.
  - 3D Reconstructed obstacle with thermographic/pressure coloring.
  - 3D Particle streamlines tracing fluid paths around the body.
  - Dynamic 2D contour cut-planes on **XY (Top)**, **XZ (Side)**, or **YZ (Front)**.
  - 3D raycast flow probe displaying local Velocity, Temperature, and Pressure.
- **`OpenFoamDictEditor.vue`**: Real-time dictionary inspector with one-click copy and ZIP download.
- **`ResidualChart.vue`**: Real-time logarithmic residual convergence plot.
