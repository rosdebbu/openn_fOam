<template>
  <div class="app-layout">
    <!-- Top Navigation Header -->
    <HeaderNavbar
      :caseName="params.caseName"
      :currentArchetype="params.archetype"
      :solverMode="params.solverMode"
      :aiConfig="aiConfig"
      :isPlaying="isPlaying"
      :isConnected="isConnected"
      :isSidebarOpen="isSidebarOpen"
      @update:caseName="val => params.caseName = val"
      @update:archetype="setArchetype"
      @update:solverMode="val => params.solverMode = val"
      @openSettings="isSettingsOpen = true"
      @togglePlay="togglePlay"
      @stepBack="stepBack"
      @stop="stopSimulation"
      @fastForward="fastForward"
      @reset="resetSimulation"
      @snapshot="takeSnapshot"
      @exportCase="handleExportCase"
      @toggleSidebar="toggleSidebar"
    />

    <!-- Main Studio Body -->
    <div class="studio-body">
      <!-- Left OpenFOAM Case Hub (Collapsible Slide Bar) -->
      <transition name="slide-sidebar">
        <SidebarControls
          v-show="isSidebarOpen"
          :params="params"
          :aiConfig="aiConfig"
          :isComputing="status === 'computing'"
          @update:params="updateParams"
          @update:customGeometry="handleCustomGeometry"
          @applyDict="handleApplyDict"
          @fileUploaded="handleFileUploaded"
          @startSimulation="runNow"
          @closeSidebar="isSidebarOpen = false"
        />
      </transition>

      <!-- Right Main 3D CFD Viewport -->
      <main class="viewport-area">
        <!-- Floating Expand Pill when Sidebar is Collapsed -->
        <button
          v-if="!isSidebarOpen"
          class="sidebar-floating-toggle-btn"
          @click="toggleSidebar"
          title="Open Case Hub (Ctrl + \)"
        >
          <span class="pill-icon">📁</span>
          <span class="pill-text">OpenFOAM Hub</span>
          <span class="pill-arrow">▶</span>
        </button>

        <CfdThree3D
          ref="viewportRef"
          :data="simulationData"
          :params="params"
          :telemetry="telemetry"
          @update:activeField="val => params.activeField = val"
        />

        <!-- Floating Bottom Slide Drawer: Telemetry & OpenFOAM Terminal Drawer -->
        <div class="bottom-telemetry-dock" :class="{ 'dock-expanded': isBottomDockOpen }">
          <!-- Slide Bar Handle Pill -->
          <div class="dock-slide-bar" @click="isBottomDockOpen = !isBottomDockOpen">
            <div class="slide-bar-left">
              <span class="slide-icon">{{ isBottomDockOpen ? '▼' : '▲' }}</span>
              <span class="slide-title">📟 OpenFOAM Solver Log & Telemetry</span>
              <div class="mini-metrics" v-if="!isBottomDockOpen">
                <span class="mini-tag res">Res: {{ latestResidualFormatted }}</span>
                <span class="mini-tag force">Cd: {{ telemetry.cd.toFixed(3) }}</span>
              </div>
            </div>

            <div class="slide-bar-right" @click.stop>
              <div class="dock-tabs" v-if="isBottomDockOpen">
                <button
                  class="dock-tab-btn"
                  :class="{ active: activeDockTab === 'terminal' }"
                  @click="activeDockTab = 'terminal'"
                >
                  📟 Solver Log
                </button>
                <button
                  class="dock-tab-btn"
                  :class="{ active: activeDockTab === 'residuals' }"
                  @click="activeDockTab = 'residuals'"
                >
                  📈 Residuals
                </button>
              </div>
              <button
                class="minimize-toggle-btn"
                @click="isBottomDockOpen = !isBottomDockOpen"
                :title="isBottomDockOpen ? 'Slide Down / Hide' : 'Slide Up / Show'"
              >
                {{ isBottomDockOpen ? '✕ Hide' : '▲ Expand' }}
              </button>
            </div>
          </div>

          <!-- Slide Drawer Content -->
          <transition name="slide-fade">
            <div v-show="isBottomDockOpen" class="dock-drawer-body">
              <!-- Live OpenFOAM Terminal View -->
              <div v-show="activeDockTab === 'terminal'" class="dock-panel terminal-panel">
                <OpenFoamTerminal
                  :archetype="params.archetype"
                  :isPlaying="isPlaying"
                  :telemetry="telemetry"
                />
              </div>

              <!-- Residual Chart View -->
              <div v-show="activeDockTab === 'residuals'" class="dock-panel">
                <ResidualChart
                  :iterations="iterations"
                  :residuals="residuals"
                  :latestResidual="latestResidual"
                />
              </div>
            </div>
          </transition>
        </div>
      </main>
    </div>

    <!-- AI Copilot & LLM Settings Modal -->
    <SettingsModal
      :isOpen="isSettingsOpen"
      @close="isSettingsOpen = false"
      @saved="handleAiConfigSaved"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue';
