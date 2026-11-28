# Verification brief: PROJECT_ANALYSIS.md

**Audience:** a second agent or a teammate who checks the claims in [PROJECT_ANALYSIS.md](PROJECT_ANALYSIS.md).
**Rule:** Do not trust the report. Run each command. Write PASS, FAIL or NOT RUN with the output you saw.
**Do not edit code.** Do not stop processes you did not start.
**Shell:** PowerShell. Run from the repo root `openn_fOam\` unless a step says `frontend\`.
**Table note:** inside the tables, `\|` is a markdown escape. Type a plain `|` when you run the command.

---

## 0. Setup, and the two npm errors that already happened

### 0.1 `ENOLOCK` from `npm audit`
- **Cause:** you ran it in the repo root. The root has no `package-lock.json`.
- **Fix:** run npm commands inside `frontend\`.

### 0.2 `EPERM ... unlink ... rolldown-binding.win32-x64-msvc.node` from `npm ci`
- **Cause:** a running Vite dev server loaded that native `.node` file. Windows will not delete a file a process has open. At the last check, PID 40540 ran `vite.js --host 0.0.0.0 --port 5173` and held it.
- **Damage:** `npm ci` deletes `node_modules` first, then installs. It stopped half way. At the last check `frontend\node_modules` had only 19 top-level entries, and `vue` and `vite` had no `package.json`. The dev server on port 5173 may break on its next reload.
- **`package.json` and `package-lock.json` are intact.** `git status` shows them unchanged.
- **Repair:**

```powershell
# 1. Stop every Vite dev server (close its terminal, or:)
Get-CimInstance Win32_Process -Filter "Name='node.exe'" | Where-Object { $_.CommandLine -match 'vite' } | Select-Object ProcessId, CommandLine
# Stop-Process -Id <PID>        # only for a server you own

# 2. Reinstall
cd frontend
npm ci

