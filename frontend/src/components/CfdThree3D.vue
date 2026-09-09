<template>
  <div class="three-viewport-container">
    <!-- Viewport Top Header: Two Distinct Structured Lines (Status Row & Tools Ribbon) -->
    <div class="viewport-header-strip">
      <!-- Line 1: Title, Simulation Archetype, and Aerodynamic Telemetry -->
      <div class="header-status-line">
        <div class="status-left">
          <span class="viewport-title">OpenZess 3D Studio</span>
          <span class="archetype-badge">{{ archetypeBadgeTitle }}</span>
          <span class="live-tag" :class="{ 'live-active': isReceivingLive }">
            <span class="pulse-dot"></span> {{ isReceivingLive ? 'SOLVER STREAMING' : 'IDLE' }}
          </span>
        </div>
        <div class="status-right">
          <span class="telemetry-pill">Co_max: {{ telemetry.courantMax ? telemetry.courantMax.toFixed(2) : '0.00' }}</span>
          <span class="telemetry-pill forces">Cd: {{ telemetry.cd ? telemetry.cd.toFixed(3) : '0.000' }}</span>
          <span class="telemetry-pill forces">Cl: {{ telemetry.cl ? telemetry.cl.toFixed(3) : '0.000' }}</span>
        </div>
      </div>

      <!-- Line 2: Organized Toolbar Strip (Field, Colormap, Visualization & Camera Toggles) -->
      <div class="header-tools-line">
        <!-- Field & Colormap selectors -->
        <div class="tools-left">
          <div class="field-select-wrapper">
            <label for="field-var-select">Field:</label>
            <select
              id="field-var-select"
              :value="activeField"
              @change="onFieldChange(($event.target as HTMLSelectElement).value as FieldVariable)"
              class="field-dropdown"
            >
              <option value="U">🌀 Velocity |U| [m/s]</option>
              <option value="p">🔴 Pressure (p) [Pa]</option>
              <option value="omega">🌪️ Vorticity (ω) [1/s]</option>
              <option value="T">🌡️ Temperature (T) [K]</option>
            </select>
          </div>

          <div class="colormap-select-wrapper">
            <label for="colormap-select">Palette:</label>
            <select
              id="colormap-select"
              :value="activeColormap"
              @change="onColormapChange(($event.target as HTMLSelectElement).value as ColormapScheme)"
              class="colormap-dropdown"
            >
              <option value="coolwarm">❄️ Coolwarm</option>
              <option value="turbo">🌈 Turbo</option>
              <option value="jet">🌊 Jet</option>
              <option value="viridis">🌌 Viridis</option>
              <option value="inferno">🔥 Inferno</option>
            </select>
          </div>
        </div>

        <!-- Action Toggles -->
        <div class="tools-right">
          <div class="tool-btn-group">
            <button
              class="hud-tool-btn"
              :class="{ active: isSliceRakeOpen }"
              @click="isSliceRakeOpen = !isSliceRakeOpen"
              title="Open Interactive Slice Plane Position & Streamline Rake Sliders"
            >
              🎛️ Slice & Rake
            </button>

            <button
              class="hud-tool-btn"
              :class="{ active: showStreamlines }"
              @click="showStreamlines = !showStreamlines"
              title="Toggle Continuous 3D Fluid Ribbon Streamlines"
            >
              🌊 Ribbons
            </button>

            <button
              class="hud-tool-btn"
              :class="{ active: showGeometry }"
              @click="showGeometry = !showGeometry"
              title="Toggle 3D Physical Obstacle Surface"
            >
              🧱 3D Body
            </button>

            <button
              class="hud-tool-btn"
              :class="{ active: showCutplanes }"
              @click="showCutplanes = !showCutplanes"
              title="Toggle Bilinear DataTexture Slice Plane"
            >
              📐 Slice Plane
            </button>

            <button
              class="hud-tool-btn"
              :class="{ active: showGlyphs }"
              @click="showGlyphs = !showGlyphs"
              title="Toggle 3D Velocity Vector Cones"
            >
              🏹 Glyphs
            </button>

            <button
              class="hud-tool-btn"
              :class="{ active: showFloorGrid }"
              @click="showFloorGrid = !showFloorGrid"
              title="Toggle Ground Grid & Contact Shadow"
            >
              🏁 Grid
            </button>
          </div>

          <div class="tool-btn-group">
            <button
              class="hud-tool-btn"
              :class="{ active: isAutoRotate }"
              @click="isAutoRotate = !isAutoRotate"
              title="Toggle 3D Orbit Auto-Rotation"
            >
              🔄 Orbit
            </button>

            <button
              class="hud-tool-btn"
              @click="resetCamera"
              title="Reset 3D Camera to Standard Engineering Isometric View"
            >
              🎯 Reset
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Interactive Slice Plane & Streamline Rake Floating HUD Panel -->
    <transition name="hud-fade">
      <div v-if="isSliceRakeOpen" class="interactive-controls-hud">
        <div class="hud-panel-header">
          <span class="hud-panel-title">🎛️ Interactive CFD Probes & Manipulators</span>
          <button class="hud-close-btn" @click="isSliceRakeOpen = false" title="Close Panel">✕</button>
        </div>

        <!-- Section 1: Interactive Slice Plane -->
        <div class="hud-section">
          <div class="hud-section-title">
            <span>📐 Slice Plane Position & Axis</span>
            <span class="hud-param-badge">{{ sliceAxis.toUpperCase() }} = {{ slicePos.toFixed(2) }} m</span>
          </div>

          <!-- Axis Selector Pills -->
          <div class="axis-pill-group">
            <button
              class="axis-pill-btn"
              :class="{ active: sliceAxis === 'z' }"
              @click="setSliceAxis('z')"
            >
              XY (Spanwise Z)
            </button>
            <button
              class="axis-pill-btn"
              :class="{ active: sliceAxis === 'y' }"
              @click="setSliceAxis('y')"
            >
              XZ (Vertical Y)
            </button>
            <button
              class="axis-pill-btn"
              :class="{ active: sliceAxis === 'x' }"
              @click="setSliceAxis('x')"
            >
              YZ (Wake Cross X)
            </button>
          </div>

          <!-- Position Slider -->
          <div class="slider-control-row">
            <label class="slider-label">Position:</label>
            <input
              type="range"
              :min="sliceMin"
              :max="sliceMax"
              step="0.02"
              v-model.number="slicePos"
              @input="onSlicePosChange"
              class="hud-slider"
            />
            <span class="slider-val">{{ slicePos.toFixed(2) }}</span>
          </div>

          <!-- Opacity Slider -->
          <div class="slider-control-row">
            <label class="slider-label">Opacity:</label>
            <input
              type="range"
              min="0.2"
              max="1.0"
              step="0.05"
              v-model.number="sliceOpacity"
              @input="onSliceOpacityChange"
              class="hud-slider"
            />
            <span class="slider-val">{{ Math.round(sliceOpacity * 100) }}%</span>
          </div>
        </div>

        <!-- Section 2: Draggable Streamline Rake -->
        <div class="hud-section">
          <div class="hud-section-title">
            <span>🌊 Streamline Emitter Rake</span>
            <span class="hud-param-badge">Pos: ({{ rakeX.toFixed(2) }}, {{ rakeY.toFixed(2) }})</span>
          </div>

          <!-- Rake Presets -->
          <div class="preset-pill-group">
            <button class="preset-pill-btn" @click="applyRakePreset('inlet')">
              Inlet
            </button>
            <button class="preset-pill-btn" @click="applyRakePreset('nose')">
              🎯 Stagnation Nose
            </button>
            <button class="preset-pill-btn" @click="applyRakePreset('boundary')">
              📐 Boundary Layer
            </button>
            <button class="preset-pill-btn" @click="applyRakePreset('wake')">
              🌪️ Recirculation Wake
            </button>
          </div>

          <!-- Rake X Slider -->
          <div class="slider-control-row">
            <label class="slider-label">Rake X:</label>
            <input
              type="range"
              min="-1.95"
              max="1.2"
              step="0.05"
              v-model.number="rakeX"
              @input="onRakeChange"
              class="hud-slider"
            />
            <span class="slider-val">{{ rakeX.toFixed(2) }}</span>
          </div>

          <!-- Rake Y Slider -->
          <div class="slider-control-row">
            <label class="slider-label">Rake Y:</label>
            <input
              type="range"
              min="-0.85"
              max="0.85"
              step="0.05"
              v-model.number="rakeY"
              @input="onRakeChange"
              class="hud-slider"
            />
            <span class="slider-val">{{ rakeY.toFixed(2) }}</span>
          </div>

          <!-- Rake Span / Spread Slider -->
          <div class="slider-control-row">
            <label class="slider-label">Spread:</label>
            <input
              type="range"
              min="0.15"
              max="1.8"
              step="0.05"
              v-model.number="rakeSpan"
              @input="onRakeChange"
              class="hud-slider"
            />
            <span class="slider-val">{{ rakeSpan.toFixed(2) }} m</span>
          </div>
        </div>
      </div>
    </transition>

    <!-- Scientific Colorbar Legend (HUD Overlay) -->
    <div v-if="showColorbar" class="scientific-colorbar-dock">
      <div class="colorbar-card">
        <div class="colorbar-header">
          <span class="colorbar-title">{{ colorbarData.title }}</span>
          <span class="colorbar-unit">{{ colorbarData.unit }}</span>
        </div>

        <div class="colorbar-gradient-track">
          <div
            class="colorbar-gradient-fill"
            :style="{ background: colorbarGradientStyle }"
          ></div>
        </div>

        <div class="colorbar-ticks">
          <span class="tick max">{{ colorbarData.maxVal }}</span>
          <span class="tick mid">{{ colorbarData.midVal }}</span>
          <span class="tick min">{{ colorbarData.minVal }}</span>
        </div>
      </div>
    </div>

    <!-- Engineering Coordinate Triad Overlay (Bottom Left) -->
    <div class="engineering-triad-dock">
      <canvas ref="triadCanvasRef" width="100" height="100" class="triad-canvas"></canvas>
      <div class="triad-labels">
        <span class="axis-badge x">X: Streamwise</span>
        <span class="axis-badge y">Y: Normal/Lift</span>
        <span class="axis-badge z">Z: Spanwise</span>
      </div>
    </div>

    <!-- WebGL Canvas Mount Node -->
    <div ref="canvasMountRef" class="webgl-canvas-mount"></div>

    <!-- Hover Flow Probe HUD Overlay -->
    <div
      v-if="probe.active"
      class="hover-flow-probe-hud"
      :style="{ left: probe.screenX + 'px', top: probe.screenY + 'px' }"
    >
      <div class="probe-hud-card">
        <div class="probe-val-row">
          <span class="probe-val-title">{{ probe.label }}</span>
          <span class="probe-val-num">{{ probe.value.toFixed(3) }} {{ probe.unit }}</span>
        </div>
        <div class="probe-hud-tag">
          <span>{{ probe.subtext }}</span>
        </div>
      </div>
      <div class="probe-pointer-line"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import * as THREE from 'three';
