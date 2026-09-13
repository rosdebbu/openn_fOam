<template>
  <header class="header-navbar">
    <!-- Left: Brand Logo and Title -->
    <div class="brand">
      <!-- ChatGPT-Style Sidebar Toggle Button -->
      <button
        class="sidebar-toggle-btn"
        :class="{ active: isSidebarOpen }"
        @click="$emit('toggleSidebar')"
        :title="isSidebarOpen ? 'Collapse Sidebar (Ctrl + \\)' : 'Expand Sidebar (Ctrl + \\)'"
        aria-label="Toggle Sidebar"
      >
        <svg class="sidebar-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect width="18" height="18" x="3" y="3" rx="2"/>
          <path d="M9 3v18"/>
          <path d="m14 9-3 3 3 3" v-if="isSidebarOpen"/>
          <path d="m12 9 3 3-3 3" v-else/>
        </svg>
      </button>

      <div class="logo-cube" title="OpenZess 3D Studio">
        <div class="cube-inner">
          <span class="cube-face front"></span>
          <span class="cube-face back"></span>
          <span class="cube-face right"></span>
          <span class="cube-face left"></span>
          <span class="cube-face top"></span>
          <span class="cube-face bottom"></span>
        </div>
      </div>
      <h1 class="brand-title">OpenZess 3D Studio</h1>

      <!-- Archetype Switcher Dropdown -->
      <div class="archetype-dropdown-wrapper" ref="archetypeDropdownRef">
        <button
          class="archetype-pill-btn"
          @click="showArchetypeMenu = !showArchetypeMenu"
          title="Select Simulation Type & Physical Scenario"
        >
          <span class="archetype-icon">{{ currentArchetypeInfo.icon }}</span>
          <span class="archetype-label">{{ currentArchetypeInfo.name }}</span>
          <span class="dropdown-arrow">▾</span>
        </button>

        <transition name="fade-drop">
          <div v-if="showArchetypeMenu" class="archetype-menu">
            <div class="menu-heading">Simulation Scenarios</div>
            <button
              v-for="arch in archetypes"
              :key="arch.id"
              class="archetype-menu-item"
              :class="{ selected: currentArchetype === arch.id }"
              @click="selectArchetype(arch.id)"
            >
              <span class="menu-item-icon">{{ arch.icon }}</span>
              <div class="menu-item-text">
                <strong>{{ arch.name }}</strong>
                <small>{{ arch.solver }} · {{ arch.desc }}</small>
              </div>
            </button>
          </div>
        </transition>
      </div>

      <!-- Engine Selector Dropdown (Rust Bare-Metal / PINN AI / Python SciPy) -->
      <div class="engine-dropdown-wrapper" ref="engineDropdownRef">
        <button
          class="engine-pill-btn"
          :class="solverMode || 'cfd'"
          @click="showEngineMenu = !showEngineMenu"
          title="Select CFD Physics Engine (Rust SIMD, PINN AI, or Python SciPy)"
        >
          <span class="engine-icon">{{ currentEngineInfo.icon }}</span>
          <span class="engine-label">{{ currentEngineInfo.name }}</span>
          <span class="engine-badge" :class="currentEngineInfo.id">{{ currentEngineInfo.badge }}</span>
          <span class="dropdown-arrow">▾</span>
        </button>

        <transition name="fade-drop">
          <div v-if="showEngineMenu" class="engine-menu">
            <div class="menu-heading">CFD Physics Engines</div>
            <button
              v-for="eng in engines"
              :key="eng.id"
              class="engine-menu-item"
              :class="{ selected: (solverMode || 'cfd') === eng.id }"
              @click="selectEngine(eng.id)"
            >
              <span class="menu-item-icon">{{ eng.icon }}</span>
              <div class="menu-item-text">
                <div class="menu-item-title-row">
                  <strong>{{ eng.name }}</strong>
                  <span class="speed-tag" :class="eng.speedClass">{{ eng.speed }}</span>
                </div>
                <small>{{ eng.tech }} · {{ eng.desc }}</small>
              </div>
            </button>
          </div>
        </transition>
      </div>
    </div>

    <!-- Right: AI Copilot Key Status, Colab Runtime Widget, Transport Controls, Export -->
    <div class="header-right">
      <!-- AI Copilot Status & Key Config Button -->
      <button
        class="ai-key-status-btn"
        :class="{ configured: hasAiKey }"
        @click="$emit('openSettings')"
        title="Configure LLM API Key (Gemini, OpenAI, Claude, DeepSeek, Ollama)"
      >
        <span class="ai-sparkle">{{ hasAiKey ? '⚡' : '🔑' }}</span>
        <span class="ai-label">{{ aiModelDisplay }}</span>
        <span class="config-gear">⚙️</span>
      </button>

      <!-- Google Colab Runtime Telemetry Widget -->
      <div class="colab-widget-container" ref="colabWidgetRef">
        <button
          class="colab-btn"
          :class="{ connected: isConnected, connecting: isConnecting }"
          @click="showColabMenu = !showColabMenu"
          title="Google Colab-style Local Hardware Bridge"
        >
          <span class="colab-icon">✓</span>
          <span class="colab-label">RAM</span>
          <span class="colab-gauge">
            <span class="gauge-bar" :style="{ width: ramUsage + '%' }"></span>
          </span>
          <span class="colab-label">Disk</span>
          <span class="colab-gauge">
            <span class="gauge-bar" :style="{ width: diskUsage + '%' }"></span>
          </span>
          <span class="colab-arrow">▾</span>
        </button>

        <!-- Colab Dropdown Menu -->
        <transition name="fade-drop">
          <div v-if="showColabMenu" class="colab-dropdown">
            <div class="dropdown-header">
              <div class="header-status">
                <span class="pulse-dot"></span>
                <strong>Connected to Local Hardware</strong>
              </div>
              <span class="header-host">127.0.0.1:8000</span>
            </div>

            <div class="resource-breakdown">
              <div class="resource-item">
                <div class="res-info">
                  <span>System RAM</span>
                  <strong>{{ (ramUsage * 0.32).toFixed(1) }} GB / 32.0 GB</strong>
                </div>
                <div class="res-meter">
                  <div class="res-fill" :style="{ width: ramUsage + '%' }"></div>
                </div>
              </div>

              <div class="resource-item">
                <div class="res-info">
                  <span>Local NVMe Disk</span>
                  <strong>{{ (diskUsage * 10).toFixed(0) }} GB / 1024 GB</strong>
                </div>
                <div class="res-meter">
                  <div class="res-fill disk" :style="{ width: diskUsage + '%' }"></div>
                </div>
              </div>

              <div class="resource-item">
                <div class="res-info">
                  <span>Compute Device</span>
                  <span class="device-tag">NVIDIA CUDA GPU (Local)</span>
                </div>
              </div>
            </div>

            <div class="dropdown-actions">
              <button class="menu-action-btn" @click="handleReconnect">
                <span>🔄 Reconnect Local Bridge</span>
              </button>
              <button class="menu-action-btn" @click="showColabMenu = false">
                <span>⚙️ Change Runtime Type</span>
              </button>
            </div>
          </div>
        </transition>
      </div>

      <!-- Playback & Transport Controls -->
      <div class="transport-controls">
        <button class="transport-btn" @click="$emit('stepBack')" title="Step Back / Slow (⏪)">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <path d="M11 5L3 12L11 19V5ZM20 5L12 12L20 19V5Z" />
          </svg>
        </button>

        <button
          class="transport-btn play-pause-btn"
          :class="{ active: isPlaying }"
          @click="$emit('togglePlay')"
          :title="isPlaying ? 'Pause Simulation (⏸)' : 'Run Simulation (▶)'"
        >
          <svg v-if="!isPlaying" width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <path d="M8 5V19L19 12L8 5Z" />
          </svg>
          <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <path d="M6 19H10V5H6V19ZM14 5V19H18V5H14Z" />
          </svg>
        </button>

        <button class="transport-btn" @click="$emit('stop')" title="Stop Simulation (⏹)">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
            <path d="M6 6H18V18H6V6Z" />
          </svg>
        </button>

        <button class="transport-btn" @click="$emit('fastForward')" title="Fast Forward (⏩)">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <path d="M4 19L12 12L4 5V19ZM13 19L21 12L13 5V19Z" />
          </svg>
        </button>

        <button class="transport-btn" @click="$emit('reset')" title="Reset Simulation (🔄)">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
            <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4C7.58 4 4.01 7.58 4.01 12C4.01 16.42 7.58 20 12 20C15.73 20 18.84 17.45 19.73 14H17.65C16.83 16.33 14.61 18 12 18C8.69 18 6 15.31 6 12C6 8.69 8.69 6 12 6C13.66 6 15.14 6.69 16.22 7.78L13 11H20V4L17.65 6.35Z" />
          </svg>
        </button>

        <button class="transport-btn" @click="$emit('snapshot')" title="Capture Snapshot / Download (📥)">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19 9H15V3H9V9H5L12 16L19 9ZM5 18V20H19V18H5Z" />
          </svg>
        </button>
      </div>

      <!-- Export OpenFOAM Case Dropdown -->
      <div class="export-dropdown-container" ref="exportDropdownRef">
        <button
          class="export-btn"
          @click="showExportMenu = !showExportMenu"
          title="Export OpenFOAM Case files and ParaView meshes"
        >
          <span>Export Case (.ZIP / .VTK)</span>
          <span class="arrow">▾</span>
        </button>

        <transition name="fade-drop">
          <div v-if="showExportMenu" class="export-menu">
            <button class="export-menu-item" @click="handleExport('zip')">
              <span class="icon">📦</span>
              <div class="item-text">
                <strong>Full OpenFOAM Case (.ZIP)</strong>
                <small>Includes system/, constant/, 0/ and Allrun</small>
              </div>
            </button>

            <button class="export-menu-item" @click="handleExport('vtk')">
              <span class="icon">📊</span>
              <div class="item-text">
                <strong>ParaView Grid (.VTK)</strong>
                <small>Structured points with U, p, T scalars</small>
              </div>
            </button>

            <button class="export-menu-item" @click="handleExport('png')">
              <span class="icon">📸</span>
              <div class="item-text">
                <strong>High-Res Viewport (.PNG)</strong>
                <small>4K render of 3D flow field</small>
              </div>
            </button>
          </div>
        </transition>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import type { SimulationArchetype, AiProviderConfig, SolverMode } from '../types/cfd';