# 3. Check
npx vue-tsc -b
npm run build
```

- If `npm ci` fails again with `EPERM`: close editors that open the folder, pause OneDrive sync for this folder, and try again. The repo lives inside OneDrive (`...\OneDrive\Documents\GitHub\...`). OneDrive can lock files in `node_modules`. A repo outside OneDrive avoids this problem.
- You do **not** need `npm ci` to verify most claims here. You only need it for steps V-C12, V-D7 and for running the frontend. `npm audit` alone works with the existing lockfile.

### 0.3 Optional: start a test backend on a spare port
Steps V-B4 and V-B6 need a backend that you start yourself.

```powershell
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8010
```

Stop it with Ctrl+C when you finish. Do not use port 8000. Another process may own it.

---

## 1. Verification steps

`Evidence` in the report: VERIFIED = Claude ran it. INFERRED = Claude did not run it (marked below).

### A. Research integrity

| ID | Command | Expect |
|---|---|---|
| A1 | `Select-String -Path wasm-solver\*.c, wasm-solver\*.cpp, wasm-solver\src\*.rs -Pattern "fvm_step\|fvm_create\|fvm_paint_obstacle"` | **No output.** No source defines the `fvm_*` API. |
| A1 | `Select-String -Path frontend\public\wasm\fvm_solver.js -Pattern "_fvm_get_turbulence" -List` | One match. The shipped binary exposes a turbulence API. |
| A1 | `Select-String -Path wasm-solver\compile_wasm.bat -Pattern "openfoam_solver.js"` | A match. The script writes a different file than the one the app loads. |
| A2 | `Select-String -Path README.md -Pattern "41 × 41"` and `Get-Content docs\IEEE_BENCHMARK_RESULTS.md -TotalCount 12` | README: `0.0385`. IEEE doc: `0.2381`, and the RMSE rises with refinement (0.2200 to 0.2381). |
| A3 | `Select-String -Path scripts\run_ieee_benchmarks.py -Pattern 'res.get\("cfl"'` and `Select-String -Path scripts\train_openzess_grpo.py -Pattern '"cfl_max"'` | The first script reads `cfl`. The function returns `cfl_max`. The doc shows Max CFL `0.000` on every row. |
| A4 | `Select-String -Path scripts\train_openzess_grpo.py -Pattern "for _ in range\(12\)"` | A match (line 146 on 2026-11-28). |
| A5 | `Select-String -Path scripts\train_openzess_grpo.py -Pattern "ghia_rmse < 0.65"` | A match (line 264). Observed RMSE is about 0.23, so the test is always true. |
| A6 | NOT REPRODUCIBLE FROM THE REPO. | Claude ran one 12-prompt probe in a scratch folder: the base model gave valid JSON 12 of 12. The script is not in the repo. Treat this claim as **unverified** until someone re-runs the ablation on a held-out set. |
| A7 | `git check-ignore -v openzess_qwen3_0.6b_rl` | `.gitignore:53:openzess_qwen3_0.6b_rl/`. Also: `git status --short openzess_qwen3_0.6b_rl_sft` shows `??` (untracked). |
| A8 | `foreach ($f in 'backend\solver_3d.py','backend\mesh_3d.py','backend\ai_vision_engine.py','backend\vtk_writer_3d.py') { "$f : $(Test-Path $f)" }` | All `False`. |
| A8 | `Select-String -Path frontend\package.json -Pattern "chart.js\|tailwind"` | **No output.** `docs\TECH_STACK.md` lists both. |

### B. Security and robustness

| ID | Command | Expect |
|---|---|---|
| B1 | `Select-String -Path backend\app.py -Pattern 'agent-desktop/(click\|type\|screenshot\|launch-paraview)'` | 4 routes. |
| B1 | `Select-String -Path backend\app.py -Pattern "Depends\|HTTPBearer\|api_key\|Authorization"` | **No output.** No auth code. |
| B2 | `Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue \| Select-Object LocalAddress, OwningProcess` | At the time of the report: `0.0.0.0`. This depends on who started the server. If it shows `127.0.0.1` or nothing, the finding does not apply right now. Report what you see. |
| B3 | Same as B1, plus `Select-String -Path backend\app.py -Pattern 'delete\("/api/projects"'` | Route exists with no auth. |
| B4 | Start the backend (0.3), then `python scripts\verify_backend_limits.py` | Line `/api/health WHILE simulating:` shows a median clearly above the idle value (Claude saw 484 ms vs 216 ms, and 4 pings instead of about 20). Numbers vary by machine. |
| B5 | `Select-String -Path backend\app.py -Pattern "^MAX_GRID\|^MAX_ITERATIONS"` | `MAX_GRID = 256`, `MAX_ITERATIONS = 20000`. |
| B6 | Same script as B4. | `Re=0` and `Re=-5`: `frames=3 err=None`. `Re=1e12`: `frames=1 err=None`. `gridResolution='abc'`: the connection closes without a close frame. |
| B7 | `Select-String -Path backend\app.py -Pattern "^last_results"` | A module-level `last_results = {}`. |
| B8 | INFERRED. Not tested. | To test: send a request with a `Host:` header that is not `localhost`. Does the server answer? |
| B9 | `Select-String -Path frontend\src\utils\aiCopilot.ts -Pattern "dangerouslyAllowBrowser"` | A match. |
| B10 | `git ls-files .vscode data saved_chats` | Files are listed. `.vscode\mcp.json` holds `C:\Users\ROSHNI\...` paths. |
| B11 | `git grep -InE "sk-[A-Za-z0-9]{20,}\|AIza[0-9A-Za-z_-]{30,}\|ghp_[A-Za-z0-9]{30,}" -- . ":!graphify-out" ":!frontend/package-lock.json"` | **No output.** |
| B11 | `cd frontend; npm audit --omit=dev` | `found 0 vulnerabilities`. **A teammate already ran this and saw it.** |

### C. Application bugs

| ID | Command | Expect |
|---|---|---|
| C1 | `Select-String -Path frontend\src\components\ParaViewGlanceViewer.vue -Pattern "else customReynolds.value = reVal"` | A match inside `sendAiChat`. The preset watcher reads `pendingPresetRe`, which this path never sets. NOT run in a browser: confirm by typing `cylinder at Re=900` in the **AI Chat** tab and reading `nu` in the Log tab. If `nu` is not `0.00111`, the bug is real. |
| C2 | `Get-ChildItem frontend\src -Recurse -Include *.vue,*.ts \| Select-String -Pattern ":8000"` | About 9 hits in 6 files. |
| C3 | INFERRED. | Read `syncWithActiveSolver` in the viewer (it trusts `res.ok`) and `frontend\vercel.json` (rewrite `/(.*)` to `/index.html`). To test, deploy or run `vercel dev`, then open the Sync action. |
| C4 | `Select-String -Path frontend\src\components\ParaViewGlanceViewer.vue -Pattern "generateProceduralCfdData\(41, 41"` | 3 matches. |
| C5 | `Select-String -Path frontend\src\components\ParaViewGlanceViewer.vue -Pattern "new OpenFoamWasmEngine\(41, 41"` | 2 matches. |
| C10 | `foreach ($n in 'AiAssistant','CfdCanvas2D','HelloWorld','OpenFoamDictEditor','OpenFoamTerminal','cfdWorker') { $c = @(Get-ChildItem frontend\src -Recurse -Include *.vue,*.ts \| Select-String -Pattern $n -List \| Where-Object { $_.Filename -notlike "$n.*" }).Count; "$n importers: $c" }` | `0` for each. |
| C11 | `(Get-Content frontend\src\components\ParaViewGlanceViewer.vue).Count` | More than 4,000 lines. It was 4,724 on 2026-11-28 and keeps growing. |
| C12 | After `npm run build`: `Get-ChildItem frontend\dist\assets \| Sort-Object Length -Descending \| Select-Object -First 3 Name, Length` | The largest file is about 1.8 MB. Needs a repaired `node_modules` (section 0.2). |

### D. Repo and operations

| ID | Command | Expect |
|---|---|---|
| D1 | `git count-objects -vH` and `(git ls-files rust-sidecar/tools/rustbuild \| Measure-Object).Count` | A large pack (Claude saw a 380 MB `.git`). About 2,159 tracked files under `rustbuild` (of 2,356 in the whole repo). `Select-String -Path .gitignore -Pattern "rustbuild"` gives no output. |
| D2 | `Get-Content requirements.txt` | 6 lines, no `torch`, `transformers`, `peft`, `laya`. |
| D3 | `Get-ChildItem Dockerfile*, docker-compose*, fly.toml, render.yaml -ErrorAction SilentlyContinue` | No output. |
| D4 | `python -m coverage run --source=backend -m pytest -q; python -m coverage report` (then delete the `.coverage` file) | 93 passed. TOTAL about 66%. `app.py` about 52%, `text_to_3d.py` 0%. |
| D6 | `python -m ruff check backend tests scripts\train_openzess_grpo.py scripts\run_ieee_benchmarks.py main.py --statistics` | 25 errors, all style. The two probe scripts added later (`verify_*.py`) add 13 more style errors. Not logic errors. |
| D7 | `cd frontend; npm outdated` | Several packages behind (for example `@anthropic-ai/sdk` 1.5.0 to 1.14.0). |
| D9 | `Get-Content .github\workflows\ci.yml` | 3 jobs: pytest (3.10 and 3.13), `cargo test`, frontend build. No lint, no frontend tests. |

---

## 2. Things the report did not check
- Rust sidecar: `cd rust-sidecar; cargo test --release`.
- The deployed Vercel site (C3 is inferred).
- Accessibility, mobile layout, browser compatibility.
- The physics inside `fvm_solver.wasm`.

## 3. Report format

```
<ID>: PASS | FAIL | NOT RUN
Evidence: <command output, trimmed>
Notes: <one line>
```

End with a list of claims in `PROJECT_ANALYSIS.md` that the commands do not support, and any line numbers that moved.