import type { SimulationStepData, SimulationParams, FieldVariable, ColormapScheme, AerodynamicTelemetry } from '../types/cfd';

const props = defineProps<{
  data: SimulationStepData | null;
  params: SimulationParams;
  telemetry: AerodynamicTelemetry;
}>();

const emit = defineEmits<{
  (e: 'update:activeField', field: FieldVariable): void;
}>();

const canvasMountRef = ref<HTMLDivElement | null>(null);
const triadCanvasRef = ref<HTMLCanvasElement | null>(null);

const activeField = ref<FieldVariable>(props.params.activeField || 'U');
const activeColormap = ref<ColormapScheme>('coolwarm');

const showGeometry = ref(true);
const showCutplanes = ref(true);
const showStreamlines = ref(true);
const showGlyphs = ref(false);
const showFloorGrid = ref(true);
const showColorbar = ref(true);
const isAutoRotate = ref(false);

// Interactive Slice & Rake Panel State
const isSliceRakeOpen = ref(true); // Open by default for immediate discovery
const sliceAxis = ref<'x' | 'y' | 'z'>('z');
const slicePos = ref(0.0);
const sliceOpacity = ref(0.88);

// Draggable Streamline Rake State
const rakeX = ref(-1.95);
const rakeY = ref(0.0);
const rakeSpan = ref(1.72);

const sliceMin = computed(() => {
  if (sliceAxis.value === 'x') return -1.9;
  if (sliceAxis.value === 'y') return -0.9;
  return -0.55;
});

const sliceMax = computed(() => {
  if (sliceAxis.value === 'x') return 1.9;
  if (sliceAxis.value === 'y') return 0.9;
  return 0.55;
});

const isReceivingLive = computed(() => {
  return !!props.data && props.data.iteration > 0;
});

// Flow Probe Tooltip State
const probe = ref({
  active: false,
  screenX: 0,
  screenY: 0,
  value: 0.0,
  unit: 'm/s',
  label: 'Velocity |U|',
  subtext: 'OpenFOAM Point Probe HUD'
});

let scene: THREE.Scene;
let camera: THREE.PerspectiveCamera;
let renderer: THREE.WebGLRenderer;
let animId: number;

// Triad Scene & Renderer
let triadScene: THREE.Scene;
let triadCamera: THREE.PerspectiveCamera;
let triadRenderer: THREE.WebGLRenderer;
let triadGroup: THREE.Group;

let mainGroup: THREE.Group;
let geometryGroup: THREE.Group;
let ribbonStreamlinesGroup: THREE.Group;
let cutplanesGroup: THREE.Group;
let glyphsGroup: THREE.Group;
let floorGroup: THREE.Group;
let pulsesGroup: THREE.Group;
let rakeBarGroup: THREE.Group;

let cutplaneMesh: THREE.Mesh | null = null;
let dataTexture: THREE.DataTexture | null = null;
let textureBuffer: Uint8Array | null = null;
let textureWidth = 80;
let textureHeight = 40;

let probeMarker: THREE.Mesh;
let obstacleMesh: THREE.Mesh | null = null;
let rakeBarMesh: THREE.Mesh | null = null;

// Ribbon Streamlines Data (Genuine 3D Quads with Width & Lighting)
const NUM_STREAMLINES = 36;
const STREAMLINE_STEPS = 52;
const RIBBON_WIDTH = 0.024;

interface RibbonStreamline {
  seed: THREE.Vector3;
  mesh: THREE.Mesh;
  geom: THREE.BufferGeometry;
  positions: Float32Array; // Centerline points
  meshPositions: Float32Array; // Ribbon quads (2 * STEPS * 3)
  meshColors: Float32Array;    // Ribbon vertex colors
  pulsePos: number;            // 0..1
}
let ribbonStreamlines: RibbonStreamline[] = [];

let pulsePoints: THREE.Points | null = null;
let pulsePositions: Float32Array;
let pulseColors: Float32Array;

// Mouse drag & raycast state
let isDragging = false;
let previousMousePosition = { x: 0, y: 0 };
let targetRotationX = 0.32;
let targetRotationY = -0.68;
let raycaster = new THREE.Raycaster();
let mouse = new THREE.Vector2();

// Domain bounds in Three.js world space
const DOMAIN = {
  minX: -2.0,
  maxX: 2.0,
  minY: -1.0,
  maxY: 1.0,
  minZ: -0.6,
  maxZ: 0.6
};