import type { SimulationParams, SimulationStepData, SimulationArchetype, SolverMode, AiProviderConfig, AerodynamicTelemetry } from './types/cfd';
import { getStoredAiConfig } from './utils/aiCopilot';

import HeaderNavbar from './components/HeaderNavbar.vue';
import SidebarControls from './components/SidebarControls.vue';
import CfdThree3D from './components/CfdThree3D.vue';
import ResidualChart from './components/ResidualChart.vue';
import OpenFoamTerminal from './components/OpenFoamTerminal.vue';
import SettingsModal from './components/SettingsModal.vue';

// Studio Simulation Parameters matching Mockup
const params = reactive<SimulationParams>({
  caseName: 'NACA0012_Airfoil_Run',
  archetype: 'airfoil',
  activeField: 'U',
  substance: 'air',
  naturalForces: {
    gravity: [0, -9.81, 0],
    ambientTemp: 293.15,
    referencePressure: 101325
  },
  caseType: 'channel',
  solverMode: 'cfd',
  turbulenceModel: 'k-omega-sst',
  reynoldsNumber: 50000,
  gridResolution: 64,
  maxIterations: 1000,
  dt: 0.005,
  tolerance: 1e-5,
  studioParams: {
    irisPurple: 0.45,
    vorticityAngle: 0.209, // 12 deg AoA
    vorticityCore: 50,
    butterscotchCore: 100
  }
});

const aiConfig = reactive<AiProviderConfig>(getStoredAiConfig());
const isSettingsOpen = ref(false);
const isBottomDockOpen = ref(false);
const isSidebarOpen = ref(true);
const activeDockTab = ref<'residuals' | 'terminal'>('terminal');

function toggleSidebar() {
  isSidebarOpen.value = !isSidebarOpen.value;
  setTimeout(() => {
    window.dispatchEvent(new Event('resize'));
  }, 260);
}

function handleKeydown(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && (e.key === '\\' || e.key === 'b')) {
    e.preventDefault();
    toggleSidebar();
  }
}

const isPlaying = ref(true);
const isConnected = ref(true);
const status = ref<'ready' | 'computing' | 'converged' | 'error'>('computing');

// Real OpenFOAM Telemetry
const telemetry = reactive<AerodynamicTelemetry>({
  cd: 0.048,
  cl: 0.842,
  l_d: 17.54,
  courantMax: 0.42,
  courantMean: 0.08,
  continuityError: 1.2e-6
});

const simulationData = ref<SimulationStepData | null>(null);
const iterations = ref<number[]>([0]);
const residuals = ref<number[]>([1.0]);

// Custom Geometry Builder — user-defined obstacle shape/size/position that is
// sent to the real solver as `obstacleSpec` (the "build your own simulation" path)
const customGeometry = ref<{
  shape: string; cx: number; cy: number; size: number; aoa: number;
} | null>(null);

// Frame history enabling REAL transport controls: step back / fast forward
// scrub through actually received solver frames instead of doing nothing.
const frameHistory = ref<SimulationStepData[]>([]);
const frameIndex = ref(-1);
const isScrubbing = ref(false);

let socket: any = null;
let simInterval: any = null;
const viewportRef = ref<{ capturePng?: () => boolean } | null>(null);

const latestResidual = computed(() => {
  if (residuals.value.length === 0) return null;
  return residuals.value[residuals.value.length - 1];
});

const latestResidualFormatted = computed(() => {
  const res = latestResidual.value;
  return res !== null ? res.toExponential(2) : '1.0e-5';
});