const props = defineProps<{
  currentArchetype: SimulationArchetype;
  solverMode?: SolverMode;
  aiConfig: AiProviderConfig;
  isPlaying: boolean;
  isConnected: boolean;
  isConnecting?: boolean;
  isSidebarOpen?: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:archetype', arch: SimulationArchetype): void;
  (e: 'update:solverMode', mode: SolverMode): void;
  (e: 'openSettings'): void;
  (e: 'togglePlay'): void;
  (e: 'stepBack'): void;
  (e: 'stop'): void;
  (e: 'fastForward'): void;
  (e: 'reset'): void;
  (e: 'snapshot'): void;
  (e: 'exportCase', type: 'zip' | 'vtk' | 'png'): void;
  (e: 'toggleSidebar'): void;
}>();

const showArchetypeMenu = ref(false);
const showEngineMenu = ref(false);
const showColabMenu = ref(false);
const showExportMenu = ref(false);

const archetypeDropdownRef = ref<HTMLDivElement | null>(null);
const engineDropdownRef = ref<HTMLDivElement | null>(null);
const colabWidgetRef = ref<HTMLDivElement | null>(null);
const exportDropdownRef = ref<HTMLDivElement | null>(null);

const engines: { id: SolverMode; name: string; icon: string; badge: string; tech: string; desc: string; speed: string; speedClass: string }[] = [
  { id: 'rust', name: 'Rust Bare-Metal', icon: '🦀', badge: 'SIMD', tech: 'Axum + Rayon', desc: 'Multi-threaded Navier-Stokes & Poisson solver', speed: 'Fastest ⚡', speedClass: 'fastest' },
  { id: 'ai', name: 'PINN AI Surrogate', icon: '⚡', badge: '<50ms', tech: 'Neural Network', desc: 'Instant physics-informed neural operator flow prediction', speed: 'Instant 🚀', speedClass: 'instant' },
  { id: 'cfd', name: 'Python SciPy', icon: '🔬', badge: 'Sparse', tech: 'SciPy + NumPy', desc: 'High-precision sparse fractional-step CPU solver', speed: 'High-Res 🎯', speedClass: 'precise' }
];

