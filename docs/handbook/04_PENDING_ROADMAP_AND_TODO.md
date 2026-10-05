# 🗺️ Pending Roadmap & TODO Guide for Collaborators

This document details the exact remaining tasks, priorities, and implementation guides so team members and contributors know exactly where to pick up development.

---

## 1. Prioritized Roadmap Overview

```mermaid
gantt
    title OpenZess Studio Development Roadmap
    dateFormat  YYYY-MM-DD
    section Phase 1 (Completed)
    Cache-Busting & Path Resolution   :done, 2026-10-01, 2026-10-04
    Sidebar 4-Tab Overhaul            :done, 2026-10-04, 2026-10-05
    Custom Geometry Builder & Persist :done, 2026-10-05, 2026-10-05
    section Phase 2 (Current Focus)
    Task 2.1: k-epsilon Turbulence    :active, 2026-10-05, 2026-10-08
    Task 2.2: 3D STL Ingestion        :2026-10-08, 2026-10-12
    Task 2.5: UI Project Store Wire   :2026-10-12, 2026-10-14
    section Phase 3 (Advanced CFD)
    Two-Phase VOF Free Surface        :2026-10-15, 2026-10-22
    snappyHexMesh Live Generation     :2026-10-22, 2026-10-30
```

---

## 2. Detailed Task Breakdown

### 🎯 Task 2.1: Sub-Grid Turbulence Modeling ($k$-$\epsilon$ / Mixing Length)
* **Objective:** Replace purely laminar viscosity with effective turbulent viscosity:
  $$\nu_{\text{eff}} = \nu_{\text{laminar}} + \nu_t$$
* **Current State:** The solver runs laminar Navier-Stokes with effective molecular viscosity.
* **What Needs to be Done:**
  1. In `backend/solver.py`, implement Prandtl mixing-length or 2-equation $k$-$\epsilon$ model:
     $$\nu_t = C_\mu \frac{k^2}{\epsilon}$$
     where $C_\mu = 0.09$.
  2. For high Reynolds number flows ($\text{Re} > 10^5$), add wall functions for velocity near solid boundaries:
     $$u^+ = \frac{1}{\kappa} \ln(y^+) + B$$
  3. Expose a **Turbulence Model** dropdown in `SidebarControls.vue` (`Laminar`, `Mixing Length`, `k-epsilon RANS`).
  4. Write turbulence kinetic energy $k$ and dissipation $\epsilon$ into exported OpenFOAM files (`0/k`, `0/epsilon`, `constant/turbulenceProperties`).

---

### 🎯 Task 2.2: 3D STL CAD Surface Ingestion & Voxel Masking
* **Objective:** Enable users to drag-and-drop any standard `.stl` CAD file and immediately run simulations around the 3D geometry.
* **Current State:** The drag-and-drop zone in `SidebarControls.vue` accepts files, but backend voxelization is pending.
* **What Needs to be Done:**
  1. In `backend/solver.py`, add an STL parser that reads ASCII and Binary STL triangle facets.
  2. Implement Ray-Casting or Signed Distance Field (SDF) voxelization to generate a boolean 3D obstacle mask on the structured grid.
  3. In `backend/openfoam_export.py`, generate the corresponding `system/surfaceFeatureExtractDict` and `system/snappyHexMeshDict` pointing to the uploaded geometry in `constant/triSurface/`.

---

### 🎯 Task 2.5: UI Project Store Wiring
* **Objective:** Connect the "Save" and "Load" buttons in `SidebarControls.vue`'s `History & Save` tab to `projectStore.ts`.
* **Current State:** The backend API (`/api/projects`) and client store (`projectStore.ts`) are 100% complete and tested; the UI buttons just need the `@click="saveCurrentProject"` hook.
* **What Needs to be Done:**
  1. In `SidebarControls.vue`, import `projectStore`.
  2. Bind the text input to project name state.
  3. Call `projectStore.saveProject()` on button click, display a success toast, and refresh the project list dropdown.

---

### 🎯 Task 3.1: Two-Phase / Multi-Phase Volume-of-Fluid (VOF)
* **Objective:** Model air-water interfaces with surface tension for Dam Break and Submarine surface wake simulations.
* **What Needs to be Done:**
  1. Track phase fraction $\alpha \in [0, 1]$ (where $\alpha = 1$ is liquid water and $\alpha = 0$ is air):
     $$\frac{\partial \alpha}{\partial t} + \nabla \cdot (\alpha \mathbf{u}) = 0$$
  2. Compute mixture density and viscosity:
     $$\rho = \alpha \rho_{\text{water}} + (1 - \alpha) \rho_{\text{air}}$$
     $$\mu = \alpha \mu_{\text{water}} + (1 - \alpha) \mu_{\text{air}}$$
  3. Export case as `interFoam` / `multiphaseInterFoam` case setup.

---

## 3. Summary of How You Can Help

If you are picking up work on this repo, pick one of the items above:
1. **If you love physics & numerics:** Take **Task 2.1 (Turbulence Modeling)** in `backend/solver.py`.
2. **If you love CAD & 3D geometry:** Take **Task 2.2 (STL Voxelization)**.
3. **If you love frontend polish:** Take **Task 2.5 (UI Button wiring)** in `SidebarControls.vue`.