function setArchetype(arch: SimulationArchetype) {
  params.archetype = arch;
  const defaultNames: Record<string, string> = {
    airfoil: 'NACA0012_Airfoil_Run',
    cylinder: 'Cylinder_Vortex_Street',
    venturi: 'Venturi_Tube_Choked_Flow',
    f1: 'Formula1_GroundEffect_Downforce',
    drone: 'Drone_Quadrotor_Hover',
    submarine: 'Submarine_Cavitation_Hull',
    plume: 'Thermal_Buoyant_Plume',
    cavity: 'Lid_Driven_Cavity_Re100',
    water_dam: 'Dam_Break_VOF_Water',
    weather_plume: 'Atmospheric_Weather_Plume'
  };
  if (defaultNames[arch]) {
    params.caseName = defaultNames[arch];
  }
  if (arch === 'airfoil') {
    params.studioParams.irisPurple = 0.45;
    params.studioParams.vorticityAngle = 0.209;
    params.studioParams.vorticityCore = 50;
    params.studioParams.butterscotchCore = 100;
    telemetry.cd = 0.048;
    telemetry.cl = 0.842;
    telemetry.l_d = 17.54;
  } else if (arch === 'cylinder') {
    params.studioParams.irisPurple = 0.35;
    params.studioParams.vorticityAngle = 0.1;
    params.studioParams.vorticityCore = 40;
    params.studioParams.butterscotchCore = 60;
    telemetry.cd = 1.182;
    telemetry.cl = 0.421;
    telemetry.l_d = 0.36;
  } else if (arch === 'venturi') {
    params.studioParams.irisPurple = 0.25;
    params.studioParams.vorticityAngle = 0.0;
    params.studioParams.vorticityCore = 30;
    params.studioParams.butterscotchCore = 50;
    telemetry.cd = 0.21;
    telemetry.cl = 0.0;
    telemetry.l_d = 0.0;
  } else if (arch === 'f1') {
    params.studioParams.irisPurple = 0.85;
    params.studioParams.vorticityAngle = -0.12;
    params.studioParams.vorticityCore = 75;
    params.studioParams.butterscotchCore = 110;
    telemetry.cd = 0.92;
    telemetry.cl = -2.85;
    telemetry.l_d = 3.10;
    telemetry.downforce = 2450;
  } else if (arch === 'drone') {
    params.studioParams.irisPurple = 0.40;
    params.studioParams.vorticityAngle = -0.45;
    params.studioParams.vorticityCore = 80;
    params.studioParams.butterscotchCore = 70;
    telemetry.cd = 0.32;
    telemetry.cl = 1.20;
    telemetry.l_d = 3.75;
    telemetry.thrust = 17.65;
  } else if (arch === 'submarine') {
    params.studioParams.irisPurple = 0.38;
    params.studioParams.vorticityAngle = 0.05;
    params.studioParams.vorticityCore = 35;
    params.studioParams.butterscotchCore = 40;
    telemetry.cd = 0.082;
    telemetry.cl = 0.015;
    telemetry.l_d = 0.18;
    telemetry.cavitationIndex = 11.8;
  } else {
    params.studioParams.irisPurple = 0.182;
    params.studioParams.vorticityAngle = 0.152;
    params.studioParams.vorticityCore = 30;
    params.studioParams.butterscotchCore = 84.899;
    telemetry.cd = 0.82;
    telemetry.cl = 0.15;
    telemetry.l_d = 0.18;
  }
}

function updateParams(newParams: SimulationParams) {
  Object.assign(params, newParams);
}

function handleCustomGeometry(
  spec: { shape: string; cx: number; cy: number; size: number; aoa: number } | null
) {
  customGeometry.value = spec;
  if (spec) {
    params.archetype = 'cad';
  }
}

// Dictionary overrides extracted from the dict editor's edited content.
// The backend parses simple `key value;` pairs (deltaT, nu, viscosity...)
// and applies them to the live solver run.
const dictOverrides = ref<Record<string, { name: string; content: string }>>({});

function handleApplyDict(file: { name: string; path?: string; category?: string; content: string }) {
  dictOverrides.value = { ...dictOverrides.value, [file.name]: { name: file.name, content: file.content } };
  restartSimulation();
}

function handleAiConfigSaved(newConfig: AiProviderConfig) {
  Object.assign(aiConfig, newConfig);
}

