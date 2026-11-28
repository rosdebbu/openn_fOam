# OpenZess Studio: Project Analysis

**Date:** 2026-11-28
**Type:** Analysis only. No code was changed for this report.
**Evidence rule:** Each finding says how it was found. `VERIFIED` = I ran it or read the exact lines. `INFERRED` = deduced from code or config, not run.

---

## 1. Scope and method

**What I did**
- Read the repo layout, manifests, CI, deploy config and docs.
- Read the backend routes, the WebSocket solver loop, the AI pipeline, the agent-desktop module and the project store.
- Counted frontend sizes, dead modules, `any` types, hard-coded URLs and timers.
- Ran: `pytest` (93 pass), `coverage`, `ruff`, `npm audit`, `npm outdated`, `vue-tsc`.
- Ran my own backend on a spare port. I measured event-loop blocking and bad-input behaviour.
- Loaded the app in a browser and read the console.
- Compared the shipped WebAssembly binary with the C source in the repo.

**What I did not do**
- I did not run the Rust sidecar tests or build it.
- I did not audit accessibility, mobile layout or colour contrast.
- I did not run the real OpenFOAM or compare results with it.
- I did not train or evaluate any model beyond the probes in `docs/VERIFY_CHANGES.md`.
- I did not test the deployed Vercel site.

**One caution.** Another tool edits the same files at the same time. Line numbers below were correct on 2026-11-28 and can move.

---

## 2. Architecture

```
                         BROWSER (Vue 3 + TypeScript + Vite)
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ App.vue ── HeaderNavbar · SidebarControls · SettingsModal                │
 │   │                                                                       │
 │   ├─ ParaViewGlanceViewer.vue  (4,724 lines: viewer + WASM + AI + build) │
 │   │     ├─ vtk.js renderer   ├─ OpenZessBoardStage (Three.js diorama)   │
 │   │     └─ openfoamWasmBridge.ts ─► fvm_solver.wasm  fea_structure.wasm  │
 │   │            (TypeScript fallback solver when WASM fails)              │
 │   ├─ CfdThree3D.vue (legacy Three.js mode, WebSocket client)             │
 │   └─ aiCopilot.ts ─► Anthropic / Gemini / OpenAI / Ollama (keys in       │
 │                       browser localStorage)                              │
 └───────────────┬───────────────────────────────────────────────────────────┘
                 │ HTTP /api/*  ·  WebSocket /ws/simulate   (hard-coded :8000)
 ┌───────────────▼───────────────────────────────────────────────────────────┐
 │ FastAPI backend (backend/app.py, 1,087 lines, no auth)                    │
 │   solver.py (SciPy fractional step)  ai_predictor.py (potential flow)     │
 │   ai_simulate.py (regex rules + CFL guard)                                │
 │   _run_ai_pipeline: Laya router ─► Qwen3-0.6B + LoRA ─► CFL guard         │
 │   openfoam_export.py · vtk_writer.py · projects.py (JSON files)           │
 │   agent_desktop.py (host control) · text_to_3d.py (Meshy / HF Spaces)     │
 │   rust_bridge.py ─► Rust sidecar :8081 (axum, rayon)  [optional]          │
 └───────────────────────────────────────────────────────────────────────────┘
 Not wired in: wasm-solver/src/lib.rs, workers/cfdWorker.ts, real OpenFOAM
```

**Three separate solvers exist.** They are not cross-checked.
1. Python/SciPy (`backend/solver.py`). README validation uses this one.
2. `fvm_solver.wasm`. The source is not in the repo (finding A1).
3. Rust sidecar (`rust-sidecar/`).
There is also a TypeScript fallback and `wasm-solver/src/lib.rs`, which is never built into the app.

### 2.1 Technology stack (measured versions)

