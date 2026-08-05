<template>
  <div class="canvas-2d-container" ref="containerRef">
    <canvas
      ref="canvasRef"
      class="cfd-canvas-2d"
      @mousemove="handleMouseMove"
      @mouseleave="hoverInfo = null"
    ></canvas>

    <!-- Tooltip Overlay -->
    <div v-if="hoverInfo" class="grid-tooltip" :style="{ left: hoverInfo.x + 'px', top: hoverInfo.y + 'px' }">
      <div>Grid: ({{ hoverInfo.gridX }}, {{ hoverInfo.gridY }})</div>
      <div>|U|: {{ hoverInfo.speed.toFixed(4) }} m/s</div>
      <div>u: {{ hoverInfo.u.toFixed(4) }}, v: {{ hoverInfo.v.toFixed(4) }}</div>
      <div>p: {{ hoverInfo.p.toFixed(4) }} Pa</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue';
import type { SimulationStepData, VizMode, ColormapScheme } from '../types/cfd';
import { getColorRgb } from '../utils/colormaps';

const props = defineProps<{
  data: SimulationStepData | null;
  vizMode: VizMode;
  colormap: ColormapScheme;
}>();

const containerRef = ref<HTMLDivElement | null>(null);
const canvasRef = ref<HTMLCanvasElement | null>(null);
const hoverInfo = ref<{ x: number; y: number; gridX: number; gridY: number; u: number; v: number; speed: number; p: number } | null>(null);

let animFrameId: number | null = null;
let particles: Array<{ x: number; y: number; age: number; maxAge: number }> = [];

// Initialize particles for streamline animation
function initParticles(nx: number, ny: number) {
  particles = [];
  const numParticles = 300;
  for (let i = 0; i < numParticles; i++) {
    particles.push({
      x: Math.random() * nx,
      y: Math.random() * ny,
      age: Math.random() * 50,
      maxAge: 40 + Math.random() * 60
    });
  }
}

function render() {
  const canvas = canvasRef.value;
  if (!canvas || !props.data || !props.data.speed) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  const data = props.data;
  const nx = data.speed.length;
  const ny = data.speed[0].length;

  const width = canvas.width;
  const height = canvas.height;

  const cellW = width / nx;
  const cellH = height / ny;

  // Determine scalar field min/max for colormap
  const isPressure = props.vizMode === 'pressure';
  const field = isPressure ? data.p : data.speed;

  let minVal = Infinity;
  let maxVal = -Infinity;
  for (let i = 0; i < nx; i++) {
    for (let j = 0; j < ny; j++) {
      const val = field[i][j];
      if (val < minVal) minVal = val;
      if (val > maxVal) maxVal = val;
    }
  }

  // Draw heatmap pixels
  const imgData = ctx.createImageData(width, height);
  const pixels = imgData.data;

  for (let px = 0; px < width; px++) {
    for (let py = 0; py < height; py++) {
      const i = Math.min(nx - 1, Math.floor(px / cellW));
      const j = Math.min(ny - 1, Math.floor((height - py - 1) / cellH));

      const val = field[i][j];
      const scheme = isPressure ? 'pressure' : props.colormap;
      const [r, g, b] = getColorRgb(val, minVal, maxVal, scheme);

      const idx = (py * width + px) * 4;
      pixels[idx] = r;
      pixels[idx + 1] = g;
      pixels[idx + 2] = b;
      pixels[idx + 3] = 255;
    }
  }
  ctx.putImageData(imgData, 0, 0);

  // Overlay Vector Arrows if selected
  if (props.vizMode === 'vectors') {
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.7)';
    ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
    ctx.lineWidth = 1.2;

    const step = Math.max(1, Math.floor(nx / 20));
    for (let i = step / 2; i < nx; i += step) {
      for (let j = step / 2; j < ny; j += step) {
        const gridI = Math.floor(i);
        const gridJ = Math.floor(j);
        const cx = (gridI + 0.5) * cellW;
        const cy = height - (gridJ + 0.5) * cellH;

        const u = data.u[gridI][gridJ];
        const v = -data.v[gridI][gridJ]; // Flip Y for canvas
        const len = Math.sqrt(u * u + v * v);

        if (len > 1e-4) {
          const arrowLen = Math.min(cellW * 1.5, (len / (maxVal || 1)) * cellW * 2);
          const endX = cx + (u / len) * arrowLen;
          const endY = cy + (v / len) * arrowLen;

          ctx.beginPath();
          ctx.moveTo(cx, cy);
          ctx.lineTo(endX, endY);
          ctx.stroke();

          // Arrow head
          ctx.beginPath();
          ctx.arc(endX, endY, 2, 0, Math.PI * 2);
          ctx.fill();
        }
      }
    }
  }

  // Overlay Streamline Particles if selected
  if (props.vizMode === 'streamlines') {
    if (particles.length === 0) initParticles(nx, ny);

    ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
    ctx.strokeStyle = 'rgba(0, 210, 255, 0.5)';
    ctx.lineWidth = 1.5;

    for (let p of particles) {
      const gx = Math.floor(p.x);
      const gy = Math.floor(p.y);

      if (gx >= 0 && gx < nx && gy >= 0 && gy < ny) {
        const u = data.u[gx][gy];
        const v = data.v[gx][gy];

        const prevCanvasX = (p.x / nx) * width;
        const prevCanvasY = height - (p.y / ny) * height;

        // Move particle forward according to velocity vector
        p.x += u * 0.4;
        p.y += v * 0.4;
        p.age++;

        const canvasX = (p.x / nx) * width;
        const canvasY = height - (p.y / ny) * height;

        ctx.beginPath();
        ctx.moveTo(prevCanvasX, prevCanvasY);
        ctx.lineTo(canvasX, canvasY);
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(canvasX, canvasY, 1.5, 0, Math.PI * 2);
        ctx.fill();
      }

      // Respawn particle if aged out or out of bounds
      if (p.age > p.maxAge || p.x < 0 || p.x >= nx || p.y < 0 || p.y >= ny) {
        p.x = Math.random() * nx;
        p.y = Math.random() * ny;
        p.age = 0;
      }
    }

    animFrameId = requestAnimationFrame(render);
  }
}