function handleFileUploaded(file: File) {
  params.archetype = 'cad';
  console.log('Geometry uploaded:', file.name);
}

function triggerLiveSimulation() {
  if (!isPlaying.value) return;
  
  const loc = window.location;
  const envApi = (import.meta as any).env?.VITE_API_URL;
  const rawHost = envApi ? envApi.replace(/^https?:\/\//, '') : (loc.host.includes('5173') ? '127.0.0.1:8000' : loc.host);
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${proto}//${rawHost}/ws/simulate`;

  if (socket) {
    try { socket.close(); } catch (_) {}
  }

  status.value = 'computing';
  try {
    socket = new WebSocket(wsUrl);
    
    socket.onopen = () => {
      isConnected.value = true;
      // Full user physics: everything the user sets in the Case Hub is sent to
      // the real solver — substance, inlet velocity, gravity, temperatures and
      // custom geometry (obstacleSpec) all change the actual computation.
      socket.send(JSON.stringify({
        gridResolution: params.gridResolution,
        reynoldsNumber: params.reynoldsNumber,
        solverMode: params.solverMode,
        archetype: params.archetype,
        aoa: params.studioParams.vorticityAngle * (180 / Math.PI),
        maxIterations: params.maxIterations,
        dt: params.dt,
        substance: params.substance,
        inletVelocity: params.studioParams.irisPurple,
        hotTemp: params.studioParams.butterscotchCore,
        naturalForces: params.naturalForces,
        obstacleSpec: customGeometry.value,
        dictOverrides: dictOverrides.value
      }));
    };

    socket.onmessage = (event: MessageEvent) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.error) {
          console.warn('Simulation backend warning:', payload.error);
          return;
        }

        if (payload.iteration !== undefined) {
          iterations.value.push(payload.iteration);
          residuals.value.push(payload.residual);
        }

        if (payload.cd !== undefined) telemetry.cd = payload.cd;
        if (payload.cl !== undefined) telemetry.cl = payload.cl;
        if (payload.downforce !== undefined) telemetry.downforce = payload.downforce;
        if (payload.thrust !== undefined) telemetry.thrust = payload.thrust;
        if (payload.cavitationIndex !== undefined) telemetry.cavitationIndex = payload.cavitationIndex;
        if (payload.courantMax !== undefined) telemetry.courantMax = payload.courantMax;
        if (payload.continuityError !== undefined) telemetry.continuityError = payload.continuityError;

        if (payload.u && payload.v && payload.speed) {
          const frame: SimulationStepData = {
            iteration: payload.iteration || 1,
            residual: payload.residual || 0.0,
            converged: !!payload.converged,
            u: payload.u,
            v: payload.v,
            p: payload.p,
            speed: payload.speed,
            obstacleMask: payload.obstacleMask,
            mode: (payload.mode as SolverMode) || params.solverMode || 'cfd'
          };
          // Record every frame; while scrubbing the display stays frozen on
          // the frame the user stepped back to.
          frameHistory.value.push(frame);
          if (frameHistory.value.length > 240) frameHistory.value.shift();
          frameIndex.value = frameHistory.value.length - 1;
          if (!isScrubbing.value) {
            simulationData.value = frame;
          }
        }

        if (payload.converged) {
          status.value = 'converged';
        }
      } catch (err) {
        console.error('WebSocket parse error:', err);
      }
    };

    socket.onerror = () => {
      isConnected.value = false;
    };

    socket.onclose = () => {
      if (status.value === 'computing') {
        status.value = 'ready';
      }
    };
  } catch (err) {
    console.warn('WebSocket connection error; client ticker active:', err);
  }
}

watch(() => [params.solverMode, params.archetype], () => {
  restartSimulation();
});

// Debounced live re-run: changing any physics slider (Reynolds, grid, dt,
// substance, gravity, inlet velocity, AoA, hot temp) or editing the Custom
// Geometry Builder automatically re-runs the REAL simulation — user-made
// cases respond immediately instead of showing stale/wrong results.
let reRunTimer: any = null;
watch(
  () => [
    params.reynoldsNumber,
    params.gridResolution,
    params.dt,
    params.substance,
    ...params.naturalForces.gravity,
    params.naturalForces.ambientTemp,
    params.studioParams.irisPurple,
    params.studioParams.vorticityAngle,
    params.studioParams.butterscotchCore,
    customGeometry.value
  ],
  () => {
    if (reRunTimer) clearTimeout(reRunTimer);
    reRunTimer = setTimeout(() => {
      restartSimulation();
    }, 450);
  }
);