| Layer | Technology | Version / size | Note |
|---|---|---|---|
| UI framework | Vue 3 (`<script setup>`) | 3.5.44 | |
| Language | TypeScript | 6.0.3 | `vue-tsc` runs in CI |
| Build | Vite | 8.3.7 | Main bundle 1.79 MB, one chunk |
| 3D / viz | Three.js 0.185 + vtk.js 38.0.5 | | Two 3D engines in one app |
| Browser solver | Emscripten WASM | `fvm_solver.wasm` 27 KB, `fea_structure.wasm` 10 KB | Source gap (A1) |
| Backend | Python 3.12 local, FastAPI 0.141, Starlette 1.6 | | CI tests 3.10 and 3.13 |
| Numerics | NumPy, SciPy | `>=` only | No pins |
| Optional engine | Rust (axum 0.7, tokio, rayon) | 8 tests | Not run by me |
| Model | Qwen3-0.6B + LoRA (r=16) | RL adapter 557 MB local | Gitignored (A4) |
| Router | `laya` (GitHub package) | not in requirements | Silent fallback |
| Training | TRL (GRPO), PEFT, bitsandbytes | | `scripts/train_openzess_grpo.py` |
| Deploy | Vercel (frontend static only) | `frontend/vercel.json` | No backend host |
| CI | GitHub Actions | pytest, cargo test, frontend build | No frontend tests |

---

## 3. Findings

Severity: **P0** blocks the paper or is a serious risk. **P1** real defect. **P2** quality. **P3** minor.

### A. Research integrity (P0)

| ID | Finding | Evidence | Impact |
|---|---|---|---|
| A1 | **The source of `fvm_solver.wasm` is not in the repo.** The app calls `fvm_create`, `fvm_step`, `fvm_paint_obstacle`, `fvm_set_adaptive_dt`, and the glue exports k, epsilon, nut, drag, lift and scalar functions. The only C file exports a different API (`wasm_init_solver`, `wasm_step_piso`) and `compile_wasm.bat` writes a different output file (`openfoam_solver.js`). The binary is dated 2026-10-18. | VERIFIED. `grep` for `fvm_step`/`fvm_create` finds no C, C++ or Rust source. `public/wasm/fvm_solver.js` lists `_fvm_get_turbulence`. | You cannot rebuild, audit or fix the solver the paper's WebAssembly claim rests on. |
| A2 | **Two contradictory validation tables.** README: RMSE 0.0385 at 41x41, falling with refinement. IEEE doc: RMSE 0.2381 at 41x41, rising 0.2200 → 0.2381 with refinement. | VERIFIED. README lines 172-190 vs `docs/IEEE_BENCHMARK_RESULTS.md`. | A reviewer sees both. The IEEE table shows no convergence. |
| A3 | **"Max CFL = 0.000" is a default value.** The script reads key `cfl`. The function returns `cfl_max`. | VERIFIED. `scripts/run_ieee_benchmarks.py:42` vs `train_openzess_grpo.py:130,144`. | Every Max CFL cell in the paper is wrong. |
| A4 | **The verifier runs 12 time steps** (about 0.2 s physical time). Ghia needs a steady state (about 20 to 30 s). | VERIFIED. `train_openzess_grpo.py:146`. | The "validation" measures the start-up transient. |
| A5 | **The RL reward is saturated.** `if ghia_rmse < 0.65` is always true when RMSE is about 0.23. | VERIFIED. `train_openzess_grpo.py:264`. In my probe, RL and SFT differ mainly in grid size. | The RL result measures JSON compliance, not learned physics. |
| A6 | **The paper's ablation did not reproduce.** The paper says the base model gives 33% valid JSON. My probe: 12 of 12. Settings differ (greedy, thinking off, 12 prompts). | VERIFIED once. | The headline number may not hold. Re-run on a held-out set. |
| A7 | **The trained RL adapter is not in git.** `.gitignore:53` ignores `openzess_qwen3_0.6b_rl/`. The SFT adapter is untracked. No training data or eval set is stored. | VERIFIED. `git check-ignore`. | A fresh clone has no trained model and cannot reproduce it. |
| A8 | **Docs claim things that do not exist.** `docs/TECH_STACK.md` lists Chart.js, Tailwind, `solver_3d.py`, `mesh_3d.py`, `ai_vision_engine.py`, `vtk_writer_3d.py`. None exist. The header says "C++20 WASM" and the log says "OpenFOAM v2406: icoFoam WebAssembly Execution". No C++20 source exists. README says "no turbulence model" while the WASM exports a turbulence API. | VERIFIED (file checks, grep). | Claims a reviewer can disprove in minutes. |

