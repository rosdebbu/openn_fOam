# OpenZess Studio — frontend

Vue 3 + TypeScript + Vite + Three.js. See the repository root `README.md` for
the full project.

```bash
npm ci            # install exact locked dependencies
npm run dev       # dev server on :5173 (talks to the backend on 127.0.0.1:8000)
npm run build     # type-check (vue-tsc) + production bundle in dist/
```

`python main.py` in the repository root rebuilds `dist/` automatically when
the sources are newer, then serves it at `http://localhost:8000/studio/`.

Everything the viewport, solver log, residual chart and telemetry show comes
from solver frames streamed over `/ws/simulate`; nothing is synthesized in the
browser.
