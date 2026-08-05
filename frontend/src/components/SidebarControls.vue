<template>
  <aside class="sidebar-controls">
    <div class="sidebar-header">
      <button
        class="tab-btn"
        :class="{ active: activeSidebarTab === 'controls' }"
        @click="activeSidebarTab = 'controls'"
      >
        ⚙️ Controls
      </button>
      <button
        class="tab-btn"
        :class="{ active: activeSidebarTab === 'dicts' }"
        @click="activeSidebarTab = 'dicts'"
      >
        📄 OpenFOAM Dicts
      </button>
    </div>

    <!-- Controls Panel -->
    <div v-if="activeSidebarTab === 'controls'" class="panel-content">
      <!-- Case Selection -->
      <div class="control-group">
        <label for="case-select">Problem Case</label>
        <select
          id="case-select"
          v-model="localParams.caseType"
          @change="emitUpdate"
        >
          <option value="cavity">Lid-Driven Cavity Flow</option>
          <option value="channel">Channel Flow (Poiseuille)</option>
          <option value="obstacle">Flow Past Obstacle</option>
          <option value="pipe">Pipe Flow</option>
        </select>
      </div>

      <!-- Solver Engine -->
      <div class="control-group">
        <label for="solver-mode">Engine Mode</label>
        <select
          id="solver-mode"
          v-model="localParams.solverMode"
          @change="emitUpdate"
        >
          <option value="cfd">Traditional CFD (SciPy Sparse SIMPLE)</option>
          <option value="ai">AI PINN Predictor (Instant 0.05s)</option>
        </select>
      </div>

      <!-- Turbulence Model -->
      <div class="control-group">
        <label for="turb-model">Turbulence Model</label>
        <select
          id="turb-model"
          v-model="localParams.turbulenceModel"
          @change="emitUpdate"
        >
          <option value="laminar">Laminar</option>
          <option value="k-epsilon">RANS: k-ε (Standard)</option>
          <option value="k-omega-sst">RANS: k-ω SST (Menter)</option>
        </select>
      </div>

      <!-- Reynolds Number -->
      <div class="control-group">
        <div class="label-with-val">
          <label for="re-slider">Reynolds Number (Re)</label>
          <span class="val-badge">{{ localParams.reynoldsNumber }}</span>
        </div>
        <input
          type="range"
          id="re-slider"
          min="10"
          max="2000"
          step="10"
          v-model.number="localParams.reynoldsNumber"
          @input="emitUpdate"
        />
      </div>

      <!-- Grid Resolution -->
      <div class="control-group">
        <div class="label-with-val">
          <label for="grid-slider">Grid Resolution (N × N)</label>
          <span class="val-badge">{{ localParams.gridResolution }}</span>
        </div>
        <input
          type="range"
          id="grid-slider"
          min="21"
          max="101"
          step="10"
          v-model.number="localParams.gridResolution"
          @input="emitUpdate"
        />
      </div>

      <!-- Visualization Mode -->
      <div class="control-group">
        <label for="viz-type">Visualization Mode</label>
        <select
          id="viz-type"
          :value="vizMode"
          @change="$emit('update:vizMode', ($event.target as HTMLSelectElement).value as VizMode)"
        >
          <option value="speed">2D Velocity Magnitude |U|</option>
          <option value="pressure">2D Pressure Field (p)</option>
          <option value="streamlines">2D Streamlines & Particles</option>
          <option value="vectors">2D Velocity Vector Arrows</option>
          <option value="three3d">3D WebGL Heightmap (Three.js)</option>
        </select>
      </div>

      <!-- Action Buttons -->
      <div class="action-buttons">
        <button
          class="btn btn-run"
          :disabled="isComputing"
          @click="$emit('runSimulation')"
        >
          <span v-if="!isComputing">🚀 Run Simulation</span>
          <span v-else>⏳ Computing...</span>
        </button>

        <button
          class="btn btn-reset"
          @click="$emit('resetSimulation')"
        >
          🔄 Reset
        </button>
      </div>
    </div>

    <!-- Dicts Panel -->
    <div v-else class="panel-content dict-panel">
      <OpenFoamDictEditor :params="localParams" />
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue';
import type { SimulationParams, VizMode } from '../types/cfd';
import OpenFoamDictEditor from './OpenFoamDictEditor.vue';

const props = defineProps<{
  params: SimulationParams;
  vizMode: VizMode;
  isComputing: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:params', params: SimulationParams): void;
  (e: 'update:vizMode', vizMode: VizMode): void;
  (e: 'runSimulation'): void;
  (e: 'resetSimulation'): void;
}>();

const activeSidebarTab = ref<'controls' | 'dicts'>('controls');

const localParams = reactive<SimulationParams>({ ...props.params });

watch(() => props.params, (newVal) => {
  Object.assign(localParams, newVal);
}, { deep: true });

function emitUpdate() {
  emit('update:params', { ...localParams });
}
</script>

<style scoped>
.sidebar-controls {
  width: 340px;
  background: rgba(15, 23, 42, 0.95);
  border-right: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  flex-direction: column;
  height: calc(100vh - 60px);
  overflow-y: auto;
}

.sidebar-header {
  display: flex;
  background: rgba(30, 41, 59, 0.6);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.tab-btn {
  flex: 1;
  padding: 12px 16px;
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tab-btn.active {
  color: #00d2ff;
  border-bottom: 2px solid #00d2ff;
  background: rgba(0, 210, 255, 0.05);
}

.panel-content {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  flex: 1;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.control-group label {
  font-size: 12px;
  font-weight: 600;
  color: #cbd5e1;
}

.label-with-val {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.val-badge {
  font-size: 12px;
  font-weight: 700;
  color: #00d2ff;
  background: rgba(0, 210, 255, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
}

select, input[type="text"], input[type="number"] {
  background: #1e293b;
  color: #f8fafc;
  border: 1px solid #334155;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s;
}

select:focus, input:focus {
  border-color: #00d2ff;
}

input[type="range"] {
  accent-color: #00d2ff;
  height: 6px;
  border-radius: 3px;
  cursor: pointer;
}

.action-buttons {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

.btn {
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.2s ease;
}

.btn-run {
  flex: 2;
  background: linear-gradient(135deg, #00d2ff 0%, #3a7bd5 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(0, 210, 255, 0.3);
}

.btn-run:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 210, 255, 0.5);
}

.btn-run:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-reset {
  flex: 1;
  background: rgba(255, 255, 255, 0.08);
  color: #cbd5e1;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.btn-reset:hover {
  background: rgba(255, 255, 255, 0.15);
}

.dict-panel {
  padding: 10px 0;
}
</style>