### B. Security and robustness

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| B1 | P0 | **Unauthenticated host control.** `/api/agent-desktop/click`, `/type`, `/screenshot`, `/launch-paraview` have no auth. `screenshot` takes a caller-chosen `output_path`. `launch-paraview` takes any file path. | VERIFIED. `backend/app.py:564-591`, `agent_desktop.py`. |
| B2 | P0 | **The backend on port 8000 is bound to `0.0.0.0`** (PID 12756 at the last check, not started by me). The LAN can reach B1. `main.py` itself binds `127.0.0.1`. | VERIFIED. `Get-NetTCPConnection`. |
| B3 | P1 | **No auth, quota or rate limit on anything.** This includes `DELETE /api/projects`, project saves (no size limit), the 30-second GPU endpoints `/api/ai/*`, and `/api/ai/text-to-3d` (uses Meshy credits or HF quota). | VERIFIED by reading routes. |
| B4 | P1 | **The solver blocks the event loop.** `solver.step(dt)` is CPU-bound and runs inside the async WebSocket handler. Measured: 96x96, 200 iterations, 2.1 s. `/api/health` took 484 ms median (216 ms idle) and only 4 of about 20 pings completed. Larger grids are worse. | VERIFIED. `app.py:486`. |
| B5 | P1 | **Weak resource limits.** Grid up to 256 (x2 in x for channel cases), up to 20,000 iterations, no timeout, no per-client cap. | VERIFIED. `MAX_GRID=256`, `MAX_ITERATIONS=20000`. |
| B6 | P1 | **Bad inputs are accepted silently.** `Re = 0` and `Re = -5` run without an error: `CasePhysics` falls back to air's viscosity. `Re = 1e12` returns 1 frame and no message. A non-numeric `gridResolution` drops the socket without a close frame. | VERIFIED. `solver.py:101-107`, probe results. |
| B7 | P1 | **Global `last_results`.** All clients share one result store. User A can export user B's run. | VERIFIED. `app.py:49`. |
| B8 | P2 | **DNS rebinding.** CORS and the WebSocket Origin check are the only guards. There is no `Host` header check. | INFERRED. |
| B9 | P2 | **API keys live in the browser.** `dangerouslyAllowBrowser: true`, keys in `localStorage`. An XSS bug would steal them. | VERIFIED. `aiCopilot.ts:95`. |
| B10 | P2 | **Privacy and hygiene.** `.vscode/mcp.json` (tracked) holds local Windows paths. `saved_chats/` and `data/seen_jobs.json` are tracked. An internship scraper (`/tracker`, `/api/internships/latest`) lives inside the CFD server. | VERIFIED. |
| B11 | P3 | **Good news.** A scan of tracked files found no API keys. `npm audit` reports 0 vulnerabilities. Subprocess calls use argument lists, not a shell. Project names are sanitized. | VERIFIED. |

