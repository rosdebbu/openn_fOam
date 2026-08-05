# Graph Report - openn_fOam  (2026-07-31)

## Corpus Check
- 7 files · ~7,476 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 39 nodes · 57 edges · 7 communities detected
- Extraction: 75% EXTRACTED · 25% INFERRED · 0% AMBIGUOUS · INFERRED: 14 edges (avg confidence: 0.61)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]

## God Nodes (most connected - your core abstractions)
1. `Mesh2D` - 12 edges
2. `AcceleratedSolver` - 9 edges
3. `websocket_simulate()` - 5 edges
4. `predict_pinn_flow()` - 3 edges
5. `download_vtk()` - 3 edges
6. `OpenZess FastAPI Server Exposes REST APIs & WebSockets for live CFD simulation s` - 3 edges
7. `Export and download the last simulation run as a VTK file for ParaView.` - 3 edges
8. `export_vtk()` - 3 edges
9. `renderThree3D()` - 3 edges
10. `renderCanvas()` - 3 edges

## Surprising Connections (you probably didn't know these)
- `OpenZess AI Engine — Fast PINN & Surrogate Physics Predictor Generates instant f` --uses--> `Mesh2D`  [INFERRED]
  backend\ai_predictor.py → backend\mesh.py
- `Simulates a trained Physics-Informed Neural Network (PINN) inference      to out` --uses--> `Mesh2D`  [INFERRED]
  backend\ai_predictor.py → backend\mesh.py
- `Mesh2D` --uses--> `OpenZess Solver Engine — Accelerated Navier-Stokes Solver Uses SciPy sparse matr`  [INFERRED]
  backend\mesh.py → backend\solver.py
- `Mesh2D` --uses--> `Build 5-point discrete Laplacian sparse matrix for Pressure Poisson equation.`  [INFERRED]
  backend\mesh.py → backend\solver.py
- `predict_pinn_flow()` --calls--> `websocket_simulate()`  [INFERRED]
  backend\ai_predictor.py → backend\app.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.25
Nodes (6): download_vtk(), OpenZess FastAPI Server Exposes REST APIs & WebSockets for live CFD simulation s, Export and download the last simulation run as a VTK file for ParaView., export_vtk(), OpenZess VTK Writer — Export CFD Fields to ParaView format (.vtk), Export 2D mesh fields (u, v, p) into a VTK Legacy Structured Points format.

### Community 1 - "Community 1"
Cohesion: 0.43
Nodes (3): websocket_simulate(), AcceleratedSolver, Build 5-point discrete Laplacian sparse matrix for Pressure Poisson equation.

### Community 2 - "Community 2"
Cohesion: 0.53
Nodes (4): getColor(), initThree(), renderCanvas(), renderThree3D()

### Community 3 - "Community 3"
Cohesion: 0.4
Nodes (3): open_browser(), OpenZess Studio Launcher Starts the backend FastAPI server and opens the Web Stu, Wait for server to start, then open browser.

### Community 4 - "Community 4"
Cohesion: 0.5
Nodes (3): predict_pinn_flow(), OpenZess AI Engine — Fast PINN & Surrogate Physics Predictor Generates instant f, Simulates a trained Physics-Informed Neural Network (PINN) inference      to out

### Community 5 - "Community 5"
Cohesion: 0.5
Nodes (2): Mesh2D, 2D Structured Mesh for finite difference / finite volume CFD.

### Community 6 - "Community 6"
Cohesion: 0.5
Nodes (2): OpenZess Mesh Module — 2D Grid Generation, OpenZess Solver Engine — Accelerated Navier-Stokes Solver Uses SciPy sparse matr

## Knowledge Gaps
- **6 isolated node(s):** `OpenZess Studio Launcher Starts the backend FastAPI server and opens the Web Stu`, `Wait for server to start, then open browser.`, `OpenZess Mesh Module — 2D Grid Generation`, `2D Structured Mesh for finite difference / finite volume CFD.`, `OpenZess VTK Writer — Export CFD Fields to ParaView format (.vtk)` (+1 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 5`** (4 nodes): `Mesh2D`, `.__init__()`, `.to_dict()`, `2D Structured Mesh for finite difference / finite volume CFD.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 6`** (4 nodes): `mesh.py`, `solver.py`, `OpenZess Mesh Module — 2D Grid Generation`, `OpenZess Solver Engine — Accelerated Navier-Stokes Solver Uses SciPy sparse matr`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Mesh2D` connect `Community 5` to `Community 0`, `Community 1`, `Community 4`, `Community 6`?**
  _High betweenness centrality (0.209) - this node is a cross-community bridge._
- **Why does `AcceleratedSolver` connect `Community 1` to `Community 0`, `Community 5`, `Community 6`?**
  _High betweenness centrality (0.114) - this node is a cross-community bridge._
- **Why does `websocket_simulate()` connect `Community 1` to `Community 0`, `Community 4`, `Community 5`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Are the 8 inferred relationships involving `Mesh2D` (e.g. with `OpenZess AI Engine — Fast PINN & Surrogate Physics Predictor Generates instant f` and `Simulates a trained Physics-Informed Neural Network (PINN) inference      to out`) actually correct?**
  _`Mesh2D` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `AcceleratedSolver` (e.g. with `OpenZess FastAPI Server Exposes REST APIs & WebSockets for live CFD simulation s` and `Export and download the last simulation run as a VTK file for ParaView.`) actually correct?**
  _`AcceleratedSolver` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `websocket_simulate()` (e.g. with `Mesh2D` and `predict_pinn_flow()`) actually correct?**
  _`websocket_simulate()` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `OpenZess Studio Launcher Starts the backend FastAPI server and opens the Web Stu`, `Wait for server to start, then open browser.`, `OpenZess Mesh Module — 2D Grid Generation` to the rest of the system?**
  _6 weakly-connected nodes found - possible documentation gaps or missing edges._