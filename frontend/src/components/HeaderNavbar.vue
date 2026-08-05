<template>
  <header class="header-navbar">
    <div class="brand">
      <div class="logo-badge">⚡</div>
      <div class="brand-text">
        <span class="brand-title">OpenZess <small>Studio v2.0</small></span>
        <span class="brand-subtitle">OpenFOAM Vue 3 + Three.js WebGL CFD Interface</span>
      </div>
    </div>

    <div class="header-actions">
      <!-- Status Badge -->
      <div class="status-indicator" :class="statusClass">
        <span class="status-dot"></span>
        <span class="status-text">{{ statusText }}</span>
      </div>

      <!-- Mode Badge -->
      <div class="mode-indicator" :class="params.solverMode">
        {{ params.solverMode === 'ai' ? '🧠 AI PINN Surrogate' : '🔬 SciPy CFD Solver' }}
      </div>

      <!-- Colormap Dropdown -->
      <div class="colormap-select-wrapper">
        <label for="colormap-select">Palette:</label>
        <select
          id="colormap-select"
          :value="colormap"
          @change="$emit('update:colormap', (($event.target as HTMLSelectElement).value as ColormapScheme))"
        >
          <option value="inferno">🔥 Inferno</option>
          <option value="jet">🌈 Jet</option>
          <option value="coolwarm">❄️ Coolwarm</option>
          <option value="viridis">🌌 Viridis</option>
          <option value="pressure">🔴 Blue-Red (Pressure)</option>
        </select>
      </div>

      <!-- Export VTK Button -->
      <button class="btn btn-export" @click="$emit('exportVtk')" title="Export simulation for ParaView">
        <span>📦 Export ParaView VTK</span>
      </button>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { SimulationParams, ColormapScheme } from '../types/cfd';

const props = defineProps<{
  params: SimulationParams;
  status: 'ready' | 'computing' | 'converged' | 'error';
  colormap: ColormapScheme;
}>();

defineEmits<{
  (e: 'update:colormap', val: ColormapScheme): void;
  (e: 'exportVtk'): void;
}>();

const statusText = computed(() => {
  switch (props.status) {
    case 'computing': return 'Computing...';
    case 'converged': return 'Converged (Residual < 1e-5)';
    case 'error': return 'Error';
    default: return 'Ready';
  }
});

const statusClass = computed(() => props.status);
</script>

<style scoped>
.header-navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 60px;
  padding: 0 20px;
  background: rgba(15, 23, 42, 0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-badge {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: linear-gradient(135deg, #00d2ff 0%, #3a7bd5 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  box-shadow: 0 0 15px rgba(0, 210, 255, 0.4);
}

.brand-text {
  display: flex;
  flex-direction: column;
}

.brand-title {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0.5px;
  color: #ffffff;
}

.brand-title small {
  font-size: 11px;
  font-weight: 500;
  color: #00d2ff;
  background: rgba(0, 210, 255, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
}

.brand-subtitle {
  font-size: 11px;
  color: #94a3b8;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #94a3b8;
}

.status-indicator.ready .status-dot {
  background: #38bdf8;
  box-shadow: 0 0 8px #38bdf8;
}

.status-indicator.computing .status-dot {
  background: #f59e0b;
  box-shadow: 0 0 8px #f59e0b;
  animation: pulse 1s infinite alternate;
}

.status-indicator.converged .status-dot {
  background: #10b981;
  box-shadow: 0 0 8px #10b981;
}

.mode-indicator {
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

.mode-indicator.cfd {
  background: rgba(56, 189, 248, 0.15);
  color: #38bdf8;
  border: 1px solid rgba(56, 189, 248, 0.3);
}

.mode-indicator.ai {
  background: rgba(168, 85, 247, 0.15);
  color: #c084fc;
  border: 1px solid rgba(168, 85, 247, 0.3);
}

.colormap-select-wrapper {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #cbd5e1;
}

.colormap-select-wrapper select {
  background: #1e293b;
  color: #f8fafc;
  border: 1px solid #334155;
  padding: 5px 10px;
  border-radius: 6px;
  font-size: 12px;
  cursor: pointer;
}

.btn-export {
  background: linear-gradient(135deg, #059669 0%, #10b981 100%);
  color: white;
  border: none;
  padding: 8px 14px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 10px rgba(16, 185, 129, 0.3);
}

.btn-export:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 15px rgba(16, 185, 129, 0.5);
}

@keyframes pulse {
  from { opacity: 0.5; }
  to { opacity: 1; }
}
</style>