### C. Application bugs and design defects

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| C1 | P1 | **The AI Chat tab still drops the Reynolds number.** `sendAiChat` sets `wasmPreset`, then `customReynolds`. The preset watcher passes no Re, so the preset's own Re wins. AI Run was fixed. Chat was not. | VERIFIED by reading. `ParaViewGlanceViewer.vue:2582`. Not run in the browser. |
| C2 | P1 | **The API base URL has 4 conventions.** Five places use `http://${hostname}:8000`. Others use `envApi` or a `5173` host check. This breaks on HTTPS (mixed content), on Vercel, and on any other port. The Vite proxy exists but these calls bypass it. | VERIFIED. `grep`. |
| C3 | P1 | **`syncWithActiveSolver` trusts `res.ok`.** On Vercel, the SPA rewrite returns `index.html` with status 200. The code then parses HTML as VTK. | VERIFIED code (`ParaViewGlanceViewer.vue`) plus `vercel.json` rewrite. The Vercel behaviour is INFERRED. |
| C4 | P1 | **The app opens on fake data.** `activeData = generateProceduralCfdData(41, 41)` is analytic, not solved. It also replaces real data on any fetch failure. | VERIFIED. Lines 1471, 2673, 2676. |
| C5 | P1 | **The browser solver grid is fixed at 41x41.** `new OpenFoamWasmEngine(41, 41, ...)`. No resolution control. | VERIFIED. Lines 2152, 2207. |
| C6 | P1 | **The AI never refuses.** "asdf qwerty zzz" produces a shape named "asdf". | VERIFIED live. |
| C7 | P2 | **AI geometry is random-looking.** Sampling (`temperature 0.4`) gives different shapes for the same prompt. The fallback `_procedural_primitives_for_idea` builds a hash-seeded body for any unseen word. | VERIFIED code. |
| C8 | P2 | **The keyword block runs before the backend.** Words like car, lander, boat, drone return a fixed template. A model never sees them. | VERIFIED. |
| C9 | P2 | **Old regex quirks.** `sub` matches "substance". `water` maps to the venturi. `box` maps to the cavity. | VERIFIED. |
| C10 | P2 | **Dead code, about 1,330 lines.** Zero importers: `AiAssistant.vue` (a `setTimeout` fake), `CfdCanvas2D.vue`, `HelloWorld.vue`, `OpenFoamDictEditor.vue`, `OpenFoamTerminal.vue`, `workers/cfdWorker.ts`. Also `wasm-solver/src/lib.rs` is never built. | VERIFIED. Import count = 0. |
| C11 | P2 | **One 4,724-line component.** `ParaViewGlanceViewer.vue` holds the viewer, WASM loop, AI, build tab and chat. It has 8 `@ts-ignore` and the project has 48 `any`. | VERIFIED. |
| C12 | P2 | **Bundle.** One 1.79 MB JS chunk plus a 359 KB chunk (the Anthropic SDK loaded in the browser). No code splitting for vtk.js or Three.js. | VERIFIED. `dist/assets`. |
| C13 | P2 | **Slow AI.** One model answer takes about 30 s. One lock (`_qwen_lock`) serializes all AI calls. | VERIFIED (measured earlier). |
| C14 | P2 | **The router fails silently.** `laya` is not in `requirements.txt`. If it is missing, `laya_route` is `None` and nothing tells the user. | INFERRED from code. |
| C15 | P3 | **Concurrent-edit hazard.** While the other tool edited the viewer, the console showed a render crash (`textTo3dPrompt` used in the template before it was defined). It is fixed now. | VERIFIED (transient). |
| C16 | P1 | **The WASM solver blew up and the "self-heal" hid it. FIXED 2026-11-28.** The bridge ran `fvm_step(20)`: 20 pressure sweeps was too few, so divergence built up. Peak speed grew exponentially (1.2, 150, 8.5e22) until it overflowed to NaN. Only then did `step()` call `reset()`, so the field restarted and blew up again about every 10 s. Not a CFL problem: Co stayed near 0.5, and it also happened at 81x81 with half the time step. Built-in presets blew up too (peak 43 on the cylinder, 1e26 on the house). Fix: sweeps scale with the grid (`pressureIters`, about 2.6 x grid size) and the grid is 61x61. Result: 8 of 8 presets stable over 1,680 steps, peak 1.0 to 1.64, about 36 ms per frame. | VERIFIED. See `docs/VERIFY_CHANGES.md` round 3. |

### D. Repo, build and operations

