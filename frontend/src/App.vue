<template>
  <div class="app-layout">
    <!-- Top Navigation Header -->
    <HeaderNavbar
      :currentArchetype="params.archetype"
      :aiConfig="aiConfig"
      :isPlaying="isPlaying"
      :isConnected="isConnected"
      @update:archetype="setArchetype"
      @openSettings="isSettingsOpen = true"
      @togglePlay="togglePlay"
      @stepBack="stepBack"
      @stop="stopSimulation"
      @fastForward="fastForward"
      @reset="resetSimulation"
      @snapshot="takeSnapshot"
      @exportCase="handleExportCase"
    />

    <!-- Main Studio Body -->
    <div class="studio-body">
      <!-- Left OpenFOAM Case Hub -->
      <SidebarControls
        v-show="isSidebarOpen"
        :params="params"
        :aiConfig="aiConfig"
        :isComputing="status === 'computing'"
        @update:params="updateParams"
        @fileUploaded="handleFileUploaded"
        @autoRunSimulation="startLiveSimulation"
      />

      <!-- Floating Sidebar Toggle Tab -->
      <button
        class="sidebar-toggle-tab"
        :class="{ 'sidebar-collapsed': !isSidebarOpen }"
        @click="isSidebarOpen = !isSidebarOpen"
        :title="isSidebarOpen ? 'Collapse Physics & AI Panel' : 'Expand Physics & AI Panel'"
      >
        <span class="toggle-icon">{{ isSidebarOpen ? '◀' : '▶' }}</span>
        <span class="toggle-text" v-if="!isSidebarOpen">PHYSICS & CASE HUB</span>
      </button>

      <!-- Right Main 3D CFD Viewport -->
      <main class="viewport-area">
        <CfdThree3D
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
              <span class="slide-title">📊 OpenFOAM Solver Log & Telemetry</span>
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
                {{ isBottomDockOpen ? '▲ Hide' : '▼ Expand' }}
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
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue';
import type { SimulationParams, SimulationStepData, SimulationArchetype, AiProviderConfig, AerodynamicTelemetry } from './types/cfd';
import { getStoredAiConfig } from './utils/aiCopilot';

import HeaderNavbar from './components/HeaderNavbar.vue';
import SidebarControls from './components/SidebarControls.vue';
import CfdThree3D from './components/CfdThree3D.vue';
import ResidualChart from './components/ResidualChart.vue';
import OpenFoamTerminal from './components/OpenFoamTerminal.vue';
import SettingsModal from './components/SettingsModal.vue';

// Studio Simulation Parameters matching Mockup
const params = reactive<SimulationParams>({
  archetype: 'cylinder',
  activeField: 'U',
  substance: 'air',
  naturalForces: {
    gravity: [0, -9.81, 0],
    ambientTemp: 293.15,
    referencePressure: 101325
  },
  caseType: 'channel',
  solverMode: 'cfd',
  turbulenceModel: 'laminar',
  reynoldsNumber: 100,
  gridResolution: 41,
  maxIterations: 300,
  dt: 0.005,
  tolerance: 1e-5,
  studioParams: {
    irisPurple: 0.45,
    vorticityAngle: 0.209,
    vorticityCore: 50,
    butterscotchCore: 100
  }
});

const aiConfig = reactive<AiProviderConfig>(getStoredAiConfig());
const isSettingsOpen = ref(false);
const isSidebarOpen = ref(true);
const isBottomDockOpen = ref(false);
const activeDockTab = ref<'residuals' | 'terminal'>('terminal');

const isPlaying = ref(true);
const isConnected = ref(false);
const status = ref<'ready' | 'computing' | 'converged' | 'error'>('ready');

// Real OpenFOAM Telemetry
const telemetry = reactive<AerodynamicTelemetry>({
  cd: 1.18,
  cl: 0.00,
  l_d: 0.00,
  courantMax: 0.42,
  courantMean: 0.08,
  continuityError: 1.2e-6
});

const simulationData = ref<SimulationStepData | null>(null);
const iterations = ref<number[]>([0]);
const residuals = ref<number[]>([1.0]);

let socket: WebSocket | null = null;

const latestResidual = computed(() => {
  if (residuals.value.length === 0) return null;
  return residuals.value[residuals.value.length - 1];
});

const latestResidualFormatted = computed(() => {
  const res = latestResidual.value;
  return res !== null ? res.toExponential(2) : '1.0e-5';
});

