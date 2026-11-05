<template>
  <div class="openfoam-terminal-card" :class="{ collapsed: isCollapsed }">
    <div class="terminal-header" @click="isCollapsed = !isCollapsed">
      <div class="header-left">
        <span class="term-icon">📟</span>
        <span class="term-title">OpenFOAM Solver Execution Log (FVM Stream)</span>
        <span class="pulse-indicator"></span>
      </div>
      <div class="header-actions" @click.stop>
        <button class="term-action-btn" @click="isAutoScroll = !isAutoScroll" :title="isAutoScroll ? 'Auto-scroll ON' : 'Auto-scroll OFF'">
          {{ isAutoScroll ? '⬇ Auto-scroll' : '⏸ Paused' }}
        </button>
        <button class="term-action-btn" @click="clearLogs" title="Clear log window">
          🗑 Clear
        </button>
        <button class="term-toggle-btn" @click="isCollapsed = !isCollapsed">
          {{ isCollapsed ? '▲' : '▼' }}
        </button>
      </div>
    </div>

    <div v-show="!isCollapsed" class="terminal-body" ref="termBodyRef">
      <div class="openfoam-ascii-banner">
/*--------------------------------*- C++ -*----------------------------------*\
| =========                 |                                                 |
| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   O peration     | Version:  v2406                                 |
|   \\  /    A nd           | Website:  www.openfoam.com                      |
|    \\/     M anipulation  | Solver:   {{ activeSolverName }}
\*---------------------------------------------------------------------------*/
      </div>

      <div v-for="(line, idx) in logs" :key="idx" class="term-line" :class="line.type">
        <span class="line-time">[{{ line.time }}]</span>
        <span class="line-text">{{ line.text }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue';
import type { SimulationArchetype, AerodynamicTelemetry } from '../types/cfd';

const props = defineProps<{
  archetype: SimulationArchetype;
  isPlaying: boolean;
  telemetry: AerodynamicTelemetry;
}>();

const isCollapsed = ref(false);
const isAutoScroll = ref(true);
const termBodyRef = ref<HTMLDivElement | null>(null);

interface LogEntry {
  time: string;
  text: string;
  type: 'info' | 'solver' | 'p-solve' | 'force' | 'continuity' | 'header';
}

const logs = ref<LogEntry[]>([]);
let intervalId: any = null;
let simTime = 0.00;
let stepCounter = 0;

const activeSolverName = computed(() => {
  switch (props.archetype) {
    case 'airfoil': return 'simpleFoam (Incompressible RAS)';
    case 'cylinder': return 'pimpleFoam (Transient Vortex Shedding)';
    case 'venturi': return 'rhoSimpleFoam (Compressible Nozzle)';
    case 'cavity': return 'icoFoam (Transient Laminar)';
    case 'cad': return 'snappyHexMesh + simpleFoam';
    case 'plume':
    default: return 'buoyantBoussinesqSimpleFoam (Aerothermal)';
  }
});

function formatTime(t: number) {
  return t.toFixed(3) + 's';
}

function generateNextLogStep() {
  if (!props.isPlaying) return;

  simTime += 0.005;
  stepCounter++;

  const courant = (props.telemetry.courantMax * (0.95 + Math.random() * 0.1)).toFixed(3);
  const courantMean = (props.telemetry.courantMean * (0.95 + Math.random() * 0.1)).toFixed(3);

  const initialUx = (0.04 * Math.exp(-stepCounter * 0.03) + Math.random() * 0.002).toExponential(4);
  const finalUx = (1.2e-5 * (1 + Math.random() * 0.2)).toExponential(4);

  const initialP = (0.12 * Math.exp(-stepCounter * 0.02) + Math.random() * 0.005).toExponential(4);
  const finalP = (2.4e-6 * (1 + Math.random() * 0.3)).toExponential(4);

  const newLines: LogEntry[] = [
    { time: formatTime(simTime), text: `Time = ${formatTime(simTime)}, Courant Number mean: ${courantMean} max: ${courant}`, type: 'header' },
    { time: formatTime(simTime), text: `DILUPBiCGStab:  Solving for Ux, Initial residual = ${initialUx}, Final residual = ${finalUx}, No Iterations 4`, type: 'solver' },
    { time: formatTime(simTime), text: `DILUPBiCGStab:  Solving for Uy, Initial residual = ${initialUx}, Final residual = ${finalUx}, No Iterations 4`, type: 'solver' },
    { time: formatTime(simTime), text: `GAMG:  Solving for p, Initial residual = ${initialP}, Final residual = ${finalP}, No Iterations 11`, type: 'p-solve' },
    { time: formatTime(simTime), text: `time step continuity errors : sum local = ${(Math.random() * 2e-6).toExponential(3)}, global = -${(Math.random() * 4e-7).toExponential(3)}, cumulative = -${(Math.random() * 8e-7).toExponential(3)}`, type: 'continuity' },
    { time: formatTime(simTime), text: `Forces [Cd: ${props.telemetry.cd.toFixed(3)}, Cl: ${props.telemetry.cl.toFixed(3)}, L/D: ${props.telemetry.l_d.toFixed(2)}]`, type: 'force' }
  ];

  if (props.archetype === 'plume') {
    newLines.push({
      time: formatTime(simTime),
      text: `bounding T, min: 293.15 max: ${(293.15 + (props.telemetry.cd * 50)).toFixed(2)}`,
      type: 'info'
    });
  }

  logs.value.push(...newLines);

  // Keep max 120 lines in memory for performance
  if (logs.value.length > 120) {
    logs.value.splice(0, logs.value.length - 120);
  }

  if (isAutoScroll.value) {
    nextTick(() => {
      if (termBodyRef.value) {
        termBodyRef.value.scrollTop = termBodyRef.value.scrollHeight;
      }
    });
  }
}

function clearLogs() {
  logs.value = [];
}

onMounted(() => {
  // Generate initial log lines
  generateNextLogStep();
  intervalId = setInterval(generateNextLogStep, 1500);
});

onUnmounted(() => {
  if (intervalId) clearInterval(intervalId);
});
</script>

<style scoped>
.openfoam-terminal-card {
  background: #0b0f16;
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.7);
  user-select: text;
  width: 100%;
}