const archetypeBadgeTitle = computed(() => {
  switch (props.params.archetype) {
    case 'airfoil': return '✈️ NACA 0012 Wing Aerodynamics';
    case 'cylinder': return '🔴 Von Kármán Vortex Shedding (Re=' + (props.params.reynoldsNumber || 100) + ')';
    case 'cavity': return '🌀 Lid-Driven Cavity (Ghia Benchmark)';
    case 'venturi': return '🚿 Venturi Nozzle Flow';
    case 'cad': return '📤 CAD Wind Tunnel';
    default: return '🌊 Incompressible Navier-Stokes Flow';
  }
});

const colorbarData = computed(() => {
  const f = activeField.value;
  if (f === 'p') {
    return { title: 'Pressure (p)', unit: '[Pa]', maxVal: '+2.00', midVal: '0.00', minVal: '-1.50' };
  } else if (f === 'omega') {
    return { title: 'Vorticity (ω)', unit: '[s⁻¹]', maxVal: '+15.0', midVal: '0.0', minVal: '-15.0' };
  } else if (f === 'T') {
    return { title: 'Temperature (T)', unit: '[K]', maxVal: '350.0', midVal: '320.0', minVal: '293.15' };
  }
  return { title: 'Velocity |U|', unit: '[m/s]', maxVal: '1.800', midVal: '0.900', minVal: '0.000' };
});

const colorbarGradientStyle = computed(() => {
  const s = activeColormap.value;
  if (s === 'coolwarm') return 'linear-gradient(to right, #3b82f6, #f8fafc, #ef4444)';
  if (s === 'viridis') return 'linear-gradient(to right, #440154, #21918c, #fde725)';
  if (s === 'inferno') return 'linear-gradient(to right, #000004, #bb3754, #fcffa4)';
  if (s === 'jet') return 'linear-gradient(to right, #0000ff, #00ffff, #ffff00, #ff0000)';
  return 'linear-gradient(to right, #30123b, #1ae4b6, #a2fc3c, #e83f12, #7a0403)'; // Turbo
});

function onFieldChange(field: FieldVariable) {
  activeField.value = field;
  emit('update:activeField', field);
  updateSliceDataTexture();
  updateObstacleSurfaceColors();
  updateRibbonStreamlinesGeometry();
}

function onColormapChange(cm: ColormapScheme) {
  activeColormap.value = cm;
  updateSliceDataTexture();
  updateObstacleSurfaceColors();
  updateRibbonStreamlinesGeometry();
}

// Slice Plane Controls Handlers
function setSliceAxis(axis: 'x' | 'y' | 'z') {
  sliceAxis.value = axis;
  slicePos.value = 0.0;
  rebuildSlicePlane();
}

function onSlicePosChange() {
  if (!cutplaneMesh) return;
  if (sliceAxis.value === 'z') {
    cutplaneMesh.position.set(0, 0, slicePos.value);
  } else if (sliceAxis.value === 'y') {
    cutplaneMesh.position.set(0, slicePos.value, 0);
  } else if (sliceAxis.value === 'x') {
    cutplaneMesh.position.set(slicePos.value, 0, 0);
  }
  updateSliceDataTexture();
}

function onSliceOpacityChange() {
  if (cutplaneMesh && cutplaneMesh.material) {
    (cutplaneMesh.material as THREE.MeshBasicMaterial).opacity = sliceOpacity.value;
  }
}

// Rake Handlers & Presets
function applyRakePreset(preset: 'inlet' | 'nose' | 'boundary' | 'wake') {
  if (preset === 'inlet') {
    rakeX.value = -1.95;
    rakeY.value = 0.0;
    rakeSpan.value = 1.72;
  } else if (preset === 'nose') {
    rakeX.value = -1.25;
    rakeY.value = 0.0;
    rakeSpan.value = 0.45;
  } else if (preset === 'boundary') {
    rakeX.value = -1.15;
    rakeY.value = 0.42;
    rakeSpan.value = 0.35;
  } else if (preset === 'wake') {
    rakeX.value = -0.35;
    rakeY.value = 0.0;
    rakeSpan.value = 0.70;
  }
  onRakeChange();
}

function onRakeChange() {
  updateRakeSeeds();
  updateRakeBarGeometry();
  updateRibbonStreamlinesGeometry();
}

function updateRakeSeeds() {
  const isCavity = props.params.archetype === 'cavity';
  for (let i = 0; i < ribbonStreamlines.length; i++) {
    const sl = ribbonStreamlines[i];
    if (isCavity) {
      const radius = 0.18 + (i / NUM_STREAMLINES) * 0.92;
      const angle = (i / NUM_STREAMLINES) * Math.PI * 2;
      sl.seed.set(Math.cos(angle) * radius, Math.sin(angle) * radius, ((i % 2) - 0.5) * 0.25);
    } else {
      const yOffset = -rakeSpan.value * 0.5 + (i / (NUM_STREAMLINES - 1)) * rakeSpan.value;
      const seedY = rakeY.value + yOffset;
      const seedZ = ((i % 3) - 1) * 0.28;
      sl.seed.set(rakeX.value, seedY, seedZ);
    }
  }
}

// =========================================================================
// REAL FLUID FIELD SAMPLING (Navier-Stokes Solution Bilinear Interpolator)
// =========================================================================
function sampleFluidField(x: number, y: number): { u: number; v: number; p: number; speed: number; omega: number } {
  const data = props.data;
  const isCavity = props.params.archetype === 'cavity';

  if (data && data.u && data.u.length > 0 && data.u[0].length > 0) {
    const uArr = data.u;
    const vArr = data.v;
    const pArr = data.p;
    const nx = uArr.length;
    const ny = uArr[0].length;

    let dMinX = isCavity ? -1.2 : DOMAIN.minX;
    let dMaxX = isCavity ? 1.2 : DOMAIN.maxX;
    let dMinY = isCavity ? -1.2 : DOMAIN.minY;
    let dMaxY = isCavity ? 1.2 : DOMAIN.maxY;

    let gx = ((x - dMinX) / (dMaxX - dMinX)) * (nx - 1);
    let gy = ((y - dMinY) / (dMaxY - dMinY)) * (ny - 1);

    gx = Math.max(0, Math.min(nx - 1.001, gx));
    gy = Math.max(0, Math.min(ny - 1.001, gy));

    const i0 = Math.floor(gx);
    const i1 = Math.min(nx - 1, i0 + 1);
    const j0 = Math.floor(gy);
    const j1 = Math.min(ny - 1, j0 + 1);

    const fx = gx - i0;
    const fy = gy - j0;

    const u00 = uArr[i0][j0], u10 = uArr[i1][j0];
    const u01 = uArr[i0][j1], u11 = uArr[i1][j1];
    const u = (1 - fx) * (1 - fy) * u00 + fx * (1 - fy) * u10 + (1 - fx) * fy * u01 + fx * fy * u11;

    const v00 = vArr[i0][j0], v10 = vArr[i1][j0];
    const v01 = vArr[i0][j1], v11 = vArr[i1][j1];
    const v = (1 - fx) * (1 - fy) * v00 + fx * (1 - fy) * v10 + (1 - fx) * fy * v01 + fx * fy * v11;

    const p00 = pArr[i0][j0], p10 = pArr[i1][j0];
    const p01 = pArr[i0][j1], p11 = pArr[i1][j1];
    const p = (1 - fx) * (1 - fy) * p00 + fx * (1 - fy) * p10 + (1 - fx) * fy * p01 + fx * fy * p11;

    const dv_dx = (vArr[Math.min(nx - 1, i0 + 1)][j0] - vArr[Math.max(0, i0 - 1)][j0]) / (2 * (dMaxX - dMinX) / nx);
    const du_dy = (uArr[i0][Math.min(ny - 1, j0 + 1)] - uArr[i0][Math.max(0, j0 - 1)]) / (2 * (dMaxY - dMinY) / ny);
    const omega = dv_dx - du_dy;

    return { u, v, p, speed: Math.sqrt(u * u + v * v), omega };
  }

  // Initial clean physical baseline before simulation starts
  if (isCavity) {
    const r = Math.sqrt(x * x + y * y);
    const u = -y * Math.max(0, 1 - r);
    const v = x * Math.max(0, 1 - r);
    return { u, v, p: 0.0, speed: Math.sqrt(u * u + v * v), omega: 2.0 };
  }

  const cx = -0.8;
  const cy = 0.0;
  const rad = 0.35;
  const dx = x - cx;
  const dy = y - cy;
  const r2 = dx * dx + dy * dy;
  const U_inf = 1.0;

  if (r2 < rad * rad) {
    return { u: 0.0, v: 0.0, p: 1.0, speed: 0.0, omega: 0.0 };
  }

  const u = U_inf * (1 - (rad * rad * (dx * dx - dy * dy)) / (r2 * r2));
  const v = -U_inf * (rad * rad * (2 * dx * dy)) / (r2 * r2);
  const speed = Math.sqrt(u * u + v * v);
  const p = 0.5 * (1.0 - speed * speed);
  return { u, v, p, speed, omega: 0.0 };
}