| ID | Sev | Finding | Evidence |
|---|---|---|---|
| D1 | P0 | **`.git` is 380 MB.** 2,356 tracked files. About 186 MB is Rust build output in `rust-sidecar/tools/rustbuild/` (566 `.o`, 156 `.rlib`, 66 `.exe`). `.gitignore` has `target/` only. | VERIFIED. |
| D2 | P1 | **`requirements.txt` is incomplete.** Runtime imports `torch`, `transformers`, `peft`, `trl`, `datasets`, `laya`, `requests`, `gradio_client` are not declared. No pins, no lockfile. | VERIFIED. |
| D3 | P1 | **No backend hosting.** No Dockerfile, compose or deploy workflow. Vercel hosts only the static frontend, and CORS allows only localhost. The deployed site has no AI and no server solver. | VERIFIED. |
| D4 | P1 | **Test gaps.** Backend coverage is 66%: `app.py` 52%, `agent_desktop.py` 22%, `rust_bridge.py` 25%, `text_to_3d.py` 0%. The frontend has 0 test files and no end-to-end config. CI has no lint step and no coverage gate. | VERIFIED. `coverage report`. |
| D5 | P2 | **Weak logging.** 15 `print()` calls, 2 `logging` uses, 2 swallowed exceptions. `_run_ai_pipeline` turns any exception into a fallback. | VERIFIED. |
| D6 | P2 | **Style lint.** `ruff` reports 25 style items (10 imports not at top, 14 semicolon lines in `solver.py`, 1 unused import). No logic errors found. | VERIFIED. |
| D7 | P3 | **Outdated packages.** `@anthropic-ai/sdk` 1.5.0 → 1.14.0, `vite` 8.3.7 → 8.4.0, `vue` 3.5.44 → 3.5.46, and others. | VERIFIED. |
| D8 | P3 | **Clutter.** About 30 PDFs in the repo root and `docs/` (not tracked), an empty `.kilo/`, a tracked 13 MB `graphify-out/graph.json` that changes on each run, tool folders `.agents`, `.claude`, `.vscode`. | VERIFIED. |
| D10 | P2 | **The repo lives inside OneDrive.** `npm ci` failed with `EPERM` on a locked `.node` file, and left `frontend/node_modules` half deleted (found 2026-11-28). A running Vite server was the lock. OneDrive can also lock or slow `node_modules`. | VERIFIED (error screenshot, `node_modules` check). See `docs/VERIFY_ANALYSIS.md` section 0.2. |
| D9 | P3 | **CI is good but narrow.** It runs pytest on 3.10 and 3.13, `cargo test`, and the frontend build. Starlette 1.6 supports `httpx2`, so `httpx2>=2.0` in `requirements-dev.txt` is correct. | VERIFIED. |

---

## 4. Missing features and add-ons

### 4.1 Product
- Accounts and auth. Per-user projects and results (replace the global `last_results`).
- Run history and side-by-side comparison of runs.
- Parametric sweeps (Re, size, angle) and a results table.
- Probes, line plots, and a Cd/Cl history chart in the browser solver.
- Mesh resolution control in the browser solver.
- STL, OBJ and CAD import (the dropzone says "not implemented").
- OpenFOAM export for all geometries, and OpenFOAM case import.
- Run real OpenFOAM on a server (Docker). See the architecture in the earlier answer.
- Turbulence in the Python solver, and a 3D solver.
- Share links, PDF report export, undo and redo.
- Mobile layout and accessibility (not audited).

### 4.2 AI
- Change the model output from a menu to a build recipe: a list of shapes with position, size and angle, plus fluid, speed and an `unsupported` flag.
- Constrained decoding (a JSON grammar) so output is always valid.
- Refusal and clarifying questions.
- A held-out test set (about 200 prompts) and a fixed evaluation script with the same settings for base, SFT and RL.
- A real reward: check the output against the prompt (Re, shape) and run the solver to a steady state.
- Faster inference (quantized model, `llama.cpp` or a similar runtime). The target is under 3 s.
- Run the model in the browser (WebGPU or WASM, about 400 MB) so the Vercel site has AI.
- Chat history, streaming replies, and a "explain these results" tool that reads residuals.
- Store the trained adapter in a model hub, with a model card.