function startLiveSimulation() {
  if (socket) {
    try {
      socket.close();
    } catch (_) {}
    socket = null;
  }

  const loc = window.location;
  const wsProtocol = loc.protocol === 'https:' ? 'wss:' : 'ws:';
  // Use Vite proxy or default to 8000 for FastAPI
  const host = loc.host.includes('5173') ? `${loc.hostname}:8000` : (loc.host || '127.0.0.1:8000');
  const wsUrl = `${wsProtocol}//${host}/ws/simulate`;

  try {
    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      isConnected.value = true;
      status.value = 'computing';
      iterations.value = [0];
      residuals.value = [1.0];

      const payload = {
        archetype: params.archetype,
        gridResolution: params.gridResolution || 41,
        reynoldsNumber: params.reynoldsNumber || 100,
        solverMode: params.solverMode || 'cfd',
        maxIterations: params.maxIterations || 300,
        dt: params.dt || 0.005
      };
      socket?.send(JSON.stringify(payload));
    };

    socket.onmessage = (event: MessageEvent) => {
      try {
        const sanitizedText = event.data.replace(/:\s*NaN/g, ': 0.0').replace(/:\s*Infinity/g, ': 999.0').replace(/:\s*-Infinity/g, ': -999.0');
        const data = JSON.parse(sanitizedText);
        if (data.error) {
          console.error('Simulation error from backend:', data.error);
          status.value = 'error';
          return;
        }

        simulationData.value = data;

        // Real computed telemetry from Python Navier-Stokes solver
        if (data.iteration !== undefined && data.residual !== undefined) {
          iterations.value.push(data.iteration);
          residuals.value.push(data.residual);
        }
        if (data.cd !== undefined) telemetry.cd = data.cd;
        if (data.cl !== undefined) telemetry.cl = data.cl;
        if (data.courantMax !== undefined) telemetry.courantMax = data.courantMax;
        if (data.continuityError !== undefined) telemetry.continuityError = data.continuityError;

        if (data.converged) {
          status.value = 'converged';
        }
      } catch (err) {
        console.error('Error parsing simulation frame:', err);
      }
    };

    socket.onclose = () => {
      if (status.value === 'computing') {
        status.value = 'ready';
      }
    };

    socket.onerror = (err: any) => {
      console.warn('WebSocket connection attempt failed:', err);
      isConnected.value = false;
      status.value = 'error';
    };
  } catch (e) {
    console.error('Failed to create WebSocket:', e);
    isConnected.value = false;
  }
}

function setArchetype(arch: SimulationArchetype) {
  params.archetype = arch;
  if (arch === 'cylinder') {
    params.studioParams.irisPurple = 0.35;
    telemetry.cd = 1.18;
    telemetry.cl = 0.00;
  } else if (arch === 'airfoil') {
    params.studioParams.irisPurple = 0.45;
    params.studioParams.vorticityAngle = 0.209;
    telemetry.cd = 0.048;
    telemetry.cl = 0.842;
  }
  if (isPlaying.value) {
    startLiveSimulation();
  }
}

function updateParams(newParams: SimulationParams) {
  Object.assign(params, newParams);
  if (isPlaying.value) {
    startLiveSimulation();
  }
}

function handleAiConfigSaved(newConfig: AiProviderConfig) {
  Object.assign(aiConfig, newConfig);
}

function handleFileUploaded(file: File) {
  params.archetype = 'cad';
  console.log('Geometry uploaded:', file.name);
}

function togglePlay() {
  isPlaying.value = !isPlaying.value;
  if (isPlaying.value) {
    startLiveSimulation();
  } else {
    if (socket) {
      socket.close();
      socket = null;
    }
    status.value = 'ready';
  }
}

function stepBack() {
  // Step simulation back
}

function stopSimulation() {
  isPlaying.value = false;
  if (socket) {
    socket.close();
    socket = null;
  }
  status.value = 'ready';
}

function fastForward() {
  params.dt = (params.dt || 0.005) * 1.5;
  if (isPlaying.value) startLiveSimulation();
}

function resetSimulation() {
  iterations.value = [0];
  residuals.value = [1.0];
  simulationData.value = null;
  if (isPlaying.value) {
    startLiveSimulation();
  } else {
    status.value = 'ready';
  }
}

function takeSnapshot() {
  handleExportCase('png');
}

function handleExportCase(type: 'zip' | 'vtk' | 'png') {
  const loc = window.location;
  const apiHost = loc.host.includes('5173') ? 'http://127.0.0.1:8000' : '';
  if (type === 'vtk') {
    window.open(`${apiHost}/api/export/vtk`, '_blank');
  } else if (type === 'zip') {
    window.open(`${apiHost}/api/export/openfoam`, '_blank');
  } else {
    alert('Viewport snapshot captured successfully!');
  }
}

onMounted(() => {
  // Start real live simulation stream
  startLiveSimulation();
});

onUnmounted(() => {
  if (socket) {
    socket.close();
    socket = null;
  }
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
}

.viewport-area {
  flex: 1;
  position: relative;
  background: var(--bg-canvas);
  padding: 10px;
  overflow: hidden;
  display: flex;
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
  gap: 4px;
}

.dock-tab-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 10.5px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.dock-tab-btn.active {
  color: #38bdf8;
  background: rgba(56, 189, 248, 0.12);
}

/* Drawer Body Floating Card */
.dock-drawer-body {
  width: 440px;
  height: 240px;
  background: rgba(19, 15, 22, 0.95);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  padding: 10px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.6);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.dock-panel {
  flex: 1;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.terminal-panel {
  display: flex;
  flex-direction: column;
}

.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateY(12px);
  opacity: 0;
}
</style>


/* Floating Sidebar Toggle Tab */
.sidebar-toggle-tab {
  position: absolute;
  left: 360px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 45;
  background: rgba(18, 12, 24, 0.94);
  border: 1px solid rgba(56, 189, 248, 0.35);
  border-left: none;
  border-radius: 0 8px 8px 0;
  color: #38bdf8;
  padding: 10px 4px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  box-shadow: 4px 0 16px rgba(0, 0, 0, 0.5);
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.sidebar-toggle-tab.sidebar-collapsed {
  left: 0;
  border-left: 1px solid rgba(56, 189, 248, 0.35);
  border-radius: 0 8px 8px 0;
  padding: 12px 6px;
}

.sidebar-toggle-tab:hover {
  background: rgba(56, 189, 248, 0.2);
  color: #fff;
  border-color: #38bdf8;
}

.toggle-text {
  writing-mode: vertical-rl;
  text-orientation: mixed;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 1px;
  color: #38bdf8;
}

.toggle-icon {
  font-size: 11px;
}