// Colormap mapping function
function getColormapRgb(normalizedVal: number, scheme: ColormapScheme): [number, number, number] {
  const v = Math.max(0, Math.min(1, normalizedVal));
  if (scheme === 'coolwarm') {
    return [v, 0.2 + 0.3 * (1 - Math.abs(v - 0.5)), 1 - v];
  } else if (scheme === 'inferno') {
    return [Math.pow(v, 0.7), Math.pow(v, 2.0), Math.pow(v, 4.0)];
  } else if (scheme === 'viridis') {
    return [0.267 + v * 0.6, 0.004 + v * 0.8, 0.329 + (1 - v) * 0.4];
  } else if (scheme === 'jet') {
    let r = 0, g = 0, b = 0;
    if (v < 0.25) { b = 1; g = 4 * v; }
    else if (v < 0.5) { b = 1 - 4 * (v - 0.25); g = 1; }
    else if (v < 0.75) { g = 1; r = 4 * (v - 0.5); }
    else { r = 1; g = 1 - 4 * (v - 0.75); }
    return [r, g, b];
  }
  // Turbo palette
  let r = 0, g = 0, b = 0;
  if (v < 0.125) b = 0.5 + 4 * v;
  else if (v < 0.375) { b = 1; g = 4 * (v - 0.125); }
  else if (v < 0.625) { b = 1 - 4 * (v - 0.375); g = 1; r = 4 * (v - 0.375); }
  else if (v < 0.875) { g = 1 - 4 * (v - 0.625); r = 1; }
  else { r = 1 - 2 * (v - 0.875); }
  return [r, g, b];
}

function initThree() {
  if (!canvasMountRef.value) return;

  const width = canvasMountRef.value.clientWidth || 800;
  const height = canvasMountRef.value.clientHeight || 600;

  // Scene
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0c0810);

  // Camera
  camera = new THREE.PerspectiveCamera(38, width / height, 0.1, 1000);
  camera.position.set(3.6, -4.0, 3.0);
  camera.lookAt(0, 0, 0);

  // Renderer
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;

  canvasMountRef.value.innerHTML = '';
  canvasMountRef.value.appendChild(renderer.domElement);

  // Professional Studio Lighting
  const ambient = new THREE.AmbientLight(0xffffff, 0.82);
  scene.add(ambient);

  const keyLight = new THREE.DirectionalLight(0x00d2ff, 1.4);
  keyLight.position.set(6, 6, 8);
  keyLight.castShadow = true;
  scene.add(keyLight);

  const rimLight = new THREE.DirectionalLight(0xa855f7, 1.1);
  rimLight.position.set(-6, -6, 5);
  scene.add(rimLight);

  const fillLight = new THREE.DirectionalLight(0xffffff, 0.5);
  fillLight.position.set(0, 8, 2);
  scene.add(fillLight);

  // Root Groups
  mainGroup = new THREE.Group();
  geometryGroup = new THREE.Group();
  ribbonStreamlinesGroup = new THREE.Group();
  cutplanesGroup = new THREE.Group();
  glyphsGroup = new THREE.Group();
  floorGroup = new THREE.Group();
  pulsesGroup = new THREE.Group();
  rakeBarGroup = new THREE.Group();

  mainGroup.add(geometryGroup);
  mainGroup.add(ribbonStreamlinesGroup);
  mainGroup.add(cutplanesGroup);
  mainGroup.add(glyphsGroup);
  mainGroup.add(floorGroup);
  mainGroup.add(pulsesGroup);
  mainGroup.add(rakeBarGroup);
  scene.add(mainGroup);

  // Build Scene Components
  buildActiveArchetype();
  rebuildSlicePlane();
  buildRibbonStreamlines();
  buildVectorGlyphs();
  buildGroundGridAndShadow();
  buildDomainBoundingBox();
  buildRakeBarMesh();
  buildProbeMarker();

  // Initialize Engineering Triad HUD
  initEngineeringTriad();

  // Listeners
  const dom = renderer.domElement;
  dom.addEventListener('mousedown', onMouseDown);
  dom.addEventListener('mousemove', onMouseMove);
  window.addEventListener('mouseup', onMouseUp);
  dom.addEventListener('wheel', onWheel, { passive: true });

  animate();
}

function clearGroup(g: THREE.Group) {
  while (g.children.length > 0) {
    const child = g.children[0] as any;
    g.remove(child);
    if (child.geometry) child.geometry.dispose();
    if (child.material) {
      if (Array.isArray(child.material)) child.material.forEach((m: any) => m.dispose());
      else child.material.dispose();
    }
  }
}

// =========================================================================
// 1. CONTINUOUS 3D FLUID RIBBON STREAMLINES (THREE.BufferGeometry Quads)
// =========================================================================
function buildRibbonStreamlines() {
  clearGroup(ribbonStreamlinesGroup);
  clearGroup(pulsesGroup);
  ribbonStreamlines = [];

  for (let i = 0; i < NUM_STREAMLINES; i++) {
    const yOffset = -rakeSpan.value * 0.5 + (i / (NUM_STREAMLINES - 1)) * rakeSpan.value;
    const seedY = rakeY.value + yOffset;
    const seedZ = ((i % 3) - 1) * 0.28;

    const positions = new Float32Array(STREAMLINE_STEPS * 3);
    const numVerts = STREAMLINE_STEPS * 2;
    const meshPositions = new Float32Array(numVerts * 3);
    const meshColors = new Float32Array(numVerts * 3);

    const indices: number[] = [];
    for (let s = 0; s < STREAMLINE_STEPS - 1; s++) {
      const i0 = s * 2;
      const i1 = s * 2 + 1;
      const i2 = (s + 1) * 2;
      const i3 = (s + 1) * 2 + 1;
      indices.push(i0, i1, i2);
      indices.push(i1, i3, i2);
    }

    const geom = new THREE.BufferGeometry();
    geom.setIndex(indices);
    geom.setAttribute('position', new THREE.BufferAttribute(meshPositions, 3));
    geom.setAttribute('color', new THREE.BufferAttribute(meshColors, 3));

    const mat = new THREE.MeshStandardMaterial({
      vertexColors: true,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.85,
      metalness: 0.35,
      roughness: 0.3
    });

    const mesh = new THREE.Mesh(geom, mat);
    ribbonStreamlinesGroup.add(mesh);

    ribbonStreamlines.push({
      seed: new THREE.Vector3(rakeX.value, seedY, seedZ),
      mesh,
      geom,
      positions,
      meshPositions,
      meshColors,
      pulsePos: (i / NUM_STREAMLINES)
    });
  }

  pulsePositions = new Float32Array(NUM_STREAMLINES * 3);
  pulseColors = new Float32Array(NUM_STREAMLINES * 3);

  const pulseGeom = new THREE.BufferGeometry();
  pulseGeom.setAttribute('position', new THREE.BufferAttribute(pulsePositions, 3));
  pulseGeom.setAttribute('color', new THREE.BufferAttribute(pulseColors, 3));

  const pulseMat = new THREE.PointsMaterial({
    size: 0.08,
    vertexColors: true,
    transparent: true,
    opacity: 0.95,
    blending: THREE.AdditiveBlending
  });

  pulsePoints = new THREE.Points(pulseGeom, pulseMat);
  pulsesGroup.add(pulsePoints);

  updateRibbonStreamlinesGeometry();
}