function handleMouseMove(e: MouseEvent) {
  const canvas = canvasRef.value;
  if (!canvas || !props.data || !props.data.speed) return;
  const rect = canvas.getBoundingClientRect();
  const mouseX = e.clientX - rect.left;
  const mouseY = e.clientY - rect.top;

  const nx = props.data.speed.length;
  const ny = props.data.speed[0].length;

  const gridX = Math.floor((mouseX / canvas.width) * nx);
  const gridY = Math.floor(((canvas.height - mouseY) / canvas.height) * ny);

  if (gridX >= 0 && gridX < nx && gridY >= 0 && gridY < ny) {
    hoverInfo.value = {
      x: mouseX + 15,
      y: mouseY + 15,
      gridX,
      gridY,
      u: props.data.u[gridX][gridY],
      v: props.data.v[gridX][gridY],
      speed: props.data.speed[gridX][gridY],
      p: props.data.p[gridX][gridY]
    };
  } else {
    hoverInfo.value = null;
  }
}

function resizeCanvas() {
  const container = containerRef.value;
  const canvas = canvasRef.value;
  if (!container || !canvas) return;

  const size = Math.min(container.clientWidth - 20, container.clientHeight - 20, 640);
  canvas.width = size;
  canvas.height = size;

  if (props.data) {
    if (animFrameId) cancelAnimationFrame(animFrameId);
    render();
  }
}

watch(() => [props.data, props.vizMode, props.colormap], () => {
  if (animFrameId) cancelAnimationFrame(animFrameId);
  render();
}, { deep: true });

onMounted(() => {
  resizeCanvas();
  window.addEventListener('resize', resizeCanvas);
});

onUnmounted(() => {
  if (animFrameId) cancelAnimationFrame(animFrameId);
  window.removeEventListener('resize', resizeCanvas);
});
</script>

<style scoped>
.canvas-2d-container {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.cfd-canvas-2d {
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
  cursor: crosshair;
  background: #000;
}

.grid-tooltip {
  position: absolute;
  pointer-events: none;
  background: rgba(15, 23, 42, 0.95);
  color: #00d2ff;
  border: 1px solid rgba(0, 210, 255, 0.3);
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 11px;
  font-family: monospace;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
  z-index: 10;
}
</style>
