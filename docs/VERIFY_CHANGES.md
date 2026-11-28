# Verification brief: AI Run and browser geometry changes

**Audience:** a second agent that checks this work.
**Rule:** Do not trust this file. Run every command. Report PASS or FAIL for each claim with the output you saw.
**Do not edit code.** Do not stop processes you did not start. Another backend may already listen on port 8000.

---

## 1. Context

OpenZess Studio is a browser CFD platform. Frontend: Vue 3 + WebAssembly solver (`fvm_solver.wasm`). Backend: FastAPI + a small Qwen3-0.6B model with a LoRA adapter (`openzess_qwen3_0.6b_rl/`).

The user complained that the "AI Run" button "just does things". The work below fixes the causes that could be fixed without retraining the model.

## 2. Scope boundary (important)

Two parties edited the same files in the same session.

| Party | What they did |
|---|---|
| **Claude (this brief)** | The changes in section 3. |
| **Another tool** (probably Antigravity; it created `.agents/rules/asd-ste100.md`) | The Build tab, the AI Chat tab, `_run_ai_pipeline`, `_procedural_primitives_for_idea`, `_PRIMITIVE_SYSTEM_PROMPT`, `custom_primitives`, preset id 8, `OpenZessBoardStage.vue`, `openfoamWasmBridge.ts` edits. |

Nothing is committed. `git diff` shows both parties mixed. Use the anchors in section 3 to find only the Claude changes. Do not judge the other tool's code unless a claim here depends on it.

## 3. What Claude changed

### 3.1 This round: AI Run and the backend

| ID | File | Anchor (search for this) | Change | Reason |
|---|---|---|---|---|
| C1 | `backend/app.py` | `def _parse_primitives` | New function. It reads every complete `{...}` part with a `kind` key. It ignores code fences. It keeps parts from a reply that was cut off. | The old code ran `json.loads` on the whole reply. A reply cut at the token limit failed, so the app used a keyword template. |
| C2 | `backend/app.py` | `max_new_tokens=300` | Raised from 180 to 300 in the primitives branch. | The reply needs about 250 tokens. |
| C3 | `backend/app.py` | `from_model`, `"source"` | The reply now has `source: "model" or "template"`. The `engine` and `message` text say which one was used. Same for the offline template return. | The old message said "Synthesized N parts" even for a keyword template. |
| C4 | `backend/ai_simulate.py`, `backend/app.py` | `explicit_reynolds` | New helper. A Reynolds number typed by the user ("Re=900") now beats the model's number. Used in `build_spec`, `normalize_rl_spec`, and the primitives branch. | "cylinder at Re=900" ran at Re=600. |
| C5 | `ParaViewGlanceViewer.vue` | `function findLocalPreset` | New function. It returns `null` when no keyword matches. `inferLocalPresetFromPrompt` is now a wrapper that keeps the old house default for other callers. Its regex list also gained `house\|home\|cottage` before the `null`. | Old code returned a house for any unmatched text. |
| C6 | `ParaViewGlanceViewer.vue` | `pendingPresetRe` | A module variable. AI Run sets it before changing `wasmPreset`. The `wasmPreset` watcher reads it once and passes it to `initPresetPreview`. | The watcher called `initPresetPreview(nextPreset)` without a Re. The preset's own Re won, while the label showed the typed Re. |
| C7 | `ParaViewGlanceViewer.vue` | `async function routeWithLayaAi` | Rewritten after the first `synthesizeCustomPrimitives` block. (a) If the backend returns `custom_primitives`, run those parts, not the old `builderPrimitives`. (b) No empty `catch`. A failed fetch or non-200 sets a message. (c) Backend failure falls back to `findLocalPreset`. (d) No match shows "Not understood" and changes nothing. (e) Offline keyword path reads a typed Re (`typedRe`). (f) 90 s timeout. | See section 1. |
| C8 | `ParaViewGlanceViewer.vue` | `keyword template` | The car, lander, boat and drone block now says "keyword template" in the status and the log. | It is a fixed template, not a model. |

### 3.2 Earlier in the session