function updateRibbonStreamlinesGeometry() {
  const isCavity = props.params.archetype === 'cavity';
  const ds = isCavity ? 0.045 : 0.065;

  for (let sIdx = 0; sIdx < ribbonStreamlines.length; sIdx++) {
    const sl = ribbonStreamlines[sIdx];
    let curX = sl.seed.x;
    let curY = sl.seed.y;
    let curZ = sl.seed.z;

    for (let step = 0; step < STREAMLINE_STEPS; step++) {
      sl.positions[step * 3] = curX;
      sl.positions[step * 3 + 1] = curY;
      sl.positions[step * 3 + 2] = curZ;

      const { u, v } = sampleFluidField(curX, curY);

      const midX = curX + 0.5 * ds * u;
      const midY = curY + 0.5 * ds * v;
      const mid = sampleFluidField(midX, midY);

      curX += ds * mid.u;
      curY += ds * mid.v;

      if (curX > DOMAIN.maxX || curX < DOMAIN.minX || curY > DOMAIN.maxY || curY < DOMAIN.minY) {
        for (let rem = step + 1; rem < STREAMLINE_STEPS; rem++) {
          sl.positions[rem * 3] = curX;
          sl.positions[rem * 3 + 1] = curY;
          sl.positions[rem * 3 + 2] = curZ;
        }
        break;
      }
    }

    for (let step = 0; step < STREAMLINE_STEPS; step++) {
      const px = sl.positions[step * 3];
      const py = sl.positions[step * 3 + 1];
      const pz = sl.positions[step * 3 + 2];

      let tx = 1.0, ty = 0.0;
      if (step < STREAMLINE_STEPS - 1) {
        tx = sl.positions[(step + 1) * 3] - px;
        ty = sl.positions[(step + 1) * 3 + 1] - py;
      } else if (step > 0) {
        tx = px - sl.positions[(step - 1) * 3];
        ty = py - sl.positions[(step - 1) * 3 + 1];
      }
      const tLen = Math.sqrt(tx * tx + ty * ty) || 1.0;
      tx /= tLen;
      ty /= tLen;

      const nx = -ty;
      const ny = tx;

      const { speed, p, omega } = sampleFluidField(px, py);
      const w = RIBBON_WIDTH * (0.8 + 0.4 * Math.min(speed, 1.5));

      const v0Idx = step * 2;
      sl.meshPositions[v0Idx * 3] = px + nx * w;
      sl.meshPositions[v0Idx * 3 + 1] = py + ny * w;
      sl.meshPositions[v0Idx * 3 + 2] = pz;

      const v1Idx = step * 2 + 1;
      sl.meshPositions[v1Idx * 3] = px - nx * w;
      sl.meshPositions[v1Idx * 3 + 1] = py - ny * w;
      sl.meshPositions[v1Idx * 3 + 2] = pz;

      let val = speed / 1.6;
      if (activeField.value === 'p') val = (p + 1.2) / 2.6;
      else if (activeField.value === 'omega') val = (omega + 10.0) / 20.0;

      const [r, g, b] = getColormapRgb(val, activeColormap.value);
      sl.meshColors[v0Idx * 3] = r;
      sl.meshColors[v0Idx * 3 + 1] = g;
      sl.meshColors[v0Idx * 3 + 2] = b;

      sl.meshColors[v1Idx * 3] = r;
      sl.meshColors[v1Idx * 3 + 1] = g;
      sl.meshColors[v1Idx * 3 + 2] = b;
    }

    (sl.geom.attributes.position as THREE.BufferAttribute).needsUpdate = true;
    (sl.geom.attributes.color as THREE.BufferAttribute).needsUpdate = true;
    sl.geom.computeVertexNormals();
  }
}

function updateTracerPulses(dt = 0.015) {
  if (!pulsePoints) return;

  const posAttr = pulsePoints.geometry.attributes.position as THREE.BufferAttribute;
  const colAttr = pulsePoints.geometry.attributes.color as THREE.BufferAttribute;

  for (let i = 0; i < ribbonStreamlines.length; i++) {
    const sl = ribbonStreamlines[i];
    sl.pulsePos += dt * 0.75;
    if (sl.pulsePos > 1.0) sl.pulsePos -= 1.0;

    const stepIdx = Math.floor(sl.pulsePos * (STREAMLINE_STEPS - 1));
    const nextIdx = Math.min(STREAMLINE_STEPS - 1, stepIdx + 1);
    const alpha = sl.pulsePos * (STREAMLINE_STEPS - 1) - stepIdx;

    const px = (1 - alpha) * sl.positions[stepIdx * 3] + alpha * sl.positions[nextIdx * 3];
    const py = (1 - alpha) * sl.positions[stepIdx * 3 + 1] + alpha * sl.positions[nextIdx * 3 + 1];
    const pz = (1 - alpha) * sl.positions[stepIdx * 3 + 2] + alpha * sl.positions[nextIdx * 3 + 2];

    pulsePositions[i * 3] = px;
    pulsePositions[i * 3 + 1] = py;
    pulsePositions[i * 3 + 2] = pz;

    pulseColors[i * 3] = 1.0;
    pulseColors[i * 3 + 1] = 1.0;
    pulseColors[i * 3 + 2] = 1.0;
  }

  posAttr.needsUpdate = true;
  colAttr.needsUpdate = true;
}

// =========================================================================
// 2. HARDWARE BILINEAR DataTexture MULTI-AXIS SLICE PLANE
// =========================================================================
function rebuildSlicePlane() {
  clearGroup(cutplanesGroup);

  textureWidth = 80;
  textureHeight = 40;
  textureBuffer = new Uint8Array(textureWidth * textureHeight * 4);

  dataTexture = new THREE.DataTexture(
    textureBuffer,
    textureWidth,
    textureHeight,
    THREE.RGBAFormat,
    THREE.UnsignedByteType
  );
  dataTexture.magFilter = THREE.LinearFilter;
  dataTexture.minFilter = THREE.LinearFilter;
  dataTexture.generateMipmaps = false;

  let planeGeom: THREE.PlaneGeometry;

  if (sliceAxis.value === 'z') {
    // XY plane (Spanwise)
    planeGeom = new THREE.PlaneGeometry(3.9, 1.95);
  } else if (sliceAxis.value === 'y') {
    // XZ plane (Horizontal)
    planeGeom = new THREE.PlaneGeometry(3.9, 1.15);
  } else {
    // YZ plane (Cross-flow wake)
    planeGeom = new THREE.PlaneGeometry(1.95, 1.15);
  }

  const planeMat = new THREE.MeshBasicMaterial({
    map: dataTexture,
    side: THREE.DoubleSide,
    transparent: true,
    opacity: sliceOpacity.value
  });

  cutplaneMesh = new THREE.Mesh(planeGeom, planeMat);

  if (sliceAxis.value === 'z') {
    cutplaneMesh.rotation.set(0, 0, 0);
    cutplaneMesh.position.set(0, 0, slicePos.value);
  } else if (sliceAxis.value === 'y') {
    cutplaneMesh.rotation.set(-Math.PI / 2, 0, 0);
    cutplaneMesh.position.set(0, slicePos.value, 0);
  } else {
    cutplaneMesh.rotation.set(0, Math.PI / 2, 0);
    cutplaneMesh.position.set(slicePos.value, 0, 0);
  }

  cutplanesGroup.add(cutplaneMesh);
  updateSliceDataTexture();
}