const currentEngineInfo = computed(() => {
  const current = props.solverMode || 'cfd';
  return engines.find(e => e.id === current) || engines[2];
});

function selectEngine(id: SolverMode) {
  showEngineMenu.value = false;
  emit('update:solverMode', id);
}

const ramUsage = ref(38);
const diskUsage = ref(24);

const archetypes: { id: SimulationArchetype; name: string; icon: string; solver: string; desc: string }[] = [
  { id: 'plume', name: 'Buoyant Thermal Plume', icon: '💨', solver: 'buoyantBoussinesqSimpleFoam', desc: 'Coupled thermal buoyancy jet' },
  { id: 'airfoil', name: 'NACA 0012 Airfoil Flow', icon: '✈️', solver: 'simpleFoam', desc: 'Wing aerodynamics, Lift & Drag' },
  { id: 'cylinder', name: 'Bluff Body & Vortex Street', icon: '🔴', solver: 'pimpleFoam', desc: 'Von Kármán transient wake' },
  { id: 'venturi', name: 'Venturi Nozzle Flow', icon: '🚿', solver: 'rhoSimpleFoam', desc: 'Compressible throat acceleration' },
  { id: 'cavity', name: '3D Lid-Driven Cavity', icon: '🌀', solver: 'icoFoam', desc: 'Shear-driven vortex recirculation' },
  { id: 'cad', name: 'Custom CAD Upload (.STL)', icon: '📤', solver: 'snappyHexMesh + simpleFoam', desc: 'Arbitrary 3D geometry' }
];

