<template>
  <div class="residual-convergence-card">
    <div class="chart-header">
      <span class="chart-title">Logarithmic residual convergence</span>
    </div>

    <div class="chart-body">
      <div class="y-axis-labels">
        <span v-for="label in yLabels" :key="label">{{ label }}</span>
      </div>

      <div class="canvas-container">
        <canvas ref="canvasRef" width="220" height="130"></canvas>
        <div class="y-axis-title">Residual chart</div>
      </div>
    </div>

    <div class="x-axis-footer">
      <div class="x-ticks">
        <span v-for="tick in xTicks" :key="tick">{{ tick }}</span>
      </div>
      <span class="x-axis-label">Iterative solver</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';

const props = defineProps<{
  iterations: number[];
  residuals: number[];
  latestResidual: number | null;
}>();

const canvasRef = ref<HTMLCanvasElement | null>(null);

// Axis extents shared by the canvas plot and the tick labels, so the labels
// always describe what is drawn. Residuals are plotted on whole decades.
const finiteResiduals = computed(() => props.residuals.filter(r => Number.isFinite(r) && r > 0));
// Labels sit on whole decades: the span is padded to a multiple of `step`
// so the evenly spaced labels coincide with the plotted log scale.
const decades = computed(() => {
  const r = finiteResiduals.value;
  if (r.length < 2) return { top: 0, bottom: -4, step: 1 };
  const top = Math.ceil(Math.log10(Math.max(...r)));
  const low = Math.min(Math.floor(Math.log10(Math.min(...r))), top - 1);
  const step = Math.ceil((top - low) / 5);
  return { top, bottom: top - Math.ceil((top - low) / step) * step, step };
});
const iterMax = computed(() => Math.max(...props.iterations, 1));

const SUPERSCRIPT: Record<string, string> = {
  '-': '⁻', '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹'
};
const yLabels = computed(() => {
  const { top, bottom, step } = decades.value;
  const labels: string[] = [];
  for (let exp = top; exp >= bottom; exp -= step) {
    labels.push('10' + String(exp).split('').map(c => SUPERSCRIPT[c]).join(''));
  }
  return labels;
});
const xTicks = computed(() => [0, 1, 2, 3, 4].map(k => Math.round((k * iterMax.value) / 4)));

function drawChart() {
  const canvas = canvasRef.value;
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const w = canvas.width;
  const h = canvas.height;

  // Clear
  ctx.clearRect(0, 0, w, h);

  // Background Grid Lines
  ctx.strokeStyle = 'rgba(255, 255, 255, 0.07)';
  ctx.lineWidth = 1;

  // Horizontal grid lines
  for (let i = 1; i < 5; i++) {
    const y = (h / 5) * i;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(w, y);
    ctx.stroke();
  }

  // Vertical grid lines
  for (let i = 1; i < 5; i++) {
    const x = (w / 5) * i;
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, h);
    ctx.stroke();
  }

  // Create neon violet/cyan gradient
  const gradient = ctx.createLinearGradient(0, 0, w, h);
  gradient.addColorStop(0, '#c084fc');
  gradient.addColorStop(0.5, '#a855f7');
  gradient.addColorStop(1, '#818cf8');

  ctx.strokeStyle = gradient;
  ctx.lineWidth = 2;

  // Plot the real residual history only — nothing is drawn until the
  // solver has reported at least two points.
  if (finiteResiduals.value.length < 2) {
    ctx.fillStyle = 'rgba(255, 255, 255, 0.45)';
    ctx.font = '11px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Waiting for solver residuals…', w / 2, h / 2);
    return;
  }

  const { top, bottom } = decades.value;
  const span = (top - bottom) || 1;
  const points: Array<{ x: number; y: number }> = [];
  for (let k = 0; k < props.residuals.length; k++) {
    const r = props.residuals[k];
    if (!Number.isFinite(r) || r <= 0) continue;
    const iter = props.iterations[k] ?? k;
    const x = Math.min(1, iter / iterMax.value) * w;
    const y = ((top - Math.log10(r)) / span) * h;
    points.push({ x, y: Math.min(h - 2, Math.max(2, y)) });
  }

  ctx.beginPath();
  points.forEach((pt, idx) => {
    if (idx === 0) ctx.moveTo(pt.x, pt.y);
    else ctx.lineTo(pt.x, pt.y);
  });
  ctx.stroke();

  ctx.shadowColor = 'rgba(168, 85, 247, 0.5)';
  ctx.shadowBlur = 8;
  ctx.stroke();
  ctx.shadowBlur = 0;
}

watch(() => [props.residuals, props.iterations], () => {
  drawChart();
}, { deep: true });

onMounted(() => {
  drawChart();
});
</script>

<style scoped>
.residual-convergence-card {
  background: rgba(20, 26, 36, 0.88);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  padding: 10px 14px;
  width: 280px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.6);
  user-select: none;
}

.chart-header {
  margin-bottom: 6px;
}

.chart-title {
  font-size: 11.5px;
  font-weight: 600;
  color: #f1f5f9;
  letter-spacing: -0.1px;
}

.chart-body {
  display: flex;
  gap: 6px;
  position: relative;
}

.y-axis-labels {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  color: #94a3b8;
  padding-bottom: 4px;
  min-width: 32px;
}

.canvas-container {
  flex: 1;
  position: relative;
  border-left: 1px solid rgba(255, 255, 255, 0.15);
  border-bottom: 1px solid rgba(255, 255, 255, 0.15);
}

.canvas-container canvas {
  width: 100%;
  height: 120px;
  display: block;
}

.y-axis-title {
  position: absolute;
  left: -20px;
  top: 50%;
  transform: translateY(-50%) rotate(-90deg);
  font-size: 8px;
  color: #64748b;
  display: none;
}

.x-axis-footer {
  margin-left: 38px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-top: 4px;
}

.x-ticks {
  display: flex;
  justify-content: space-between;
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  color: #94a3b8;
}

.x-axis-label {
  text-align: center;
  font-size: 9.5px;
  color: #94a3b8;
}
</style>