| ID | File | Change |
|---|---|---|
| E1 | `frontend/src/utils/obstacleGeometry.ts` (new) | `primitivesFromObstacleSpec`: converts the Custom Geometry Builder spec `{shape,cx,cy,size,aoa}` (0 to 1) to `CustomPrimitive[]` (-1 to 1). Clamps centres to the domain. The airfoil angle of attack is an approximation (capsule thickness). |
| E2 | `frontend/src/utils/obstacleGeometry.check.ts` (new) | Assert-based self-check. 62 checks. |
| E3 | `ParaViewGlanceViewer.vue` | Group "Custom Geometry (In-Browser Solver)" at the top of the Properties tab. Anchors: `Custom Geometry (In-Browser Solver)`, `runCustomGeometry`, import of `obstacleGeometry`. The refs `builderShape`, `builderCx`, `builderCy`, `builderSize`, `builderAoa`, `builderRe` were added by Claude. **`builderRe` is also used by the other tool's Build tab.** |
| E4 | `.claude/launch.json` (new) | Dev-server launch config (`npm run dev --prefix frontend`). |
| E5 | `docs/architecture_audit.html` (new) | Audit report with two SVG figures. Published (private) at https://claude.ai/artifact/LNPWahbmHEcQroZzVfon8x |
| E6 | `tests/test_parse_primitives.py` (new, 5 tests), `tests/test_ai_simulate.py` (4 tests appended) | Tests for C1 and C4. |
| E7 | `scripts/verify_primitive_parsing.py` (new) | Reproduces the "model parts were almost never used" finding. |

## 4. Verification steps

Run from the repo root `openn_fOam/` in PowerShell.

### V1. Backend tests
```powershell
python -m pytest tests -q
```
**Expect:** `93 passed`. (84 before. 5 in `test_parse_primitives.py` and 4 in `test_ai_simulate.py` were added.)

### V2. Frontend typecheck
```powershell
cd frontend; npx vue-tsc -b; cd ..
```
**Expect:** no errors, no output besides npm notices.

### V3. Geometry adapter self-check
```powershell
cd frontend
$out = Join-Path $env:TEMP "geomcheck"
npx tsc --ignoreConfig --outDir $out --target es2022 --module commonjs --skipLibCheck --strict src/utils/obstacleGeometry.check.ts
node "$out/obstacleGeometry.check.js"
cd ..
```
**Expect:** 62 lines starting with `ok`, then `ALL CHECKS PASSED`.
(Claude first said 65 checks. The correct number is 62.)