const currentArchetypeInfo = computed(() => {
  return archetypes.find(a => a.id === props.currentArchetype) || archetypes[0];
});

const hasAiKey = computed(() => {
  return !!props.aiConfig.apiKey || props.aiConfig.provider === 'ollama';
});

const aiModelDisplay = computed(() => {
  if (props.aiConfig.provider === 'ollama') return '🦙 Ollama (Local)';
  if (!props.aiConfig.apiKey) return 'Set AI Key';
  if (props.aiConfig.provider === 'gemini') return 'Gemini 2.5 Flash';
  if (props.aiConfig.provider === 'openai') return 'GPT-4o';
  if (props.aiConfig.provider === 'claude') return 'Claude 3.5';
  if (props.aiConfig.provider === 'deepseek') return 'DeepSeek-V3';
  if (props.aiConfig.provider === 'groq') return 'Groq Llama 3';
  return 'AI Configured';
});

function selectArchetype(id: SimulationArchetype) {
  showArchetypeMenu.value = false;
  emit('update:archetype', id);
}

function handleReconnect() {
  showColabMenu.value = false;
}

function handleExport(type: 'zip' | 'vtk' | 'png') {
  showExportMenu.value = false;
  emit('exportCase', type);
}

function handleClickOutside(e: MouseEvent) {
  const target = e.target as Node;
  if (archetypeDropdownRef.value && !archetypeDropdownRef.value.contains(target)) {
    showArchetypeMenu.value = false;
  }
  if (engineDropdownRef.value && !engineDropdownRef.value.contains(target)) {
    showEngineMenu.value = false;
  }
  if (colabWidgetRef.value && !colabWidgetRef.value.contains(target)) {
    showColabMenu.value = false;
  }
  if (exportDropdownRef.value && !exportDropdownRef.value.contains(target)) {
    showExportMenu.value = false;
  }
}

onMounted(() => {
  window.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
  window.removeEventListener('click', handleClickOutside);
});
</script>

<style scoped>
.header-navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 56px;
  padding: 0 18px;
  background-color: var(--bg-surface);
  border-bottom: 1px solid var(--border-subtle);
  position: relative;
  z-index: 100;
  user-select: none;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.sidebar-toggle-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.09);
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.sidebar-toggle-btn:hover {
  background: rgba(56, 189, 248, 0.15);
  border-color: rgba(56, 189, 248, 0.4);
  color: #38bdf8;
  transform: scale(1.04);
}

.sidebar-toggle-btn.active {
  color: #38bdf8;
  background: rgba(56, 189, 248, 0.08);
  border-color: rgba(56, 189, 248, 0.25);
}

.sidebar-icon {
  width: 18px;
  height: 18px;
  transition: transform 0.2s ease;
}