### 4.3 Engineering
- Split `ParaViewGlanceViewer.vue` into a store plus small components.
- Generate a typed API client from the FastAPI OpenAPI schema. One base-URL helper.
- Add `vitest` unit tests and Playwright smoke tests.
- Add `ruff` and a coverage gate to CI.
- Add a Dockerfile, a compose file, and a deploy workflow for the backend.
- Add structured logging, a request-ID, and a metrics endpoint.
- Pin Python dependencies. Add Dependabot.
- Add `rustbuild/` to `.gitignore`, then remove the artifacts from history (`git filter-repo`) to shrink `.git`.

### 4.4 Research and paper
- Put the WASM solver source in the repo with a build script, or replace it with the code in the repo.
- One validation table from one script: Ghia (steady state), cylinder Strouhal and Cd at Re = 100, grid-convergence order.
- Cross-check the Python, WASM and Rust solvers on the same cases.
- Timing table: WASM vs Python vs Rust vs OpenFOAM.
- A reproducibility package: seeds, data, scripts, model hash.

---

## 5. What is already good
- CORS is locked to localhost on purpose, and the WebSocket checks `Origin`. The code explains why.
- `validate_spec` clamps the Courant and diffusion numbers. Python solver coverage is 96%.
- 93 backend tests pass. CI builds the frontend with `vue-tsc`.
- No secrets in tracked files. `npm audit` is clean.
- The README states its own limits (2D, laminar, first-order, staircase bodies).
- The WASM path has a TypeScript fallback.
- The solver reports divergence to the client with a clear message.

---

## 6. Corrections to my earlier statements
1. I said `fvm_solver.wasm` was "real Emscripten C with a proper ABI". The binary is real, but its source is not in the repo (A1).
2. I said `httpx2>=2.0` looked suspect. It is a real package by the pydantic org, and Starlette 1.6 uses it. It is fine.
3. I said the model fails because `torch` is missing. On this machine it is installed and the model loads. The cause of the "unavailable" message was never found.
4. I said the adapter check had 65 assertions. The number is 62.

---

## 7. Suggested order of work

| # | Work | Why first | Effort |
|---|---|---|---|
| 1 | Close B1 and B2: bind to `127.0.0.1`, remove or protect agent-desktop routes. | Open host control on the LAN. | 1 h |
| 2 | A3 + A4 + A2: fix the `cfl_max` key, run to steady state, publish one validation table. | Paper claims. | 1 day |
| 3 | A1: get the WASM source into the repo, or rebuild from the repo's C. | Reproducibility. | 1 to 3 days |
| 4 | A5 + A6 + A7: fix the reward, re-run the ablation on a held-out set, store the adapter. | Paper claims. | 2 days |
| 5 | D1: ignore and purge `rustbuild/`. | Repo size. | 2 h |
| 6 | C1 + C2 + C3: chat Re bug, one API-base helper, check content type in `syncWithActiveSolver`. | Visible bugs. | 3 h |
| 7 | B4 + B5 + B6: run the solver in a worker thread, add limits, validate inputs. | Stability. | 4 h |
| 8 | D2 + D3: complete requirements, add a Dockerfile, host the backend. | Deployed site works. | 1 day |
| 9 | A8: fix the docs and UI labels. | Credibility. | 2 h |
| 10 | Section 4.2 items: build recipe, refusal, constrained decoding. | Real AI feature. | 3 to 5 days |
| 11 | C10 + C11: delete dead code, split the viewer. | Maintainability. | 1 to 2 days |
| 12 | D4: frontend tests, lint, coverage gate. | Regression safety. | 1 day |

---

## 8. Not analyzed (open questions)
- Rust sidecar correctness and speed. Run `cargo test --release` in `rust-sidecar/`.
- Whether the deployed Vercel site behaves as C3 predicts.
- The physics inside the shipped WASM (no source).
- Accessibility, mobile layout, and browser compatibility.
- The exact reason the "Local Qwen unavailable" message appeared in the user's earlier run.
