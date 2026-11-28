# OpenZess Studio: Gap Analysis (what is missing)

**Date:** 2026-11-28
**Type:** Analysis only. No code was changed.
**Companion files:** [PROJECT_ANALYSIS.md](PROJECT_ANALYSIS.md) (bugs and risks), [VERIFY_ANALYSIS.md](VERIFY_ANALYSIS.md) (how to check them).
**This file asks a different question:** not "what is broken", but "what is promised or needed and absent".

Status words: **Implemented**, **Partial**, **Absent**, **Contradicted** (the code says the opposite), **Unsupported** (no evidence in the repo).

---

## 1. Summary

The project has a working core: a browser CFD viewer with a WebAssembly solver, a Python solver, OpenFOAM-style export, and a small model that picks presets. The gaps fall in five groups:

1. **Promised but absent.** The paper and pitch describe features the code does not have (3D solver, neural surrogate, photo-to-3D, SIMD speedups).
2. **Product gaps.** Users cannot yet do the main job: describe a body and get a trusted result in the browser, compare runs, and export it.
3. **AI gaps.** The model chooses from a menu. It cannot refuse, explain results, or be measured fairly.
4. **Research evidence gaps.** Key numbers in the paper have no data behind them.
5. **Engineering gaps.** No backend hosting, no frontend tests, a solver whose source is missing.

---

## 2. Promised features vs the code

| # | Where promised | Claim | Status | Evidence |
|---|---|---|---|---|
| P1 | Paper (HTML abstract) | A "continuous 3D incompressible Navier-Stokes solver" with immersed boundaries | **Contradicted** | README: "2-D, laminar, incompressible". Backend uses `Mesh2D`. `solver_3d.py` and `mesh_3d.py` do not exist. The 3D view extrudes the 2D result. |
| P2 | Paper, pitch | An "instant Physics-Informed Neural Network" (PINN), under 50 ms | **Contradicted** | `backend/ai_predictor.py` docstring: "nothing here is a neural network"; the PINN claim "was false and has been removed". README agrees. The paper and pitch were not updated. |
| P3 | Paper conclusion | Ghia fit "R² > 0.985", GCI 1.48% | **Unsupported** | No script produces R² or GCI. The number 0.985 appears in `experiments/simulation_results.json` as `rmse_vs_ghia_1982: 0.9850`. An RMSE of 0.985 is large, not good. I could not confirm this is where the paper's number came from. |
| P4 | Paper conclusion | Rust "SIMD" sidecar, 11.4x faster than SciPy, 130.2x faster than CPython, 60 FPS | **Unsupported** | No SIMD code in `rust-sidecar/` (only `rayon` threads). No benchmark output contains 11.4 or 130.2. |
| P5 | Paper, README | WebAssembly solver in the browser | **Partial** | The binary exists and runs. Its source is not in the repo (see PROJECT_ANALYSIS A1). |
| P6 | Pitch, `docs/AI_VISION_AND_COPILOT.md` | Photo to silhouette to voxel geometry | **Absent** | The doc admits: "not implemented; the upload box does not read files". |
| P7 | `docs/LOCAL_HARDWARE_RUNTIME_ARCHITECTURE.md` | GPU use and a native OpenFOAM bridge | **Absent** | The doc admits: "no GPU code and no native-OpenFOAM bridge". |
| P8 | Pitch diagram | WebSocket `/ws/simulate_3d`, Chart.js residual monitor | **Absent** | Only `/ws/simulate` exists. `chart.js` is not in `package.json`. |
| P9 | README roadmap | OpenFOAM export for every geometry | **Absent** | Export works for the lid-driven cavity only. |
| P10 | README roadmap | STL / CAD import | **Absent** | The dropzone accepts files and says "not used". |
| P11 | README roadmap | Transient validation (cylinder Strouhal number) | **Absent** | No test or script mentions Strouhal. |
| P12 | README roadmap | Second-order advection, curved cut cells, turbulence, 3D | **Absent** | Listed as future work. The shipped WASM exposes a turbulence API, but its source is missing. |
| P13 | Your project idea | A small LLM that builds simulations from chat, driven by the WASM solver | **Partial** | Chat and AI Run can pick one of 8 presets or generate 2 to 5 primitives. No refusal, no result explanation, and one chat path still loses the Reynolds number. |
| P14 | Your project idea | "Like real OpenFOAM, in the web version" | **Absent** | Export only. No import, no server-side OpenFOAM run, and the log header "OpenFOAM v2406: icoFoam" is cosmetic. |

