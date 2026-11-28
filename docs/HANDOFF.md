# OpenZess Studio — Handoff (branch `anshu/handoff-solver-fix`)

Written 2026-11-28. Base: `main` at `ea2211d`. `main` is NOT changed. All work below is only on this branch, so you can compare, test, or discard it.

## 1. What this branch holds
All uncommitted work from the working session, in one commit. To see exactly what changed from `main`:

```powershell
git diff main..anshu/handoff-solver-fix --stat
git diff main..anshu/handoff-solver-fix -- frontend/src backend tests
```

To throw the work away and go back: `git checkout main`. Nothing on `main` is lost.

### Changed files (existing code)
| File | Change |
|---|---|
| `frontend/src/utils/openfoamWasmBridge.ts` | Pressure sweeps now `max(60, 2.6*max(nx,ny))` instead of 20. Fixes solver blow-up. |
| `frontend/src/components/ParaViewGlanceViewer.vue` | `WASM_GRID = 61`; AI Run rewrite; Custom Geometry panel; VTK export reads grid size from data. |
| `frontend/src/components/OpenZessBoardStage.vue` | Streaklines, smooth 4x field, RK4 streamlines, footprint-true bodies. |
| `backend/app.py`, `backend/ai_simulate.py` | `_parse_primitives`, `max_new_tokens=300`, `explicit_reynolds`, `source` flag. |
| `tests/test_ai_simulate.py` | 4 new tests. |

### New files
`frontend/src/utils/obstacleGeometry.ts` (+ `.check.ts`), `tests/test_parse_primitives.py`, `scripts/verify_*.py`, `scripts/run_ieee_benchmarks.py`, `backend/text_to_3d.py`, `openzess_qwen3_0.6b_rl_sft/` (LoRA adapter, 49 MB), `data/generated_3d/`, `docs/*.md`, `docs/architecture_audit.html`, `.agents/rules/asd-ste100.md`, `.claude/launch.json`, `frontend/vercel.json`.

Also changed: `graphify-out/*` (auto-generated knowledge graph; safe to ignore or regenerate).

## 2. Known state (read before you trust anything)
- **Tested only in a scratch copy** of `frontend/` (its own `node_modules`). Not tested in the repo `frontend/` folder, because that `node_modules` is damaged (see section 4).
- Backend tests: 93 passed at the time of the AI Run fixes. Run again on your laptop.
- Solver: 8/8 presets stable for 1,680 steps each, about 36 ms per tick at 61x61.
- **Not fixed / not verified:**
  - Source code of `fvm_solver.wasm` and `fea_structure.wasm` is NOT in the repo. The solver was fixed from outside by changing the `step()` argument.
  - Flow is 2-D plan view. A "car" is the flow around its top-down outline.
  - FSI stress reads about 0.005 MPa. Not examined.
  - Spaceship preset once took 113 ms per tick. Not repeated.
  - Chat tab still loses the Reynolds number (item C1 in `PROJECT_ANALYSIS.md`).
  - Model never refuses a bad prompt.
  - Paper claims (3-D, PINN, R^2, SIMD speed-ups) are not supported by the code.
  - Backend binds to `0.0.0.0:8000` and agent-desktop endpoints have no auth.
- Debjit reported that something is broken. Not identified yet. First step: run section 5 on `main`, then on this branch, and compare.

## 3. What to install on the new laptop
| Item | Version used here | Notes |
|---|---|---|
| Git | any recent | clone the repo |
| Node.js | 22.x (22.23.2) | npm 12.0.2 here |
| Python | 3.12 (3.12.10) | |
| Python packages | `requirements.txt` + `requirements-dev.txt` | fastapi, uvicorn, numpy, scipy, matplotlib, websockets, pytest, httpx2 |
| **For the AI model (optional)** | | `torch`, `transformers`, `peft` — NOT in `requirements.txt`; install by hand |
| Base model | `Qwen/Qwen3-0.6B` (Hugging Face) | auto-downloads on first run (about 1.2 GB). The LoRA adapter is in `openzess_qwen3_0.6b_rl_sft/` in this repo. |
| GPU | optional | Code mentions an RTX 5050. CPU works but is slow. |
| Editor / agent | VS Code or Claude Code | |

Without `torch/transformers/peft`, the backend still starts. The "Instant preview" and WASM modes work. Only the Qwen path fails.

```powershell
git clone https://github.com/rosdebbu/openn_fOam.git
cd openn_fOam
git checkout anshu/handoff-solver-fix

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
# optional, for the AI model:
pip install torch transformers peft

cd frontend
npm ci
```

Windows tip: do NOT keep the repo inside OneDrive. OneDrive locks files in `node_modules` and causes `EPERM` errors on `npm ci` (this is what damaged the first laptop). Use a path such as `C:\dev\openn_fOam`.

## 4. The `node_modules` problem on the first laptop
`frontend/node_modules` is half-deleted after a failed `npm ci` (EPERM on `@rolldown/binding-win32-x64-msvc`). A Vite process (PID 40540) held the lock. Fix there: stop Vite, delete `frontend\node_modules`, run `npm ci`. On a new laptop this does not apply.

## 5. Run and verify
```powershell
# backend (repo root)
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
# tests (repo root, second terminal)
python -m pytest -q
# frontend
cd frontend
npm run dev          # http://localhost:5173
npx vue-tsc -b       # type check
npm run build
```

Browser checks (details and a console snippet: `docs/VERIFY_CHANGES.md`, Round 3):
1. Open the app, pick each preset. The peak speed must stay about 1.0 to 1.64. It must not grow to 10, 150 or more.
2. The field must not reset about every 10 s.
3. Streaklines must be smooth. No right-angle zigzags.
4. Cylinder shows an ellipse footprint, not a lying cylinder.

If a check fails, compare with `main` to see if this branch caused it.

## 6. Where to read next (all in `docs/`)
- `PROJECT_ANALYSIS.md` — full stack and flaw list (rows C1 to C16, D1 to D10).
- `GAP_ANALYSIS.md` — what is missing.
- `VERIFY_CHANGES.md` — each change, how to check it (Rounds 1 to 3).
- `VERIFY_ANALYSIS.md` — how to check the analysis.
- `architecture_audit.html` — architecture diagram.
- `COLLABORATOR_README.md` (repo root) — original team handbook.

## 7. Prompt for the next Claude session
Paste this into a new session on the new laptop:

> I work on OpenZess Studio (Vue 3 + Three.js + vtk.js frontend, WASM finite-volume solver, FastAPI backend, Qwen3-0.6B LoRA). I am on branch `anshu/handoff-solver-fix`. Read `docs/HANDOFF.md` first, then `docs/VERIFY_CHANGES.md`. Reply in ASD-STE100 simplified English. Do not change code when I ask for analysis only. First task: set up the environment from HANDOFF section 3, run the tests and the browser checks from section 5, and tell me if anything differs from "Known state". My partner says something broke after these changes: compare this branch with `main` and find it. Do not commit or push to `main`. Do not stop processes I did not start.

## 8. Rules the owner set
- Write answers in ASD-STE100 style.
- Analysis requests = no code changes.
- Ask before commit, push, delete or stop a process.