### V4. Model finding (needs the GPU, takes about 6 to 10 minutes)
```powershell
python scripts/verify_primitive_parsing.py
```
**Expect (Claude's run):** the last line shows the OLD method usable on about 1 of 12 prompts and the NEW method on 12 of 12.
Sampling and GPU differences can change the old count slightly. The new count should stay at or near 12.
**Observed result:** `OLD 1/12, NEW 12/12` (see section 6).

### V5. Live checks in the browser
Prerequisites:
1. Backend: `python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000`. If port 8000 is busy, do not stop the other process. Check what it is first (`Get-NetTCPConnection -LocalPort 8000`).
2. Frontend: `npm run dev --prefix frontend`. Open the printed URL.
3. Use the text box "Laya AI Router" at the top. Type a prompt and press Enter. The first model call loads the model and can take 30 to 60 s.
4. Read the solver value from the **Log** tab or the "LIVE OPENFOAM DICT" panel: the line `nu [0 2 -1 0 0 0 0] <value>; // Re = <n>`. The value must equal 1 / Re.

| # | Prompt | Expect |
|---|---|---|
| L1 | `airflow past a cylinder at Re=900` | Header says `cylinder (Re=900)`. Solver line shows `nu ... 0.00111 ... Re = 900`. (Before the fix it said Re=600.) |
| L2 | `a dragon` | Header says `dragon (model, Re=<n>)`. The panel text says "Model-designed geometry (N parts)". |
| L3 | Block the backend (run this in the page console first), then `qwerty zzz` | Header says `Not understood`. The flow does not change. |
| L4 | Backend blocked, then `airfoil at Re=700` | Preset changes to the airfoil. Solver shows `0.00143 ... Re = 700`. This is the original bug case (the preset changes). |

Console snippet for L3 and L4:
```js
window.__of = window.__of || window.fetch;
window.fetch = (u, o) => String(u).includes('/api/ai/') ? Promise.reject(new TypeError('Failed to fetch')) : window.__of(u, o);
```

### V6. In-browser custom geometry (E1 and E3, no backend needed)
Open **Properties**. Choose a shape, set size and Re, click **Solve This Geometry**.
**Expect:** the solver restarts, the log tab opens, the diorama shows the new body, and `nu` matches 1 / Re. Try `house` at Y = 0.85 and size 0.35: the roof must stay inside the domain.

## 5. Weak points. Please attack these.

1. **"12 of 12 usable" does not mean the shapes are good.** I only checked that the JSON parses. "golf ball" came out as three capsules. Nobody judged the geometry.
2. **The sample is small.** 12 prompts, 1 seed, RL adapter only.
3. **The model never refuses.** `asdf qwerty zzz` produced a shape named "asdf" with source `model`. Not fixed.
4. **The chat tab still has the Re-drop bug.** `sendAiChat` calls `wasmPreset.value = ...` and then `customReynolds.value = reVal`. The watcher passes `undefined`, so `initPresetPreview` uses the preset's own Re. I did not change `sendAiChat`. Confirm or refute this by reading the code and, if you can, in the browser.
5. **`builderRe` is shared.** My Properties slider and the other tool's Build slider write the same ref. I did not test whether they disturb each other.
6. **The keyword block still runs first.** In `routeWithLayaAi`, words like car, lander, boat and drone return a fixed template before the backend is called. A model never sees "a drone".
7. **Old regex quirks remain** in `findLocalPreset`: `sub` matches "substance", `water` maps to the venturi, `box` maps to the cavity. These were there before.
8. **`house|home|cottage` was added to `findLocalPreset`.** A prompt such as "simple" alone now gives "Not understood" in offline mode. Before it gave a house.
9. **Latency.** One answer takes about 30 s. Not changed.
10. **Earlier wrong statements by Claude (corrected):** (a) "ImportError, torch missing". On this machine torch, transformers and peft are installed and the model loads. `requirements.txt` still lacks them for other machines. The cause of the "Qwen unavailable" message was not found. (b) "65 checks". The count is 62.
11. **Paper claim that I could not reproduce.** In a separate 12-prompt probe the untrained base model gave valid JSON 12 of 12 times. The paper says 33%. Settings differed (greedy, thinking off, 12 prompts). The paper test needs a re-run on a held-out set. This is outside this brief but matters for the paper.

## 6. Operations note

To restart a test backend, Claude stopped PID 23856, which listened on port 8000. Claude did not start it. A different process (PID 37496) now listens on `0.0.0.0:8000`. Claude's own test backends are stopped. If the user lost a dev server, they must restart it.

### Observed result of V4 (one run by Claude, 2026-11-28)

```
OLD method usable: 1/12   NEW method usable: 12/12
```

- OLD gave parts only for "a stone bridge with two pillars" (2 parts). It gave 0 parts for the other 11.
- NEW gave 3 parts for 11 prompts and 2 parts for the bridge. No prompt failed.
- The part kinds are plausible JSON, not good geometry (see weak point 1).
- One run, one seed. Run it again and compare.

### Process note (later)
After the first note above, the backend on port 8000 changed again. A `uvicorn backend.app:app --host 0.0.0.0` process (PID 12756 at the last check) now runs there. Claude did not start it.

## 7. Report format

For each of V1 to V6 and each weak point 4 to 8, write:

```
<ID>: PASS | FAIL | NOT RUN
Evidence: <command output or file:line>
Notes: <one line>
```

End with a list of anything in section 3 that does not match the code.

---

## Round 3: "the simulation does not look real" (2026-11-28)

**What the user saw:** dark dots everywhere, a flat coloured sheet, a blocky car. **Root cause:** the solver itself was unstable (see PROJECT_ANALYSIS C16). Restyling alone could not fix that.

### Changes

| ID | File | Anchor | Change |
|---|---|---|---|
| R1 | `frontend/src/utils/openfoamWasmBridge.ts` | `pressureIters` | The WASM step now runs `pressureIters` pressure sweeps (about 2.6 x grid size) instead of a fixed 20. |
| R2 | `frontend/src/components/ParaViewGlanceViewer.vue` | `WASM_GRID` | Grid 41x41 to 61x61 (two engine constructors, the log line, the chat summary). `exportCurrentVtk` now reads the grid size from the data (it hard-coded 41x41). |
| R3 | `frontend/src/components/OpenZessBoardStage.vue` | `updateDeckScalarTexture`, `FIELD_UP` | The field is drawn at 4x resolution with bilinear interpolation, iso-lines, and a steady colour range: 2nd to 98th percentile of fluid cells, eased over time. Speed starts at 0. Pressure and vorticity are centred on 0. |
| R4 | same | `updateTracers`, `sampleVelocity`, `seedTracer` | The 84 dark dots are replaced by 220 streaklines advected with RK2 through the live field. They end at bodies. The invented fallback speeds (0.7, 0.65, 0.4) and the artificial lift over houses were removed. |
| R5 | same | `streamlinesGroup` block | The Streamlines filter uses RK4 through the bilinear field (it used nearest-cell sampling, which made right-angle zigzags). 17 seeds, no invented speed, no lift. |
| R6 | same | `RoundedBoxGeometry`, `ExtrudeGeometry` | Custom parts are drawn as the plan-view footprint the solver uses: box = rounded box, cylinder and capsule = ellipse, cone = wedge. Before, a cylinder was drawn lying on its side while the solver treated it as an ellipse. |

### How to verify

1. `cd frontend; npx vue-tsc -b` gives no errors. (Needs a repaired `node_modules`, see VERIFY_ANALYSIS section 0.2.)
2. Stability test. Add this temporary line in `initPresetPreview` of the viewer, after the engine is created: `(window as any).__oz = engine;` and remove it afterwards. Then in the browser console, for each preset in the dropdown, run:
```js
const e = window.__oz; let mx = 0, series = [];
for (let k = 0; k < 120; k++) { e.step(14); if (k % 10 === 0) { mx = 0; for (let i = 0; i < e.speed.length; i++) if (e.mask[i] !== 1 && isFinite(e.speed[i]) && e.speed[i] > mx) mx = e.speed[i]; series.push(+mx.toFixed(2)); } }
({ grid: e.nx, pressureIters: e.pressureIters, series, Co: e.maxCourant })
```
   **Expect:** `grid: 61`, `pressureIters: 159`, every value in `series` below about 2, no jump above 3.
3. **Claude's results** (120 ticks = 1,680 steps each): house 1.55, cylinder 1.61, venturi 1.35, tower 1.64, cavity 1.00, airfoil 1.11, submarine 1.18, spaceship 1.19. No spikes. About 36 ms per tick (the spaceship measured 113 ms once; not repeated).
4. **To see the old bug:** set `pressureIters` back to 20 (or change `this.pressureIters` to `20` in `step`). Peak speed then jumps to 40 or more within about 10 s.
5. **Visual:** run `a car` in AI Run. Expect smooth parallel white streaklines bending around the body, red bands along its sides, no dark dots, no angular lines.

### Known limits (not fixed)
- The flow is 2-D: the solver sees the plan-view footprint. A "car" is flow around its top-down outline, not a side view.
- The WASM source is still missing (PROJECT_ANALYSIS A1). The fix was done from the outside, by changing an argument.
- FSI stress on the house and tower reads 0.005 MPa. Not examined.
- Tested in a scratch copy of `frontend/` because the repo's `node_modules` was damaged by a failed `npm ci`. The repo files were copied over, so the code is the same. A `vue-tsc` run on that copy passed.
- Tested with the browser pane hidden at times, which throttles timers. Stability numbers come from stepping the engine directly in a loop, not from the on-screen timer.