**Why this matters.** P1 to P4 are in the paper. A reviewer can disprove each one from the repo. Either build the feature or change the sentence.

---

## 3. Missing product capabilities

Effort: S = under a day, M = 1 to 3 days, L = a week or more.

### 3.1 The main user journey
| Missing | Why it matters | Effort |
|---|---|---|
| One path from "describe my body" to "trusted browser result" (builder, chat and AI Run share one engine and one Reynolds value) | This is the core promise. Today there are 3 entry points with different behaviour. | M |
| Example gallery with one-click cases and a first-run tour | A new user cannot tell what to click. The AI Run box says only "e.g. 120 km/h wind...". | S |
| Clear errors in the UI (toasts, not log lines) | Failures show only in the Log tab. | S |
| Resolution control for the browser solver (grid is fixed at 41x41) | Users cannot test grid independence in the browser. | S |
| Units and a dimensional view (m/s, Pa, Re from size and speed) | Users think in metres and m/s, not Re. | M |
| Undo / redo and "reset to default" for the builder | Easy to get lost in the Build tab. | S |

### 3.2 Solver and physics
| Missing | Why it matters | Effort |
|---|---|---|
| Boundary-condition editor (inlet profile, outlet pressure, moving wall, slip, periodic) | CFD users set BCs first. Now only a few are fixed per preset. | M |
| Steady and transient modes with a stop rule (residual target, time limit) and restart | Needed for correct validation (the 12-step problem). | M |
| Second-order advection, curved boundaries | First-order upwind makes the effective Re much lower than the slider value (README says so). | L |
| Turbulence in a solver you can inspect | The WASM exposes it; its source is missing. | L |
| 3D solver | The word "3D" in the UI is an extrusion. | L |
| Heat transfer in the browser solver | Exists in the Python path only. | M |

### 3.3 Results and analysis
| Missing | Why it matters | Effort |
|---|---|---|
| Force history (Cd, Cl vs time) plot and Strouhal number from the signal | Standard cylinder result, and the missing validation (P11). | S |
| Probes and line plots (velocity profile across a section) | The Ghia comparison needs this. | M |
| Run history and side-by-side comparison | Users compare geometries and Re. | M |
| Parametric sweep (Re, size, angle) with a table | One of the biggest time savers in CFD. | M |
| Report export (PDF or HTML with figures and settings) | Students need it for assignments. | M |
| Share link or project file that reopens the exact case | Teamwork and bug reports. | M |

### 3.4 Interoperability
| Missing | Why it matters | Effort |
|---|---|---|
| OpenFOAM export for all shapes | Roadmap item. Cavity only today. | M |
| OpenFOAM case **import** (read `controlDict`, `blockMeshDict`, `0/U`) | The "like OpenFOAM" promise. | M |
| Server-side real OpenFOAM run (Docker) with log streaming | Gives real results to compare. | L |
| STL / OBJ import (slice to a mask) | Roadmap item. | M |
| VTK import beyond ASCII legacy | Real ParaView files are often binary or `.vtu`. | M |

### 3.5 Quality of use
Not audited, so treat as unknowns: keyboard access, screen-reader labels, colour contrast, touch and mobile layout, languages other than English, browser support beyond Chromium.

---

## 4. Missing AI capabilities

| Missing | Why it matters | Effort |
|---|---|---|
| A **build recipe** output: list of shapes with position, size, angle, plus fluid and speed | Today the model picks from 12 shapes. It cannot describe a new body. | M (needs retraining data) |
| **Refusal** and clarifying questions | "asdf qwerty zzz" produces a shape. | M |
| Constrained decoding (JSON grammar) | Valid output every time, no parser tricks. | S |
| **Explain my results** (reads residuals, Cd, Cl, Courant and says what they mean) | Most useful chat feature for a student. | M |
| Chat with memory and streaming replies | Single-shot replies feel slow (about 30 s per answer). | M |
| Faster inference (quantized model, `llama.cpp`, fewer tokens) | Target under 3 s. | M |
| In-browser model (WebGPU or WASM, about 400 MB) | The Vercel site has no backend, so it has no AI. | L |
| A fair **evaluation set** (about 200 prompts the model never saw) and one script | The paper's ablation did not reproduce in my probe. | M |
| A reward that checks the answer against the prompt and runs the solver to a steady state | The current reward is saturated. | M |
| Model storage with a model card (weights, data, seeds) | The trained adapter is gitignored. | S |
| Prompt logging and feedback buttons (opt-in) to improve the data | Real prompts beat synthetic ones. | M |
| Safety rails: never run a spec the CFL guard changed by more than a set limit without telling the user | The guard silently clamps `dt`, grid and Re today. | S |