function updateSliceDataTexture() {
  if (!dataTexture || !textureBuffer) return;

  for (let j = 0; j < textureHeight; j++) {
    for (let i = 0; i < textureWidth; i++) {
      const uCoord = i / (textureWidth - 1);
      const vCoord = j / (textureHeight - 1);

      let worldX = 0, worldY = 0;

      if (sliceAxis.value === 'z') {
        worldX = DOMAIN.minX + uCoord * (DOMAIN.maxX - DOMAIN.minX);
        worldY = DOMAIN.minY + vCoord * (DOMAIN.maxY - DOMAIN.minY);
      } else if (sliceAxis.value === 'y') {
        worldX = DOMAIN.minX + uCoord * (DOMAIN.maxX - DOMAIN.minX);
        worldY = slicePos.value;
      } else {
        // YZ wake slice: uCoord is Y, vCoord is Z
        worldX = slicePos.value;
        worldY = DOMAIN.minY + uCoord * (DOMAIN.maxY - DOMAIN.minY);
      }

      const { speed, p, omega } = sampleFluidField(worldX, worldY);

      let val = speed / 1.6;
      if (activeField.value === 'p') val = (p + 1.2) / 2.6;
      else if (activeField.value === 'omega') val = (omega + 10.0) / 20.0;

      const [r, g, b] = getColormapRgb(val, activeColormap.value);
      const idx = (j * textureWidth + i) * 4;

      textureBuffer[idx + 0] = Math.floor(r * 255);
      textureBuffer[idx + 1] = Math.floor(g * 255);
      textureBuffer[idx + 2] = Math.floor(b * 255);
      textureBuffer[idx + 3] = 230;
    }
  }

  dataTexture.needsUpdate = true;
}

// Physical Streamline Rake Emitter Bar
function buildRakeBarMesh() {
  clearGroup(rakeBarGroup);

  const barGeom = new THREE.CylinderGeometry(0.015, 0.015, rakeSpan.value, 16);
  const barMat = new THREE.MeshStandardMaterial({
    color: 0x38bdf8,
    metalness: 0.8,
    roughness: 0.2,
    emissive: 0x075985
  });

  rakeBarMesh = new THREE.Mesh(barGeom, barMat);
  rakeBarMesh.position.set(rakeX.value, rakeY.value, 0);
  rakeBarGroup.add(rakeBarMesh);
}

function updateRakeBarGeometry() {
  if (!rakeBarMesh) return;
  rakeBarMesh.position.set(rakeX.value, rakeY.value, 0);
  rakeBarMesh.scale.set(1, rakeSpan.value / 1.72, 1);
}

// 3D Physical Obstacle Surface
function buildActiveArchetype() {
  clearGroup(geometryGroup);
  obstacleMesh = null;

  const arch = props.params.archetype || 'cylinder';

  if (arch === 'cylinder') {
    const cylGeom = new THREE.CylinderGeometry(0.35, 0.35, 1.4, 64, 24);
    cylGeom.rotateX(Math.PI / 2);

    const cylMat = new THREE.MeshStandardMaterial({
      vertexColors: true,
      metalness: 0.25,
      roughness: 0.22,
      side: THREE.DoubleSide
    });

    obstacleMesh = new THREE.Mesh(cylGeom, cylMat);
    obstacleMesh.position.set(-0.8, 0, 0);
    obstacleMesh.castShadow = true;
    geometryGroup.add(obstacleMesh);
    updateObstacleSurfaceColors();

  } else if (arch === 'airfoil') {
    const shape = new THREE.Shape();
    const chord = 2.0;
    const nPts = 60;
    const pts: THREE.Vector2[] = [];

    for (let i = 0; i <= nPts; i++) {
      const xc = i / nPts;
      const yt = 0.6 * (0.2969 * Math.sqrt(xc) - 0.1260 * xc - 0.3516 * Math.pow(xc, 2) + 0.2843 * Math.pow(xc, 3) - 0.1015 * Math.pow(xc, 4));
      pts.push(new THREE.Vector2((xc - 0.4) * chord, yt));
    }
    for (let i = nPts; i >= 0; i--) {
      const xc = i / nPts;
      const yt = 0.6 * (0.2969 * Math.sqrt(xc) - 0.1260 * xc - 0.3516 * Math.pow(xc, 2) + 0.2843 * Math.pow(xc, 3) - 0.1015 * Math.pow(xc, 4));
      pts.push(new THREE.Vector2((xc - 0.4) * chord, -yt));
    }
    shape.setFromPoints(pts);

    const extrudeSettings = { depth: 1.2, bevelEnabled: false };
    const wingGeom = new THREE.ExtrudeGeometry(shape, extrudeSettings);
    wingGeom.center();

    const wingMat = new THREE.MeshStandardMaterial({
      vertexColors: true,
      metalness: 0.35,
      roughness: 0.25,
      side: THREE.DoubleSide
    });

    obstacleMesh = new THREE.Mesh(wingGeom, wingMat);
    obstacleMesh.castShadow = true;
    geometryGroup.add(obstacleMesh);
    updateObstacleSurfaceColors();

  } else if (arch === 'cavity') {
    const boxGeom = new THREE.BoxGeometry(2.4, 2.4, 1.2);
    const boxMat = new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      wireframe: true,
      transparent: true,
      opacity: 0.35
    });
    const boxMesh = new THREE.Mesh(boxGeom, boxMat);
    geometryGroup.add(boxMesh);

    const lidGeom = new THREE.BoxGeometry(2.4, 0.05, 1.2);
    const lidMat = new THREE.MeshStandardMaterial({
      color: 0x10b981,
      metalness: 0.6,
      roughness: 0.2,
      emissive: 0x052e16
    });
    const lidMesh = new THREE.Mesh(lidGeom, lidMat);
    lidMesh.position.set(0, 1.2, 0);
    geometryGroup.add(lidMesh);
  }
}

function updateObstacleSurfaceColors() {
  if (!obstacleMesh || !obstacleMesh.geometry) return;

  const geom = obstacleMesh.geometry;
  const posAttr = geom.attributes.position;
  const count = posAttr.count;

  let colorAttr = geom.attributes.color as THREE.BufferAttribute;
  if (!colorAttr || colorAttr.count !== count) {
    const colors = new Float32Array(count * 3);
    colorAttr = new THREE.BufferAttribute(colors, 3);
    geom.setAttribute('color', colorAttr);
  }

  const pColors = colorAttr.array as Float32Array;

  for (let i = 0; i < count; i++) {
    const localX = posAttr.getX(i);
    const localY = posAttr.getY(i);
    const worldX = localX + obstacleMesh.position.x;
    const worldY = localY + obstacleMesh.position.y;

    const norm = Math.sqrt(localX * localX + localY * localY) || 1.0;
    const sampleX = worldX + (localX / norm) * 0.08;
    const sampleY = worldY + (localY / norm) * 0.08;

    const { p, speed } = sampleFluidField(sampleX, sampleY);

    let val = 0.5;
    if (activeField.value === 'p') {
      val = (p + 1.2) / 2.6;
    } else {
      val = speed / 1.6;
    }

    const [r, g, b] = getColormapRgb(val, activeColormap.value);
    pColors[i * 3] = r;
    pColors[i * 3 + 1] = g;
    pColors[i * 3 + 2] = b;
  }

  colorAttr.needsUpdate = true;
}