.terminal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #141b24;
  border-bottom: 1px solid var(--border-subtle);
  cursor: pointer;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.term-icon {
  font-size: 14px;
}

.term-title {
  font-size: 11.5px;
  font-weight: 700;
  color: #38bdf8;
}

.pulse-indicator {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 6px #10b981;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.term-action-btn {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #94a3b8;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 10px;
  cursor: pointer;
  font-family: inherit;
}

.term-action-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #ffffff;
}

.term-toggle-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 11px;
  cursor: pointer;
  padding: 2px 4px;
}

.terminal-body {
  padding: 10px 12px;
  height: 140px;
  overflow-y: auto;
  background: #090d14;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.openfoam-ascii-banner {
  font-size: 9px;
  color: #64748b;
  white-space: pre;
  line-height: 1.2;
  margin-bottom: 6px;
}

.term-line {
  display: flex;
  gap: 8px;
  font-size: 10.5px;
  line-height: 1.35;
}

.line-time {
  color: #64748b;
  font-size: 9.5px;
  flex-shrink: 0;
}

.term-line.header .line-text {
  color: #f1f5f9;
  font-weight: 600;
}

.term-line.solver .line-text {
  color: #38bdf8;
}

.term-line.p-solve .line-text {
  color: #c084fc;
}

.term-line.continuity .line-text {
  color: #34d399;
}

.term-line.force .line-text {
  color: #fbbf24;
  font-weight: 600;
}

.term-line.info .line-text {
  color: #94a3b8;
}
</style>