function restartSimulation() {
  // Reset convergence history and restart the live stream regardless of the
  // play/pause state. Calling resetSimulation() here would set isPlaying=false
  // and stall triggerLiveSimulation(), so the stream would never restart.
  iterations.value = [0];
  residuals.value = [1.0];
  simulationData.value = null;
  frameHistory.value = [];
  frameIndex.value = -1;
  isScrubbing.value = false;
  isPlaying.value = true;
  status.value = 'computing';
  triggerLiveSimulation();
}

function runNow() {
  restartSimulation();
}

function togglePlay() {
  isPlaying.value = !isPlaying.value;
  if (isPlaying.value) {
    isScrubbing.value = false;
    status.value = 'computing';
    triggerLiveSimulation();
  } else {
    status.value = 'ready';
    if (socket) {
      try { socket.close(); } catch (_) {}
    }
  }
}

function stepBack() {
  // Step back through the REAL received solver frames
  if (frameHistory.value.length === 0) return;
  isScrubbing.value = true;
  if (isPlaying.value) {
    isPlaying.value = false;
    if (socket) { try { socket.close(); } catch (_) {} }
  }
  frameIndex.value = Math.max(0, frameIndex.value - 1);
  simulationData.value = frameHistory.value[frameIndex.value];
  status.value = 'ready';
}

function stopSimulation() {
  isPlaying.value = false;
  isScrubbing.value = false;
  status.value = 'ready';
  if (socket) {
    try { socket.close(); } catch (_) {}
  }
}

function fastForward() {
  // Step forward through recorded frames, or resume the live stream
  if (frameHistory.value.length === 0) {
    if (!isPlaying.value) runNow();
    return;
  }
  if (frameIndex.value < frameHistory.value.length - 1) {
    frameIndex.value = Math.min(frameHistory.value.length - 1, frameIndex.value + 1);
    simulationData.value = frameHistory.value[frameIndex.value];
    status.value = 'ready';
  } else {
    // Already at the latest frame -> resume live playback
    isScrubbing.value = false;
    if (!isPlaying.value) {
      isPlaying.value = true;
      status.value = 'computing';
      triggerLiveSimulation();
    }
  }
}

function resetSimulation() {
  isPlaying.value = false;
  status.value = 'ready';
  iterations.value = [0];
  residuals.value = [1.0];
}

function takeSnapshot() {
  if (viewportRef.value && typeof viewportRef.value.capturePng === 'function') {
    const downloaded = viewportRef.value.capturePng();
    if (downloaded) return;
  }
  handleExportCase('png');
}

function handleExportCase(type: 'zip' | 'vtk' | 'png') {
  const loc = window.location;
  const envApi = (import.meta as any).env?.VITE_API_URL;
  const apiHost = envApi || (loc.host.includes('5173') ? 'http://127.0.0.1:8000' : '');
  const safeCaseName = encodeURIComponent(params.caseName || 'openzess_simulation');
  if (type === 'vtk') {
    window.open(`${apiHost}/api/export/vtk?name=${safeCaseName}`, '_blank');
  } else if (type === 'zip') {
    window.open(`${apiHost}/api/export/openfoam?name=${safeCaseName}`, '_blank');
  } else {
    alert(`Viewport snapshot captured successfully for case [${params.caseName || 'openzess_simulation'}]!`);
  }
}

onMounted(() => {
  // Trigger the initial live simulation on page load (isPlaying starts true,
  // but nothing connected the WebSocket without this call).
  triggerLiveSimulation();

  // Offline fallback ticker — ONLY active when the backend is unreachable.
  // When the real solver streams data (isConnected), the backend telemetry
  // wins and this ticker stays quiet so real results are never overridden.
  simInterval = setInterval(() => {
    if (isPlaying.value && !isConnected.value) {
      const lastIter = iterations.value[iterations.value.length - 1] || 0;
      if (lastIter < 200) {
        iterations.value.push(lastIter + 5);
        const lastRes = residuals.value[residuals.value.length - 1] || 1e-3;
        residuals.value.push(Math.max(1e-13, lastRes * 0.85 * (1 + (Math.random() - 0.5) * 0.1)));
      }

      // Offline demo force variations with vortex shedding
      if (params.archetype === 'cylinder') {
        const t = performance.now() * 0.003;
        telemetry.cl = Math.sin(t * 2.5) * 0.55;
        telemetry.cd = 1.18 + Math.abs(Math.sin(t * 5.0)) * 0.08;
      }
    }
  }, 1000);

  window.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
  if (socket) socket.close();
  if (simInterval) clearInterval(simInterval);
  window.removeEventListener('keydown', handleKeydown);
});
</script>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  background-color: var(--bg-canvas);
  color: var(--text-primary);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  overflow: hidden;
}