// Ground Grid and Contact Shadow
function buildGroundGridAndShadow() {
  clearGroup(floorGroup);

  const grid = new THREE.GridHelper(5.2, 26, 0x00d2ff, 0x1e293b);
  grid.position.set(0, -1.25, 0);
  grid.material.transparent = true;
  grid.material.opacity = 0.45;
  floorGroup.add(grid);

  const shadowCanvas = document.createElement('canvas');
  shadowCanvas.width = 128;
  shadowCanvas.height = 128;
  const ctx = shadowCanvas.getContext('2d');
  if (ctx) {
    const grad = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
    grad.addColorStop(0, 'rgba(0, 0, 0, 0.65)');
    grad.addColorStop(0.5, 'rgba(0, 0, 0, 0.25)');
    grad.addColorStop(1, 'rgba(0, 0, 0, 0)');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 128, 128);
  }

  const shadowTex = new THREE.CanvasTexture(shadowCanvas);
  const shadowMat = new THREE.MeshBasicMaterial({
    map: shadowTex,
    transparent: true,
    depthWrite: false
  });
  const shadowMesh = new THREE.Mesh(new THREE.PlaneGeometry(1.6, 1.6), shadowMat);
  shadowMesh.position.set(-0.8, -1.24, 0);
  shadowMesh.rotation.x = -Math.PI / 2;
  floorGroup.add(shadowMesh);
}

// Vector Glyphs
function buildVectorGlyphs() {
  clearGroup(glyphsGroup);

  const coneGeom = new THREE.ConeGeometry(0.025, 0.09, 8);
  coneGeom.rotateX(Math.PI / 2);

  const coneMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8 });
  const instMesh = new THREE.InstancedMesh(coneGeom, coneMat, 120);

  const dummy = new THREE.Object3D();
  let count = 0;

  for (let x = -1.8; x <= 1.8; x += 0.4) {
    for (let y = -0.8; y <= 0.8; y += 0.4) {
      if (count >= 120) break;
      const { u, v, speed } = sampleFluidField(x, y);

      dummy.position.set(x, y, 0.02);
      dummy.scale.set(Math.max(0.1, speed * 0.7), Math.max(0.1, speed * 0.7), Math.max(0.1, speed * 0.7));

      if (speed > 0.001) {
        dummy.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), new THREE.Vector3(u, v, 0).normalize());
      }
      dummy.updateMatrix();

      instMesh.setMatrixAt(count, dummy.matrix);
      count++;
    }
  }

  instMesh.instanceMatrix.needsUpdate = true;
  glyphsGroup.add(instMesh);
}

// Domain Bounding Box
function buildDomainBoundingBox() {
  const boxGeom = new THREE.BoxGeometry(4.0, 2.0, 1.2);
  const wireGeom = new THREE.WireframeGeometry(boxGeom);
  const wireMat = new THREE.LineBasicMaterial({
    color: 0x475569,
    transparent: true,
    opacity: 0.32
  });
  const tunnelWire = new THREE.LineSegments(wireGeom, wireMat);
  mainGroup.add(tunnelWire);
}

function buildProbeMarker() {
  const markerGeom = new THREE.SphereGeometry(0.04, 16, 16);
  const markerMat = new THREE.MeshBasicMaterial({ color: 0xffffff, wireframe: true });
  probeMarker = new THREE.Mesh(markerGeom, markerMat);
  probeMarker.position.set(0, 0, 0);
  scene.add(probeMarker);
}

// Engineering Triad
function initEngineeringTriad() {
  if (!triadCanvasRef.value) return;

  triadScene = new THREE.Scene();
  triadCamera = new THREE.PerspectiveCamera(45, 1, 0.1, 10);
  triadCamera.position.set(0, 0, 2.8);

  triadRenderer = new THREE.WebGLRenderer({
    canvas: triadCanvasRef.value,
    alpha: true,
    antialias: true
  });
  triadRenderer.setSize(100, 100);
  triadRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

  triadGroup = new THREE.Group();

  const dirX = new THREE.Vector3(1, 0, 0);
  const arrowX = new THREE.ArrowHelper(dirX, new THREE.Vector3(0, 0, 0), 0.8, 0xef4444, 0.25, 0.15);
  triadGroup.add(arrowX);

  const dirY = new THREE.Vector3(0, 1, 0);
  const arrowY = new THREE.ArrowHelper(dirY, new THREE.Vector3(0, 0, 0), 0.8, 0x10b981, 0.25, 0.15);
  triadGroup.add(arrowY);

  const dirZ = new THREE.Vector3(0, 0, 1);
  const arrowZ = new THREE.ArrowHelper(dirZ, new THREE.Vector3(0, 0, 0), 0.8, 0x3b82f6, 0.25, 0.15);
  triadGroup.add(arrowZ);

  triadScene.add(triadGroup);
}

function updateEngineeringTriad() {
  if (!triadGroup || !triadRenderer || !triadScene || !triadCamera) return;
  triadGroup.quaternion.copy(mainGroup.quaternion);
  triadRenderer.render(triadScene, triadCamera);
}

// Real-Time Step Watcher
function onSimulationStepReceived(_stepData: SimulationStepData) {
  updateSliceDataTexture();
  updateObstacleSurfaceColors();
  updateRibbonStreamlinesGeometry();
}

watch(() => props.data, (newData) => {
  if (newData) {
    onSimulationStepReceived(newData);
  }
});

watch(() => [props.params.archetype, props.params.reynoldsNumber], () => {
  buildActiveArchetype();
  rebuildSlicePlane();
  buildRibbonStreamlines();
  buildVectorGlyphs();
});

// Animation Loop
function animate() {
  animId = requestAnimationFrame(animate);

  if (isAutoRotate.value) {
    targetRotationY += 0.003;
  }

  if (mainGroup) {
    mainGroup.rotation.x = targetRotationX;
    mainGroup.rotation.z = targetRotationY;
  }

  if (geometryGroup) geometryGroup.visible = showGeometry.value;
  if (ribbonStreamlinesGroup) ribbonStreamlinesGroup.visible = showStreamlines.value;
  if (pulsesGroup) pulsesGroup.visible = showStreamlines.value;
  if (cutplanesGroup) cutplanesGroup.visible = showCutplanes.value;
  if (glyphsGroup) glyphsGroup.visible = showGlyphs.value;
  if (floorGroup) floorGroup.visible = showFloorGrid.value;
  if (rakeBarGroup) rakeBarGroup.visible = showStreamlines.value;

  if (showStreamlines.value) {
    updateTracerPulses();
  }

  if (renderer && scene && camera) {
    renderer.render(scene, camera);
  }

  updateEngineeringTriad();
}

function onMouseDown(e: MouseEvent) {
  isDragging = true;
  previousMousePosition = { x: e.clientX, y: e.clientY };
}

function onMouseMove(e: MouseEvent) {
  if (!canvasMountRef.value || !renderer || !camera) return;

  const rect = renderer.domElement.getBoundingClientRect();
  mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
  mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

  if (isDragging) {
    const deltaX = e.clientX - previousMousePosition.x;
    const deltaY = e.clientY - previousMousePosition.y;
    targetRotationY += deltaX * 0.008;
    targetRotationX += deltaY * 0.008;
    previousMousePosition = { x: e.clientX, y: e.clientY };
  } else {
    raycaster.setFromCamera(mouse, camera);
    const targets = cutplaneMesh ? [cutplaneMesh, geometryGroup] : [geometryGroup];
    const intersects = raycaster.intersectObjects(targets, true);

    if (intersects.length > 0) {
      const hit = intersects[0];
      probe.value.active = true;
      probe.value.screenX = e.clientX - rect.left;
      probe.value.screenY = e.clientY - rect.top;

      const { p, speed, omega } = sampleFluidField(hit.point.x, hit.point.y);
      const f = activeField.value;

      if (f === 'p') {
        probe.value.value = p;
        probe.value.unit = 'Pa';
        probe.value.label = 'Pressure (p)';
      } else if (f === 'omega') {
        probe.value.value = omega;
        probe.value.unit = 's⁻¹';
        probe.value.label = 'Vorticity (ω)';
      } else {
        probe.value.value = speed;
        probe.value.unit = 'm/s';
        probe.value.label = 'Velocity |U|';
      }

      probe.value.subtext = `Pos: (${hit.point.x.toFixed(2)}, ${hit.point.y.toFixed(2)}) | Real Python CFD`;

      if (probeMarker) {
        probeMarker.position.copy(hit.point);
        probeMarker.visible = true;
      }
    } else {
      probe.value.active = false;
      if (probeMarker) probeMarker.visible = false;
    }
  }
}

