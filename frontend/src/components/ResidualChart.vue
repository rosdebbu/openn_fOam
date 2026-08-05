<template>
  <div class="residual-chart-box">
    <div class="chart-header">
      <span class="chart-title">Convergence Residual</span>
      <span v-if="latestResidual !== null" class="latest-res">
        {{ latestResidual.toExponential(4) }}
      </span>
    </div>
    <div class="canvas-wrapper">
      <canvas ref="chartCanvasRef"></canvas>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { Chart, LineController, LineElement, PointElement, LinearScale, LogarithmicScale, CategoryScale, Title, Tooltip } from 'chart.js';

Chart.register(LineController, LineElement, PointElement, LinearScale, LogarithmicScale, CategoryScale, Title, Tooltip);

const props = defineProps<{
  iterations: number[];
  residuals: number[];
  latestResidual: number | null;
}>();

const chartCanvasRef = ref<HTMLCanvasElement | null>(null);
let chartInstance: Chart | null = null;

function initChart() {
  if (!chartCanvasRef.value) return;

  chartInstance = new Chart(chartCanvasRef.value, {
    type: 'line',
    data: {
      labels: [],
      datasets: [
        {
          label: 'Residual',
          data: [],
          borderColor: '#00d2ff',
          backgroundColor: 'rgba(0, 210, 255, 0.1)',
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.2,
          fill: true
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          display: true,
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#64748b', font: { size: 10 } }
        },
        y: {
          type: 'logarithmic',
          display: true,
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#64748b', font: { size: 10 } }
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: { enabled: true }
      }
    }
  });
}

function updateChart() {
  if (!chartInstance) return;

  chartInstance.data.labels = props.iterations.map(i => i.toString());
  chartInstance.data.datasets[0].data = props.residuals;
  chartInstance.update();
}

watch(() => props.residuals, () => {
  updateChart();
}, { deep: true });

onMounted(() => {
  initChart();
});
</script>

<style scoped>
.residual-chart-box {
  background: rgba(15, 23, 42, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  height: 180px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.chart-title {
  font-size: 12px;
  font-weight: 700;
  color: #cbd5e1;
}

.latest-res {
  font-size: 11px;
  font-family: monospace;
  font-weight: 600;
  color: #00d2ff;
  background: rgba(0, 210, 255, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
}

.canvas-wrapper {
  flex: 1;
  width: 100%;
  position: relative;
}
</style>
