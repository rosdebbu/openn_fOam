# Literature Review & Scope Definition Report
**Project Title:** AI-Augmented High-Performance Web CFD Platform: Integrating Finite Volume Solvers, Physics-Informed Surrogates, and Bare-Metal Rust-Python Hybrid Compute with Real-Time 3D Telemetry  
**Project Identifier:** UR2627GEN317  
**Milestone:** 10% — Literature Review & Problem Scope Definition  
**Date:** September 2026  
**Status:** Completed  

---

## Executive Summary

Computational Fluid Dynamics (CFD) has traditionally required expensive high-performance computing (HPC) clusters, proprietary desktop software (e.g., ANSYS Fluent, COMSOL), and complex manual mesh-generation workflows. This research project introduces **OpenZess Studio**, an indigenous, browser-accessible, AI-augmented aerothermal CFD platform. 

This document fulfills the **10% Milestone** by:
1. Conducting a comprehensive multi-disciplinary literature review across four key pillars:
   - Numerical Finite Volume & Fractional-Step Solvers,
   - Physics-Informed Neural Networks (PINNs) and Deep Learning Surrogates for fluid dynamics,
   - Bare-metal systems programming (Rust) and zero-copy Python interoperability (PyO3) for scientific computing,
   - Web-native 3D telemetry, WebGL/Three.js rendering, and real-time streaming architectures.
2. Formally defining the research scope, mathematical boundaries, performance benchmarks, and delivery roadmap for project **UR2627GEN317**.

---

## Pillar 1: Literature Review

### 1.1 Incompressible Navier-Stokes & Fractional-Step Methods
* **Foundational Basis:** Chorin (1968) introduced the projection / fractional-step method, decoupling velocity advection-diffusion from the kinematic pressure Poisson equation:
  $$\vec{u}^* = \vec{u}^n + \Delta t \left[ \nu \nabla^2 \vec{u}^n - (\vec{u}^n \cdot \nabla) \vec{u}^n \right]$$
  $$\nabla^2 p = \frac{\rho}{\Delta t} \nabla \cdot \vec{u}^*$$
  $$\vec{u}^{n+1} = \vec{u}^* - \Delta t \nabla p$$
* **Finite Volume Standards:** Jasak (1996) and Weller et al. (1998) established the open-source FVM benchmark in OpenFOAM, utilizing co-located Rhie-Chow momentum interpolation to suppress checkerboard pressure oscillations.
* **Thermal Coupling:** The Boussinesq approximation (Tritton, 1988) couples thermal buoyancy as a body force $\vec{g}\beta(T - T_{\text{amb}})$ without incurring the computational expense of fully compressible density equations for low-Mach thermal flows.
* **Literature Gap:** Standard CFD implementations (OpenFOAM, SU2) are compiled desktop/cluster C++ tools with high entry barriers and zero native real-time web interactivity.

### 1.2 Physics-Informed Neural Networks (PINNs) & Neural Operators
* **PINNs Formulation:** Raissi, Perdikaris, & Karniadakis (2019) demonstrated that embedding the Navier-Stokes differential operator directly into the neural loss function ($\mathcal{L} = \mathcal{L}_{\text{data}} + \lambda \mathcal{L}_{\text{PDE}}$) enables surrogate estimation without labeled physical data.
* **Operator Learning:** Li et al. (2020) proposed the Fourier Neural Operator (FNO), proving mesh-invariant learning of fluid PDE solution operators with orders-of-magnitude inference speedups over classical solvers.
* **Hybrid Surrogate Architectures:** Brunton, Noack, & Koumoutsakos (2020) surveyed deep learning in fluid mechanics, concluding that surrogates are optimal for fast design space exploration (<50 ms), whereas classical numerical solvers remain essential for high-precision verification.
* **Literature Gap:** Existing PINN/FNO implementations operate in siloed offline Python/PyTorch environments without seamless live coupling to interactive web viewports or dual-mode numerical/surrogate switching.

### 1.3 Bare-Metal Systems Languages in Scientific Computing (Rust vs. Python/C++)
* **Language Ergonomics & Safety:** Rust (Matsakis & Klock, 2014) provides C/C++ tier execution performance with compile-time memory safety, zero-cost abstractions, and fearless multithreaded concurrency without a Garbage Collector (GC).
* **Python Interoperability:** The PyO3 bridge and Maturin build pipeline enable zero-copy shared memory access between NumPy `ndarray` buffers and native Rust SIMD stencils.
* **Literature Gap:** While Rust is widely adopted in systems engineering and distributed web services, its application in multi-threaded 3D stencil solvers coupled with dynamic web clients remains largely unexplored in published CFD literature.

### 1.4 Web-Based Scientific Visualization & Telemetry
* **In-Browser Compute & Rendering:** Modern browser capabilities via WebGL 2.0 and WebGPU (Cabello et al., Three.js) allow hardware-accelerated volumetric rendering, vector field streamlines, and dynamic cross-sectional slicing directly on client GPUs.
* **Streaming Protocol:** RFC 6455 (WebSocket) offers full-duplex, low-latency binary transport ideal for streaming high-frequency velocity/pressure fields and residual telemetry compared to REST polling.
* **Literature Gap:** Most web visualization tools (e.g., ParaView Glance, Visual3D) are passive post-processors; they do not provide bi-directional steering of an active, running physics simulation.

---

## Pillar 2: Research Scope & Project Boundaries

### 2.1 Problem Statement
To design, implement, and validate an integrated, web-native CFD platform that combines:
1. An indigenous 3D Navier-Stokes numerical solver with thermal buoyancy,
2. An instant Physics-Informed surrogate engine (<50 ms response),
3. A bare-metal Rust-Python hybrid compute kernel for multi-core scaling,
4. A reactive Three.js/WebGL user interface with live WebSocket telemetry, residual convergence tracking, and two-way OpenFOAM/VTK interoperability.

