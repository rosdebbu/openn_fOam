/**
 * OpenZess Project Persistence — Server Snapshots with Offline Fallback
 *
 * Bridges the studio UI to the backend /api/projects REST endpoints
 * (backend/projects.py). A saved project stores the COMPLETE state —
 * physics params, custom geometry spec, dict overrides — so a reopened
 * localhost session restores the latest changes instead of defaults.
 *
 * Fallback: when the FastAPI server is unreachable (pure-static hosting),
 * snapshots are mirrored into localStorage so "Save" still works.
 */

export interface SavedProjectMeta {
  name: string;
  displayName: string;
  savedAt: string;
  savedAtEpoch?: number;
  archetype?: string;
}

export interface SaveResult {
  ok: boolean;
  backend: boolean;
  meta?: SavedProjectMeta;
  error?: string;
}

const LS_PROJECT_PREFIX = 'openzess.project.';
const LS_INDEX_KEY = 'openzess.projects.index';
const LS_LAST_KEY = 'openzess.lastProject';

function resolveApiHost(): string {
  const envApi = (import.meta as any).env?.VITE_API_URL;
  return envApi || (window.location.host.includes('5173') ? 'http://127.0.0.1:8000' : '');
}

export function safeProjectName(name: string): string {
  const cleaned = String(name || '')
    .trim()
    .replace(/[^a-zA-Z0-9_\-]/g, '_')
    .slice(0, 64);
  return cleaned || 'openzess_project';
}

/* ---------------- localStorage fallback helpers ---------------- */

function lsKey(name: string): string {
  return LS_PROJECT_PREFIX + safeProjectName(name);
}

function lsWriteMeta(meta: SavedProjectMeta): void {
  try {
    const raw = localStorage.getItem(LS_INDEX_KEY);
    const index: SavedProjectMeta[] = raw ? JSON.parse(raw) : [];
    const next = index.filter((m) => m.name !== meta.name);
    next.unshift(meta);
    localStorage.setItem(LS_INDEX_KEY, JSON.stringify(next.slice(0, 100)));
  } catch {
    /* storage unavailable */
  }
}

function lsList(): SavedProjectMeta[] {
  try {
    const raw = localStorage.getItem(LS_INDEX_KEY);
    return raw ? (JSON.parse(raw) as SavedProjectMeta[]) : [];
  } catch {
    return [];
  }
}

function lsSave(name: string, state: Record<string, unknown>): SavedProjectMeta {
  const meta: SavedProjectMeta = {
    name: safeProjectName(name),
    displayName: String(name || safeProjectName(name)),
    savedAt: new Date().toLocaleTimeString(),
    savedAtEpoch: Date.now(),
    archetype: String((state as any)?.params?.archetype || '')
  };
  try {
    localStorage.setItem(
      lsKey(name),
      JSON.stringify({
        name: meta.name,
        displayName: meta.displayName,
        savedAt: meta.savedAt,
        savedAtEpoch: meta.savedAtEpoch,
        state
      })
    );
    lsWriteMeta(meta);
  } catch {
    /* storage unavailable */
  }
  return meta;
}

function lsLoadState(name: string): Record<string, unknown> | null {
  try {
    const raw = localStorage.getItem(lsKey(name));
    if (!raw) return null;
    return (JSON.parse(raw) as any).state ?? null;
  } catch {
    return null;
  }
}

function lsDelete(name: string): void {
  try {
    localStorage.removeItem(lsKey(name));
    const index = lsList().filter((m) => m.name !== safeProjectName(name));
    localStorage.setItem(LS_INDEX_KEY, JSON.stringify(index));
  } catch {
    /* storage unavailable */
  }
}

/* ---------------- Public API ---------------- */

export async function saveProject(name: string, state: Record<string, unknown>): Promise<SaveResult> {
  // Always mirror to localStorage first so offline/static hosting still persists.
  const localMeta = lsSave(name, state);
  try {
    const resp = await fetch(`${resolveApiHost()}/api/projects/save`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, state })
    });
    if (resp.ok) {
      const data = await resp.json();
      return { ok: true, backend: true, meta: data?.project || localMeta };
    }
    return { ok: true, backend: false, meta: localMeta, error: `Server responded ${resp.status}` };
  } catch (err: any) {
    return { ok: true, backend: false, meta: localMeta, error: String(err?.message || err) };
  }
}

export async function fetchProjects(): Promise<{ projects: SavedProjectMeta[]; backend: boolean }> {
  try {
    const resp = await fetch(`${resolveApiHost()}/api/projects`);
    if (resp.ok) {
      const data = await resp.json();
      return { projects: (data?.projects || []) as SavedProjectMeta[], backend: true };
    }
  } catch {
    /* backend offline -> localStorage index */
  }
  return { projects: lsList(), backend: false };
}

export async function loadProjectState(name: string): Promise<Record<string, unknown> | null> {
  try {
    const resp = await fetch(
      `${resolveApiHost()}/api/projects/load?name=${encodeURIComponent(safeProjectName(name))}`
    );
    if (resp.ok) {
      const data = await resp.json();
      if (data?.state) return data.state as Record<string, unknown>;
    }
  } catch {
    /* backend offline -> localStorage snapshot */
  }
  return lsLoadState(name);
}

export async function deleteProject(name: string): Promise<boolean> {
  lsDelete(name);
  try {
    const resp = await fetch(
      `${resolveApiHost()}/api/projects?name=${encodeURIComponent(safeProjectName(name))}`,
      { method: 'DELETE' }
    );
    return resp.ok;
  } catch {
    return false; // localStorage removal already succeeded
  }
}

export function rememberLastProject(name: string): void {
  try {
    localStorage.setItem(LS_LAST_KEY, safeProjectName(name));
  } catch {
    /* ignore */
  }
}

export function getLastProjectName(): string | null {
  try {
    return localStorage.getItem(LS_LAST_KEY);
  } catch {
    return null;
  }
}