function onMouseUp() {
  isDragging = false;
}

function onWheel(e: WheelEvent) {
  camera.position.z = Math.max(1.8, Math.min(9, camera.position.z + e.deltaY * 0.003));
}

function resetCamera() {
  targetRotationX = 0.32;
  targetRotationY = -0.68;
  camera.position.set(3.6, -4.0, 3.0);
  camera.lookAt(0, 0, 0);
}

function handleResize() {
  if (!canvasMountRef.value || !renderer || !camera) return;
  const width = canvasMountRef.value.clientWidth;
  const height = canvasMountRef.value.clientHeight;
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setSize(width, height);
}

onMounted(() => {
  initThree();
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  if (animId) cancelAnimationFrame(animId);
  window.removeEventListener('resize', handleResize);
});
</script>

<style scoped>
.three-viewport-container {
  width: 100%;
  height: 100%;
  position: relative;
  display: flex;
  flex-direction: column;
  background: #09060c;
  border-radius: 10px;
  overflow: hidden;
}

.viewport-header-strip {
  position: absolute;
  top: 10px;
  left: 14px;
  right: 14px;
  z-index: 25;
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: rgba(14, 10, 18, 0.92);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  padding: 8px 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
  pointer-events: auto;
}

.header-status-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  padding-bottom: 6px;
}

.status-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.viewport-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 0.3px;
}

.archetype-badge {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-cyan);
  background: rgba(0, 210, 255, 0.12);
  border: 1px solid rgba(0, 210, 255, 0.28);
  border-radius: 4px;
  padding: 2px 8px;
}

.live-tag {
  font-size: 10px;
  font-weight: 700;
  color: var(--text-muted);
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
  padding: 2px 6px;
  display: flex;
  align-items: center;
  gap: 5px;
}

.live-tag.live-active {
  color: #10b981;
  background: rgba(16, 185, 129, 0.15);
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.pulse-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.status-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.telemetry-pill {
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--text-secondary);
  background: rgba(255, 255, 255, 0.06);
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.telemetry-pill.forces {
  color: #38bdf8;
  border-color: rgba(56, 189, 248, 0.3);
}

.header-tools-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.tools-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.field-select-wrapper,
.colormap-select-wrapper {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--text-secondary);
}

.field-dropdown,
.colormap-dropdown {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  color: var(--text-primary);
  border-radius: 4px;
  padding: 3px 6px;
  font-size: 11px;
  outline: none;
  cursor: pointer;
}

.tools-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tool-btn-group {
  display: flex;
  align-items: center;
  gap: 4px;
}

.hud-tool-btn {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: var(--text-secondary);
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.hud-tool-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  color: var(--text-primary);
}

.hud-tool-btn.active {
  background: rgba(56, 189, 248, 0.2);
  border-color: #38bdf8;
  color: #38bdf8;
}

/* Interactive Slice & Rake Panel */
.interactive-controls-hud {
  position: absolute;
  top: 98px;
  right: 14px;
  width: 320px;
  z-index: 24;
  background: rgba(14, 10, 18, 0.94);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(56, 189, 248, 0.35);
  border-radius: 8px;
  padding: 10px 14px;
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.65);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.hud-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  padding-bottom: 6px;
}

.hud-panel-title {
  font-size: 11px;
  font-weight: 700;
  color: #38bdf8;
  letter-spacing: 0.3px;
}

.hud-close-btn {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 12px;
}

.hud-close-btn:hover {
  color: #fff;
}

.hud-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.hud-section-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 10px;
  font-weight: 600;
  color: var(--text-secondary);
}

.hud-param-badge {
  font-family: var(--font-mono);
  font-size: 9px;
  color: #00d2ff;
  background: rgba(0, 210, 255, 0.1);
  padding: 1px 5px;
  border-radius: 3px;
}

.axis-pill-group,
.preset-pill-group {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.axis-pill-btn,
.preset-pill-btn {
  flex: 1;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: var(--text-muted);
  font-size: 10px;
  padding: 3px 6px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.axis-pill-btn:hover,
.preset-pill-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
}

.axis-pill-btn.active {
  background: rgba(56, 189, 248, 0.25);
  border-color: #38bdf8;
  color: #38bdf8;
  font-weight: 600;
}

.slider-control-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 10px;
  color: var(--text-muted);
}

.slider-label {
  width: 50px;
}

.hud-slider {
  flex: 1;
  accent-color: #38bdf8;
  height: 4px;
  cursor: pointer;
}

.slider-val {
  width: 44px;
  text-align: right;
  font-family: var(--font-mono);
  color: var(--text-secondary);
  font-size: 9px;
}

.webgl-canvas-mount {
  width: 100%;
  height: 100%;
  cursor: grab;
}

.webgl-canvas-mount:active {
  cursor: grabbing;
}

/* Engineering Triad HUD Dock (Bottom Left) */
.engineering-triad-dock {
  position: absolute;
  bottom: 16px;
  left: 16px;
  z-index: 20;
  display: flex;
  align-items: flex-end;
  gap: 8px;
  pointer-events: none;
}

.triad-canvas {
  width: 70px;
  height: 70px;
  background: rgba(14, 10, 18, 0.65);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  backdrop-filter: blur(8px);
}

.triad-labels {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.axis-badge {
  font-size: 9px;
  font-family: var(--font-mono);
  padding: 1px 5px;
  border-radius: 3px;
  background: rgba(14, 10, 18, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.axis-badge.x { color: #ef4444; border-color: rgba(239, 68, 68, 0.3); }
.axis-badge.y { color: #10b981; border-color: rgba(16, 185, 129, 0.3); }
.axis-badge.z { color: #3b82f6; border-color: rgba(59, 130, 246, 0.3); }

.scientific-colorbar-dock {
  position: absolute;
  bottom: 16px;
  right: 16px;
  z-index: 20;
  pointer-events: none;
}

.colorbar-card {
  background: rgba(14, 10, 18, 0.88);
  backdrop-filter: blur(10px);
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  padding: 8px 12px;
  min-width: 180px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
}

.colorbar-header {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 5px;
}

.colorbar-gradient-track {
  width: 100%;
  height: 10px;
  border-radius: 3px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.1);
  margin-bottom: 4px;
}

.colorbar-gradient-fill {
  width: 100%;
  height: 100%;
}

.colorbar-ticks {
  display: flex;
  justify-content: space-between;
  font-size: 9px;
  font-family: var(--font-mono);
  color: var(--text-muted);
}

.hover-flow-probe-hud {
  position: absolute;
  pointer-events: none;
  z-index: 30;
  transform: translate(12px, -36px);
}

.probe-hud-card {
  background: rgba(14, 10, 18, 0.92);
  backdrop-filter: blur(8px);
  border: 1px solid #38bdf8;
  border-radius: 6px;
  padding: 6px 10px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.6);
}

.probe-val-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.probe-val-title {
  font-size: 11px;
  color: var(--text-secondary);
}

.probe-val-num {
  font-size: 12px;
  font-weight: 700;
  font-family: var(--font-mono);
  color: #38bdf8;
}

.probe-hud-tag {
  font-size: 9px;
  color: var(--text-muted);
  margin-top: 2px;
}

.hud-fade-enter-active,
.hud-fade-leave-active {
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.hud-fade-enter-from,
.hud-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.98);
}
</style>
