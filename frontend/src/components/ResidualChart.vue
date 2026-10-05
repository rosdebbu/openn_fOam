<template>
  <div class="residual-convergence-card">
    <div class="chart-header">
      <span class="chart-title">Logarithmic residual convergence</span>
    </div>

    <div class="chart-body">
      <div class="y-axis-labels">
        <span>10⁰</span>
        <span>10⁻¹</span>
        <span>10⁻²</span>
        <span>10⁻³</span>
        <span>10⁻⁴</span>
      </div>

      <div class="canvas-container">
        <canvas ref="canvasRef" width="220" height="130"></canvas>
        <div class="y-axis-title">Residual chart</div>
      </div>
    </div>

    <div class="x-axis-footer">
      <div class="x-ticks">
        <span>0</span>
        <span>50</span>
        <span>100</span>
        <span>150</span>
        <span>200</span>
      </div>
      <span class="x-axis-label">Iterative solver</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';

const props = defineProps<{
  iterations: number[];
  residuals: number[];
  latestResidual: number | null;
}>();

const canvasRef = ref<HTMLCanvasElement | null>(null);

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

  // Plot the real residual history on a log scale when available;
  // fall back to the synthetic decay curve when no data exists yet.
  const reals = props.residuals.filter(r => Number.isFinite(r) && r > 0);
  if (reals.length >= 2) {
    const maxLog = Math.log10(Math.max(...reals));
    const minLog = Math.log10(Math.min(...reals));
    const span = (maxLog - minLog) || 1;
    const iterMax = Math.max(...props.iterations, 1);

    // Map each residual to its iteration position so multiple pushes of the
    // same iteration (from both WS frames and the local ticker) are handled.
    const points: Array<{ x: number; y: number }> = [];
    let pointIdx = 0;
    for (let k = 0; k < props.residuals.length; k++) {
      const r = props.residuals[k];
      if (!Number.isFinite(r) || r <= 0) continue;
      const iter = props.iterations[k] ?? pointIdx;
      const xNorm = Math.min(1, iter / iterMax);
      const logNorm = (Math.log10(r) - minLog) / span;
      const y = Math.min(h - 4, Math.max(4, (1 - logNorm) * (h - 8) + 4));
      points.push({ x: xNorm * w, y });
      pointIdx++;
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
    return;
  }

  // Render synthetic logarithmic decay curve matching visual mockup
  const count = 200;
  ctx.beginPath();
  for (let i = 0; i <= count; i++) {
    const xNorm = i / count;
    const x = xNorm * w;

    const noise = Math.sin(i * 0.8) * 0.015 + (Math.random() - 0.5) * 0.01;
    const yNorm = Math.pow(xNorm, 0.65) * 0.92 + noise;
    const y = Math.min(h - 4, Math.max(4, yNorm * h));

    if (i === 0) {
      ctx.moveTo(x, 4);
    } else {
      ctx.lineTo(x, y);
    }
  }

  ctx.stroke();

  // Glow shadow effect
  ctx.shadowColor = 'rgba(168, 85, 247, 0.5)';
  ctx.shadowBlur = 8;
  ctx.stroke();
  ctx.shadowBlur = 0; // reset
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
