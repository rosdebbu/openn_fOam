<template>
  <div class="app-layout">
    <!-- Top Navigation Header -->
    <HeaderNavbar
      :isPlaying="isPlaying"
      :isConnected="isConnected"
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
        :params="params"
        :isComputing="status === 'computing'"
        @update:params="updateParams"
        @fileUploaded="handleFileUploaded"
      />

      <!-- Right Main 3D CFD Viewport -->
      <main class="viewport-area">
        <CfdThree3D
          :data="simulationData"
          :params="params"
        />

        <!-- Floating Logarithmic Residual Convergence Chart -->
        <div class="floating-residual-overlay">
          <ResidualChart
            :iterations="iterations"
            :residuals="residuals"
            :latestResidual="latestResidual"
          />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue';
import type { SimulationParams, SimulationStepData } from './types/cfd';

import HeaderNavbar from './components/HeaderNavbar.vue';
import SidebarControls from './components/SidebarControls.vue';
import CfdThree3D from './components/CfdThree3D.vue';
import ResidualChart from './components/ResidualChart.vue';

// Studio Simulation Parameters matching Mockup
const params = reactive<SimulationParams>({
  caseType: 'cavity',
  solverMode: 'ai',
  turbulenceModel: 'k-epsilon',
  reynoldsNumber: 100,
  gridResolution: 41,
  maxIterations: 1000,
  dt: 0.005,
  tolerance: 1e-5,
  studioParams: {
    irisPurple: 0.182,
    vorticityAngle: 0.152,
    vorticityCore: 30,
    butterscotchCore: 84.899
  }
});

const isPlaying = ref(true);
const isConnected = ref(true);
const status = ref<'ready' | 'computing' | 'converged' | 'error'>('computing');

const simulationData = ref<SimulationStepData | null>(null);
const iterations = ref<number[]>([0, 20, 50, 100, 150, 200]);
const residuals = ref<number[]>([1.0, 0.1, 0.01, 0.001, 1e-5, 1e-13]);

let socket: any = null;
let simInterval: any = null;

const latestResidual = computed(() => {
  if (residuals.value.length === 0) return null;
  return residuals.value[residuals.value.length - 1];
});

function updateParams(newParams: SimulationParams) {
  Object.assign(params, newParams);
}

function handleFileUploaded(file: File) {
  console.log('Geometry / photo uploaded:', file.name);
}

function togglePlay() {
  isPlaying.value = !isPlaying.value;
  if (isPlaying.value) {
    status.value = 'computing';
  } else {
    status.value = 'ready';
  }
}

function stepBack() {
  // Step simulation back
}

function stopSimulation() {
  isPlaying.value = false;
  status.value = 'ready';
}

function fastForward() {
  // Accelerate simulation
}

function resetSimulation() {
  isPlaying.value = false;
  status.value = 'ready';
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
  // Initialize simulated live residual convergence updates
  simInterval = setInterval(() => {
    if (isPlaying.value) {
      const lastIter = iterations.value[iterations.value.length - 1] || 0;
      if (lastIter < 200) {
        iterations.value.push(lastIter + 5);
        const lastRes = residuals.value[residuals.value.length - 1] || 1e-3;
        residuals.value.push(Math.max(1e-13, lastRes * 0.85 * (1 + (Math.random() - 0.5) * 0.1)));
      }
    }
  }, 1000);
});

onUnmounted(() => {
  if (socket) socket.close();
  if (simInterval) clearInterval(simInterval);
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

.floating-residual-overlay {
  position: absolute;
  bottom: 24px;
  right: 24px;
  z-index: 40;
}
</style>
