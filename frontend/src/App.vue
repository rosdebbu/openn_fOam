<template>
  <div class="app-layout">
    <!-- Top Navigation Header -->
    <HeaderNavbar
      :params="params"
      :status="status"
      v-model:colormap="colormap"
      @exportVtk="handleExportVtk"
    />

    <!-- Main Studio Body -->
    <div class="studio-body">
      <!-- Left Sidebar Controls & Dict Editor -->
      <SidebarControls
        v-model:params="params"
        v-model:vizMode="vizMode"
        :isComputing="status === 'computing'"
        @runSimulation="startSimulation"
        @resetSimulation="resetSimulation"
      />

      <!-- Main Central Viewport -->
      <main class="viewport-area">
        <div class="viewport-header">
          <div class="viewport-title">
            <span>🌐 Flow Field Viewport — {{ vizTitle }}</span>
          </div>

          <div class="viewport-stats">
            <span class="stat-item">Iter: <strong>{{ latestIteration }}</strong></span>
            <span class="stat-item">Residual: <strong>{{ latestResidualFormatted }}</strong></span>
            <span class="stat-item">Grid: <strong>{{ params.gridResolution }}×{{ params.gridResolution }}</strong></span>
          </div>
        </div>

        <div class="viewport-canvas-wrapper">
          <!-- 2D Canvas Viewport -->
          <CfdCanvas2D
            v-if="vizMode !== 'three3d'"
            :data="simulationData"
            :vizMode="vizMode"
            :colormap="colormap"
          />

          <!-- 3D Three.js WebGL Viewport -->
          <CfdThree3D
            v-else
            :data="simulationData"
            :colormap="colormap"
          />
        </div>

        <!-- Lower Panel: Residual Chart & AI Assistant -->
        <div class="lower-panel">
          <ResidualChart
            class="chart-section"
            :iterations="iterations"
            :residuals="residuals"
            :latestResidual="latestResidual"
          />

          <AiAssistant
            class="ai-section"
            :params="params"
          />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onUnmounted } from 'vue';
import type { SimulationParams, SimulationStepData, VizMode, ColormapScheme } from './types/cfd';

import HeaderNavbar from './components/HeaderNavbar.vue';
import SidebarControls from './components/SidebarControls.vue';
import CfdCanvas2D from './components/CfdCanvas2D.vue';
import CfdThree3D from './components/CfdThree3D.vue';
import ResidualChart from './components/ResidualChart.vue';
import AiAssistant from './components/AiAssistant.vue';

// App State
const params = reactive<SimulationParams>({
  caseType: 'cavity',
  solverMode: 'cfd',
  turbulenceModel: 'laminar',
  reynoldsNumber: 100,
  gridResolution: 41,
  maxIterations: 1000,
  dt: 0.005,
  tolerance: 1e-5
});

const vizMode = ref<VizMode>('speed');
const colormap = ref<ColormapScheme>('inferno');
const status = ref<'ready' | 'computing' | 'converged' | 'error'>('ready');

const simulationData = ref<SimulationStepData | null>(null);
const iterations = ref<number[]>([]);
const residuals = ref<number[]>([]);

let socket: WebSocket | null = null;

const latestIteration = computed(() => simulationData.value?.iteration || 0);

const latestResidual = computed(() => {
  if (residuals.value.length === 0) return null;
  return residuals.value[residuals.value.length - 1];
});

const latestResidualFormatted = computed(() => {
  const res = latestResidual.value;
  return res !== null ? res.toExponential(4) : '0.0000e+0';
});

const vizTitle = computed(() => {
  switch (vizMode.value) {
    case 'speed': return '2D Velocity Magnitude |U| Heatmap';
    case 'pressure': return '2D Pressure Field (p) Heatmap';
    case 'streamlines': return '2D Streamlines & Animated Fluid Particles';
    case 'vectors': return '2D Velocity Field Vector Glyphs';
    case 'three3d': return '3D WebGL Heightmap Mesh (Three.js)';
    default: return 'CFD Visualizer';
  }
});

function startSimulation() {
  if (socket) {
    socket.close();
  }

  status.value = 'computing';
  iterations.value = [];
  residuals.value = [];

  // Determine WS host
  const loc = window.location;
  const wsHost = loc.host.includes('5173') || loc.host.includes('localhost')
    ? '127.0.0.1:8000'
    : loc.host;
  const wsUrl = `${loc.protocol === 'https:' ? 'wss:' : 'ws:'}//${wsHost}/ws/simulate`;

  socket = new WebSocket(wsUrl);

  socket.onopen = () => {
    const payload = {
      nx: params.gridResolution,
      ny: params.gridResolution,
      Re: params.reynoldsNumber,
      mode: params.solverMode,
      max_iter: params.maxIterations
    };
    socket?.send(JSON.stringify(payload));
  };

  socket.onmessage = (event) => {
    try {
      const data: SimulationStepData = JSON.parse(event.data);
      if (data.error) {
        alert(`Simulation Error: ${data.error}`);
        status.value = 'error';
        return;
      }

      simulationData.value = data;

      if (data.mode === 'cfd' && data.residual > 0) {
        iterations.value.push(data.iteration);
        residuals.value.push(data.residual);
      }

      if (data.converged) {
        status.value = 'converged';
      }
    } catch (err) {
      console.error('Error parsing WS message:', err);
    }
  };

  socket.onerror = (err) => {
    console.error('WebSocket Error:', err);
    status.value = 'error';
  };

  socket.onclose = () => {
    if (status.value === 'computing') {
      status.value = 'ready';
    }
  };
}

function resetSimulation() {
  if (socket) socket.close();
  status.value = 'ready';
  simulationData.value = null;
  iterations.value = [];
  residuals.value = [];
}

function handleExportVtk() {
  const loc = window.location;
  const apiHost = loc.host.includes('5173') ? 'http://127.0.0.1:8000' : '';
  window.open(`${apiHost}/api/export/vtk`, '_blank');
}

onUnmounted(() => {
  if (socket) socket.close();
});
</script>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  background: #090d16;
  color: #f8fafc;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  overflow: hidden;
}

.studio-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.viewport-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #050811;
  padding: 16px;
  gap: 14px;
  overflow-y: auto;
}

.viewport-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(15, 23, 42, 0.8);
  padding: 10px 18px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.viewport-title {
  font-size: 14px;
  font-weight: 700;
  color: #00d2ff;
}

.viewport-stats {
  display: flex;
  gap: 16px;
}

.stat-item {
  font-size: 12px;
  color: #94a3b8;
}

.stat-item strong {
  color: #f8fafc;
}

.viewport-canvas-wrapper {
  flex: 1;
  min-height: 480px;
  background: #000;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.lower-panel {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

@media (max-width: 1024px) {
  .lower-panel {
    grid-template-columns: 1fr;
  }
}
</style>