.logo-cube {
  width: 32px;
  height: 32px;
  perspective: 600px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cube-inner {
  width: 26px;
  height: 26px;
  position: relative;
  transform-style: preserve-3d;
  transform: rotateX(-24deg) rotateY(32deg);
  background: var(--brand-gradient);
  border-radius: 6px;
  box-shadow: 0 0 16px rgba(168, 85, 247, 0.4), inset 0 0 8px rgba(255, 255, 255, 0.3);
  transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

.logo-cube:hover .cube-inner {
  transform: rotateX(-10deg) rotateY(55deg) scale(1.08);
}

.brand-title {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.2px;
  color: #ffffff;
  margin: 0;
}

/* Archetype Dropdown Switcher */
.archetype-dropdown-wrapper {
  position: relative;
  margin-left: 8px;
}

.archetype-pill-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--btn-surface);
  border: 1px solid var(--accent-border);
  color: #f1f5f9;
  padding: 5px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.archetype-pill-btn:hover {
  background: var(--bg-card);
  border-color: #ffffff;
}

.archetype-icon {
  font-size: 13px;
}

.dropdown-arrow {
  font-size: 10px;
  color: var(--accent-border);
}

.archetype-menu {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  width: 320px;
  background: var(--bg-surface);
  border: 1px solid var(--border-active);
  border-radius: 8px;
  padding: 6px;
  box-shadow: 0 12px 36px rgba(0, 0, 0, 0.75);
  z-index: 250;
}

.menu-heading {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  color: #94a3b8;
  padding: 6px 10px 4px;
}

.archetype-menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 8px 10px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 6px;
  color: #cbd5e1;
  text-align: left;
  cursor: pointer;
  transition: all 0.15s ease;
}

.archetype-menu-item:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #ffffff;
}

.archetype-menu-item.selected {
  background: var(--btn-surface);
  border-color: var(--accent-border);
  color: #ffffff;
}

/* Engine Dropdown Styles */
.engine-dropdown-wrapper {
  position: relative;
  margin-left: 6px;
}

.engine-pill-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--btn-surface);
  border: 1px solid var(--border-subtle);
  border-radius: 20px;
  padding: 4px 10px;
  color: #e2e8f0;
  font-size: 11.5px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.engine-pill-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: var(--accent-border);
}

.engine-pill-btn.rust {
  border-color: rgba(249, 115, 22, 0.5);
  background: rgba(249, 115, 22, 0.12);
  color: #fdba74;
}

.engine-pill-btn.ai {
  border-color: rgba(56, 189, 248, 0.5);
  background: rgba(56, 189, 248, 0.12);
  color: #7dd3fc;
}

.engine-pill-btn.cfd {
  border-color: rgba(52, 211, 153, 0.5);
  background: rgba(52, 211, 153, 0.12);
  color: #6ee7b7;
}

.engine-badge {
  font-size: 9px;
  font-weight: 700;
  padding: 1px 5px;
  border-radius: 4px;
  text-transform: uppercase;
}

.engine-badge.rust {
  background: #ea580c;
  color: #ffffff;
}

.engine-badge.ai {
  background: #0284c7;
  color: #ffffff;
}

.engine-badge.cfd {
  background: #059669;
  color: #ffffff;
}

.engine-menu {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  width: 340px;
  background: var(--bg-surface);
  border: 1px solid var(--border-active);
  border-radius: 8px;
  padding: 6px;
  box-shadow: 0 12px 36px rgba(0, 0, 0, 0.75);
  z-index: 250;
}

.engine-menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 8px 10px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 6px;
  color: #cbd5e1;
  text-align: left;
  cursor: pointer;
  transition: all 0.15s ease;
}

.engine-menu-item:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #ffffff;
}

.engine-menu-item.selected {
  background: var(--btn-surface);
  border-color: var(--accent-border);
  color: #ffffff;
}

.menu-item-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.speed-tag {
  font-size: 9px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 10px;
}

.speed-tag.fastest {
  background: rgba(249, 115, 22, 0.2);
  color: #fb923c;
}

.speed-tag.instant {
  background: rgba(56, 189, 248, 0.2);
  color: #38bdf8;
}

.speed-tag.precise {
  background: rgba(52, 211, 153, 0.2);
  color: #34d399;
}

.menu-item-icon {
  font-size: 18px;
}

.menu-item-text {
  display: flex;
  flex-direction: column;
}

.menu-item-text strong {
  font-size: 12px;
  color: #f1f5f9;
}

.menu-item-text small {
  font-size: 10px;
  color: #94a3b8;
}