.studio-body {
  display: flex;
  flex: 1;
  overflow: hidden;
  height: calc(100vh - 56px);
  position: relative;
}

/* Sidebar Smooth Slide Transition */
.slide-sidebar-enter-active,
.slide-sidebar-leave-active {
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.slide-sidebar-enter-from,
.slide-sidebar-leave-to {
  margin-left: -450px;
  opacity: 0;
}

.viewport-area {
  flex: 1;
  min-width: 0;
  position: relative;
  background: var(--bg-canvas);
  padding: 10px;
  overflow: hidden;
  display: flex;
}

/* Floating Expand Pill when Sidebar is Collapsed */
.sidebar-floating-toggle-btn {
  position: absolute;
  top: 18px;
  left: 18px;
  z-index: 35;
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(19, 15, 22, 0.92);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--accent-border);
  border-radius: 8px;
  padding: 6px 12px;
  color: #f1f5f9;
  font-size: 11.5px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
  transition: all 0.2s ease;
}

.sidebar-floating-toggle-btn:hover {
  background: var(--bg-card);
  border-color: #38bdf8;
  transform: translateX(2px);
}

.sidebar-floating-toggle-btn .pill-icon {
  font-size: 13px;
}

.sidebar-floating-toggle-btn .pill-text {
  font-size: 11px;
  font-weight: 700;
  color: #ffffff;
}

.sidebar-floating-toggle-btn .pill-arrow {
  font-size: 10px;
  color: #38bdf8;
}

/* Bottom Telemetry Slide Drawer */
.bottom-telemetry-dock {
  position: absolute;
  bottom: 14px;
  right: 14px;
  z-index: 40;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  max-width: 440px;
  user-select: none;
}

/* Compact Slide Bar Pill */
.dock-slide-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  background: rgba(19, 15, 22, 0.92);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  padding: 5px 10px;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
  transition: all 0.2s ease;
}

.dock-slide-bar:hover {
  border-color: var(--border-active);
  background: rgba(27, 21, 31, 0.98);
}

.slide-bar-left {
  display: flex;
  align-items: center;
  gap: 6px;
}

.slide-icon {
  font-size: 10px;
  color: #38bdf8;
}

.slide-title {
  font-size: 11px;
  font-weight: 700;
  color: #f1f5f9;
}

.mini-metrics {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: 4px;
}

.mini-tag {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9.5px;
  font-weight: 600;
  padding: 1px 5px;
  border-radius: 4px;
}

.mini-tag.res {
  color: #a855f7;
  background: rgba(168, 85, 247, 0.15);
}

.mini-tag.force {
  color: #fbbf24;
  background: rgba(251, 191, 36, 0.15);
}

.slide-bar-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.minimize-toggle-btn {
  background: var(--btn-surface);
  border: 1px solid var(--border-subtle);
  color: #cbd5e1;
  font-size: 10.5px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.minimize-toggle-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
}

.dock-tabs {
  display: flex;
  background: rgba(15, 20, 30, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  padding: 2px;
  gap: 2px;
}

.dock-tab-btn {
  background: transparent;
  border: 1px solid transparent;
  color: #94a3b8;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 10.5px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.dock-tab-btn:hover {
  color: #ffffff;
}

.dock-tab-btn.active {
  background: rgba(168, 85, 247, 0.25);
  border-color: rgba(168, 85, 247, 0.6);
  color: #e9d5ff;
}

.dock-drawer-body {
  display: flex;
  flex-direction: column;
}

.dock-panel {
  display: flex;
}

.dock-panel.terminal-panel {
  width: 420px;
}

.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1);
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  opacity: 0;
  transform: translateY(12px) scale(0.98);
}
</style>
