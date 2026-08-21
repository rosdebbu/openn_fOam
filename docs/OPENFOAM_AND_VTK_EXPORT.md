# 📦 OpenFOAM & ParaView 3D Data Export

OpenZess ensures that all simulations can be transitioned seamlessly into industry-standard open-source CFD toolchains: **OpenFOAM** and **ParaView**.

---

## 📑 1. OpenFOAM Case ZIP Generation

When you click **📦 OpenFOAM Case (.zip)**, OpenZess compiles a production-ready OpenFOAM v2312 directory structure:

```
openfoam_case_3d/
├── Allrun                      # Bash script to run blockMesh & solver
├── Allclean                    # Bash script to reset case
├── system/
│   ├── controlDict             # Solver runtime settings & write interval
│   ├── blockMeshDict           # Structured hex mesh matching room Lx × Ly × Lz
│   ├── fvSchemes               # Discretization schemes (Gauss linear, bounded upwind)
│   └── fvSolution              # Linear solvers (GAMG for p_rgh, smoothSolver for U & T)
├── constant/
│   ├── transportProperties     # Viscosity nu, thermal expansion beta, Prandtl Pr
│   └── g                       # Gravity vector (0 0 -9.81)
└── 0/
    ├── U                       # Velocity field boundary conditions (inlet, outlet, walls)
    ├── T                       # Temperature field boundary conditions (inlet, heat source, walls)
    └── p_rgh                   # Buoyant pressure field boundary conditions (fixedFluxPressure)
```

### Running the Case in Native OpenFOAM:
```bash
# Extract the ZIP
unzip openfoam_case_3d.zip
cd openfoam_case_3d

# Execute standard OpenFOAM workflow
./Allrun
```

---

## 📊 2. ParaView 3D VTK Export

When you click **📊 ParaView 3D (.vtk)**, OpenZess produces a standard **Legacy VTK Structured Points** dataset (`openzess_3d_simulation.vtk`):

### Fields Exported in VTK:
- **`VECTORS velocity float`**: 3D Velocity vector field $\vec{U} = (u, v, w)$ for Stream Tracers and Glyph vector arrows.
- **`SCALARS pressure float 1`**: Pressure scalar field $p$ (Pa).
- **`SCALARS temperature float 1`**: Temperature scalar field $T$ (K).
- **`SCALARS speed float 1`**: Velocity magnitude $\|U\|$ (m/s).
- **`SCALARS obstacle_mask int 1`**: Solid obstacle boolean mask (0 = fluid, 1 = obstacle body).

### Opening in ParaView:
1. Launch **ParaView**.
2. Click **File $\to$ Open...** and select `openzess_3d_simulation.vtk`.
3. Click **Apply**.
4. Use filters like **Stream Tracer**, **Contour / Isosurface**, or **Slice** to post-process your 3D flow fields.