---

## 5. Missing research evidence

For the paper, these are missing, not wrong:

1. **One validation script** that runs to a steady state and writes one table (Ghia, 3 grids, observed order of accuracy). The README numbers look sound but the IEEE table is not.
2. **Cylinder transient validation:** Strouhal number near 0.16 and Cd near 1.3 to 1.4 at Re = 100 (literature values; check your references).
3. **Cross-solver agreement:** Python vs WASM vs Rust on the same cases, in one table.
4. **Timing table** with the machine, grid, steps and repeat count: WASM vs Python vs Rust (and OpenFOAM if you add it).
5. **Data behind every number in the paper** (R², GCI, 11.4x, 130.2x, 60 FPS) saved in `experiments/` with the script that made it.
6. **A held-out AI evaluation** with confidence intervals, for base, SFT and RL under the same settings.
7. **A reproducibility package:** seeds, versions, model hash, dataset, one command to rebuild every figure.
8. **A limitations section** that matches the README (2D, laminar, first order, staircase bodies).
9. **A comparison with real OpenFOAM** on at least the cavity and the cylinder.

---

## 6. Missing engineering foundations

| Missing | Effort |
|---|---|
| Source and build script for `fvm_solver.wasm` | M |
| A hosted backend (Dockerfile, deploy workflow, CORS and auth for it) | M |
| Authentication, quotas, per-user results | M |
| Frontend tests (`vitest`) and a smoke test (Playwright) | M |
| Lint, type check and coverage gate in CI | S |
| Complete, pinned Python requirements | S |
| Structured logging and a metrics endpoint | S |
| A typed API client (one base-URL helper) | S |
| `.gitignore` for build output; cleaned history (`.git` is 380 MB) | S |
| Splitting the 4,700-line viewer component | M |
| A changelog, versioning and release notes | S |
| A repo location outside OneDrive (it locked `node_modules` and broke `npm ci`) | S |

---

## 7. What to build first

Ranked by value for the paper and for users. "First step" is the smallest useful move.

| # | Missing item | First step |
|---|---|---|
| 1 | Honest paper claims (P1 to P4) | Edit the paper and pitch to match `README.md`. Remove "3D solver" and "PINN". Add the data or remove R², GCI, 11.4x and 130.2x. |
| 2 | One validation script and table (section 5, items 1 and 5) | Fix the `cfl_max` key, run to a steady state, write `experiments/validation.json` and a table. |
| 3 | WASM source in the repo (P5) | Find the original source, or rewrite the 22-function API from the glue file. |
| 4 | Build-recipe output, refusal, constrained decoding (section 4) | Define the JSON schema, then generate 2,000 varied training prompts including refusals. |
| 5 | Held-out AI evaluation (section 4 and 5) | Write 200 prompts, freeze them, run base vs SFT vs RL. |
| 6 | Force history and Strouhal number (3.3) | Plot Cd and Cl vs time in the viewer, compute the peak frequency. |
| 7 | One engine path for builder, chat and AI Run (3.1) | One function that takes a recipe and Re, used by all three. |
| 8 | Hosted backend and auth (section 6) | Dockerfile, then one host (Fly, Render or your own machine). |
| 9 | OpenFOAM case export for all shapes, then import (3.4) | Start with a rectangle obstacle using `blockMesh` with holes. |
| 10 | Run real OpenFOAM server-side (3.4) | Docker image, one `icoFoam` cavity run, stream the log. |

---

## 8. Method and limits
- I read the README, roadmap, pitch, the HTML paper, `TECH_STACK.md`, the AI vision and hardware docs, and the code. I searched the code for each promised feature.
- I did not read the PDF version of the paper. The HTML paper may differ from it. Check P1 to P4 against the version you submit.
- I did not test every UI button. The Slice, Clip, Contour, Glyph and Streamlines buttons exist. I did not check which ones work.
- I did not run the Rust code.
- Effort numbers are rough guesses for one developer who knows the code.