/* Right header elements */
.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* AI Key Status Button */
.ai-key-status-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--btn-surface);
  border: 1px solid var(--border-subtle);
  color: #cbd5e1;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 11.5px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.ai-key-status-btn:hover {
  background: var(--bg-card);
  border-color: var(--accent-border);
  color: #ffffff;
}

.ai-key-status-btn.configured {
  background: var(--btn-surface);
  border-color: var(--accent-border);
  color: #f1f5f9;
}

.ai-sparkle {
  font-size: 12px;
}

.config-gear {
  font-size: 10px;
  opacity: 0.7;
}

/* Colab Runtime Widget */
.colab-widget-container {
  position: relative;
}

.colab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--btn-surface);
  color: #f1f5f9;
  border: 1px solid var(--border-subtle);
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 11.5px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.colab-btn:hover {
  background: var(--bg-card);
  border-color: var(--accent-border);
}

.colab-icon {
  font-size: 11px;
  font-weight: 800;
  color: var(--accent-border);
}

.colab-label {
  color: var(--text-secondary);
  font-size: 10.5px;
}

.colab-gauge {
  width: 36px;
  height: 5px;
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid var(--border-subtle);
  border-radius: 3px;
  overflow: hidden;
  display: inline-block;
}

.gauge-bar {
  display: block;
  height: 100%;
  background: var(--accent-border);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.colab-arrow {
  font-size: 10px;
  color: #94a3b8;
}

/* Colab Dropdown */
.colab-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 300px;
  background: #19202c;
  border: 1px solid var(--border-active);
  border-radius: 8px;
  padding: 14px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
  z-index: 200;
}

.dropdown-header {
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  padding-bottom: 10px;
  margin-bottom: 12px;
}

.header-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12.5px;
  color: #ffffff;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 8px #10b981;
}

.header-host {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: #94a3b8;
  margin-left: 16px;
}

.resource-breakdown {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 14px;
}

.resource-item .res-info {
  display: flex;
  justify-content: space-between;
  font-size: 11.5px;
  color: #94a3b8;
  margin-bottom: 4px;
}

.resource-item .res-info strong {
  color: #f1f5f9;
}

.device-tag {
  color: #a855f7;
  font-size: 10.5px;
  font-weight: 600;
}

.res-meter {
  height: 5px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
  overflow: hidden;
}

.res-fill {
  height: 100%;
  background: #10b981;
}

.res-fill.disk {
  background: #38bdf8;
}

.dropdown-actions {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.menu-action-btn {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: #cbd5e1;
  padding: 7px 10px;
  border-radius: 5px;
  font-size: 11.5px;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s ease;
}

.menu-action-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #ffffff;
}

/* Transport Controls */
.transport-controls {
  display: flex;
  align-items: center;
  gap: 3px;
  background: var(--btn-surface);
  border: 1px solid var(--border-subtle);
  padding: 3px;
  border-radius: 7px;
}

.transport-btn {
  width: 30px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  color: #94a3b8;
  border: 1px solid transparent;
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.transport-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #ffffff;
  border-color: rgba(255, 255, 255, 0.1);
}

.transport-btn.play-pause-btn {
  color: #38bdf8;
}

.transport-btn.play-pause-btn.active {
  background: rgba(56, 189, 248, 0.15);
  border-color: rgba(56, 189, 248, 0.35);
  color: #38bdf8;
}

/* Export Dropdown */
.export-dropdown-container {
  position: relative;
}

.export-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--btn-surface);
  color: #e2e8f0;
  border: 1px solid var(--border-subtle);
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 11.5px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.export-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: var(--border-active);
}

.export-btn .arrow {
  font-size: 10px;
  color: #94a3b8;
}

.export-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 260px;
  background: #19202c;
  border: 1px solid var(--border-active);
  border-radius: 8px;
  padding: 6px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
  z-index: 200;
}

.export-menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 8px 10px;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: #cbd5e1;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s ease;
}

.export-menu-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #ffffff;
}

.export-menu-item .icon {
  font-size: 16px;
}

.export-menu-item .item-text {
  display: flex;
  flex-direction: column;
}

.export-menu-item .item-text strong {
  font-size: 11.5px;
  color: #f1f5f9;
}

.export-menu-item .item-text small {
  font-size: 10px;
  color: #94a3b8;
}

/* Animations */
.fade-drop-enter-active,
.fade-drop-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.fade-drop-enter-from,
.fade-drop-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
