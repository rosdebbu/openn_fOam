# 🚀 How to Run, Test, and Develop

A quickstart developer guide for collaborators to get OpenZess Studio running on their local machine within 2 minutes.

---

## 1. Prerequisites

Make sure the following tools are installed on your machine:
* **Python 3.10+**: With `pip`
* **Node.js 18+**: With `npm`
* *(Optional)* **Rust toolchain (`cargo`)**: Only needed if compiling the Rust SIMD inner loop. If absent, the Python SciPy sparse solver runs automatically!

---

## 2. Quickstart (One-Click Launch on Windows)

Simply double-click:
```cmd
LAUNCH_STUDIO.bat
```
This batch script will:
1. Verify Python & Node.js environment.
2. Install Python dependencies (`requirements.txt`).
3. Build the Vue 3 frontend (`npm run build`).
4. Start the FastAPI backend on `http://127.0.0.1:8000`.
5. Automatically open `http://localhost:8000/studio/index.html` in your default browser.

---

## 3. Manual Development Setup

If you prefer running services manually with live development reloading:

### Terminal 1: Backend (FastAPI)
```bash
# Navigate to repository root
cd openn_fOam

# Install dependencies
pip install -r requirements.txt

# Start backend with auto-reload enabled
python main.py
# Server starts at: http://127.0.0.1:8000
```

### Terminal 2: Frontend (Vue 3 + Vite)
```bash
# Navigate to frontend
cd frontend

# Install npm packages
npm install

# Start Vite dev server
npm run dev
# Vite runs at: http://localhost:5173

# OR build production bundle into frontend/dist
npm run build
```

---

## 4. Key Endpoints Cheatsheet

| Endpoint | Method | Purpose |
| :--- | :---: | :--- |
| `http://localhost:8000/studio/index.html` | `GET` | OpenZess Studio Web UI |
| `/api/health` | `GET` | System health, active solver type, uptime |
| `/api/simulate` | `POST` | Execute 1 simulation step with current physics settings |
| `/api/projects` | `GET` | List all saved simulation project snapshots |
| `/api/projects/save` | `POST` | Save current project parameters to disk |
| `/api/projects/load/{id}` | `GET` | Load a saved simulation project |
| `/api/export-openfoam` | `POST` | Download production-ready OpenFOAM ZIP case directory |

---

## 5. Git & Collaboration Best Practices

1. **Working on Features:**
   * Create a feature branch: `git checkout -b feature/your-feature-name`
2. **Before Committing:**
   * Always verify the frontend compiles cleanly:
     ```bash
     cd frontend && npm run build
     ```
   * Make sure backend starts cleanly without syntax errors:
     ```bash
     python -c "import main; print('Backend syntax OK')"
     ```
3. **Commit Messages:**
   * Use conventional commit headers:
     * `feat(...)`: New features
     * `fix(...)`: Bug fixes
     * `docs(...)`: Documentation updates
     * `refactor(...)`: Code cleanup