### 2.2 In-Scope Items
- **Governing Physics:** Incompressible, laminar to transitional 3D Navier-Stokes with Boussinesq thermal buoyancy and thermal convection-diffusion.
- **Discretization:** Fractional-step projection method on structured Cartesian grids with 1st-order upwind convection and 2nd-order central diffusion.
- **Poisson Solver:** Iterative sparse linear system solver (SciPy sparse conjugate gradient & Rust-accelerated multi-threaded Gauss-Seidel/Jacobi).
- **AI Surrogate Model:** Real-time surrogate inference predicting stagnation pressure, wake recirculation, and buoyant thermal plumes for predefined and parametric geometries.
- **Compute Architecture:** Python (FastAPI, NumPy, SciPy) coupled via PyO3 to Rust (Rayon parallel thread pools, SIMD stencils).
- **Client & Telemetry:** Vue 3, Three.js WebGL 3D, HTML5 2D Canvas, Chart.js logarithmic residual monitor, and bi-directional WebSockets.
- **Interoperability:** Automated generation of production-ready OpenFOAM cases (`buoyantBoussinesqSimpleFoam`) and ParaView legacy structured-points `.vtk` files.

### 2.3 Out-of-Scope (Boundaries for Current Phase)
- Highly compressible / supersonic shock-capturing flows ($Ma > 0.3$).
- Complex multiphase flows with free-surface volume of fluid (VOF) interface reconstruction.
- Arbitrary unstructured tetrahedral mesh generation inside the browser (structured voxel grids and bounding-box domain mapping will be utilized for real-time web responsiveness).

---

## Comparative Literature Matrix

| Domain / Criterion | Traditional Desktop CFD (ANSYS/COMSOL) | OpenFOAM (Native C++) | Pure Python CFD (SciPy/PyTorch) | **OpenZess Platform (UR2627GEN317)** |
| :--- | :--- | :--- | :--- | :--- |
| **Accessibility** | Expensive license, desktop install | Linux CLI, steep learning curve | Script-only, unoptimized for 3D | **Zero-install, browser Web Studio** |
| **Inference Speed** | Minutes to hours | Minutes to hours | Fast (GPU) but no UI integration | **Instant PINN (<50 ms) + Live Solver** |
| **Compute Engine** | Proprietary C++ | Open-source C++ | Python (GIL bottleneck) | **Hybrid Python + Rust (Rayon SIMD)** |
| **Telemetry** | Post-processing only | Post-processing (ParaView) | Static matplotlib plots | **Real-time 3D Three.js + WebSocket** |
| **Interoperability** | Vendor lock-in | Native dictionaries | Custom array formats | **Export to OpenFOAM & ParaView VTK** |

---

## 26-Week Project Roadmap & Milestone Alignment

| Milestone | Target % | Focus Area | Deliverables |
| :--- | :---: | :--- | :--- |
| **Current** | **10%** | **Literature Review & Scope Definition** | Literature synthesis report, mathematical formulation, boundary definition, and tech stack architecture. |
| Next | 30% | Experimentation / Simulation Setup | Baseline 3D fractional-step solver, boundary condition validation, and grid convergence studies. |
| Phase 3 | 50% | Analysis / Hybrid Compute / Surrogate | Rust PyO3 acceleration benchmark, PINN surrogate training, residual convergence comparison. |
| Phase 4 | 70% | Paper Drafting | Research paper drafting: methodology, validation against OpenFOAM benchmarks, scaling graphs. |
| Phase 5 | 80% | Journal / Conference Submission | Manuscript finalization, citation formatting, submission to target CFD/AI conference or journal. |
| Final | 100% | Final Defense & Acceptance | Project defense, interactive web platform demonstration, artifact repository release. |

---

## References & Bibliography

1. **Chorin, A. J.** (1968). *Numerical solution of the Navier-Stokes equations*. Mathematics of Computation, 22(104), 745-762.
2. **Jasak, H.** (1996). *Error analysis and estimation in the Finite Volume method with applications to fluid flows*. Ph.D. Thesis, Imperial College of Science, Technology and Medicine, University of London.
3. **Weller, H. G., Tabor, G., Jasak, H., & Fureby, C.** (1998). *A tensorial approach to computational continuum mechanics using object-oriented techniques*. Computers in Physics, 12(6), 620-631.
4. **Raissi, M., Perdikaris, P., & Karniadakis, G. E.** (2019). *Physics-informed neural networks: A deep learning framework for solving forward and inverse problems involving nonlinear partial differential equations*. Journal of Computational Physics, 378, 686-707.
5. **Li, Z., Kovachki, N., Azizzadenesheli, K., Liu, B., Bhattacharya, K., Stuart, A., & Anandkumar, A.** (2020). *Fourier Neural Operator for Parametric Partial Differential Equations*. arXiv preprint arXiv:2010.08895 (ICLR 2021).
6. **Brunton, S. L., Noack, B. R., & Koumoutsakos, P.** (2020). *Machine learning for fluid mechanics*. Annual Review of Fluid Mechanics, 52, 477-508.
7. **Matsakis, N. D., & Klock, F. S.** (2014). *The Rust language*. ACM SIGAda Ada Letters, 34(3), 103-104.
8. **Patankar, S. V.** (1980). *Numerical Heat Transfer and Fluid Flow*. Hemisphere Publishing Corporation, Taylor & Francis Group.
9. **Tritton, D. J.** (1988). *Physical Fluid Dynamics*. Oxford University Press.
10. **Cabello, R. et al.** (2024). *Three.js: JavaScript 3D Library*. https://threejs.org/
