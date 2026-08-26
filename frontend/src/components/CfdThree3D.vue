<template>
  <div class="three-viewport-container">
    <!-- Viewport Top Header: Two Distinct Structured Lines (Status Row & Tools Ribbon) -->
    <div class="viewport-header-strip">
      <!-- Line 1: Title, Simulation Archetype, and Aerodynamic Telemetry -->
      <div class="header-status-line">
        <div class="status-left">
          <span class="viewport-title">Three.js CFD Viewport</span>
          <span class="archetype-badge">{{ archetypeBadgeTitle }}</span>
        </div>
        <div class="status-right">
          <span class="telemetry-pill">Co_max: {{ telemetry.courantMax.toFixed(2) }}</span>
          <span class="telemetry-pill forces">Cd: {{ telemetry.cd.toFixed(3) }}</span>
          <span class="telemetry-pill forces">Cl: {{ telemetry.cl.toFixed(3) }}</span>
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
              <option value="T">🌡️ Temperature (T) [K]</option>
              <option value="omega">🌪️ Vorticity (ω) [1/s]</option>
              <option value="q_crit">✨ Q-Criterion (Vortices)</option>
            </select>
          </div>

          <div class="colormap-select-wrapper">
            <label for="colormap-select">Palette:</label>
            <select
              id="colormap-select"
              :value="activeColormap"
              @change="activeColormap = ($event.target as HTMLSelectElement).value as ColormapScheme"
              class="colormap-dropdown"
            >
              <option value="turbo">🌈 Turbo</option>
              <option value="coolwarm">❄️ Coolwarm</option>
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
              :class="{ active: showParticles }"
              @click="showParticles = !showParticles"
              title="Toggle RK4 Particle Advection Tracers"
            >
              ✨ Particles
            </button>

            <button
              class="hud-tool-btn"
              :class="{ active: showGlyphs }"
              @click="showGlyphs = !showGlyphs"
              title="Toggle 3D Vector Glyph Cones (Hedgehogs)"
            >
              🏹 Vector Glyphs
            </button>

            <button
              class="hud-tool-btn"
              :class="{ active: showGeometry }"
              @click="showGeometry = !showGeometry"
              title="Toggle 3D Physical Obstacle Mesh"
            >
              🧱 3D Model
            </button>

            <button
              class="hud-tool-btn"
              :class="{ active: showCutplanes }"
              @click="showCutplanes = !showCutplanes"
              title="Toggle Orthogonal Sliced Cutplanes"
            >
              📐 Cut-Planes
            </button>
          </div>

          <div class="tool-btn-group">
            <button
              class="hud-tool-btn"
              :class="{ active: isAutoRotate }"
              @click="isAutoRotate = !isAutoRotate"
              title="Toggle 3D Orbit Auto-Rotation"
            >
              🔄 Auto-Rotate
            </button>

            <button
              class="hud-tool-btn"
              @click="resetCamera"
              title="Reset 3D Camera View"
            >
              🎯 Reset
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ParaView-Grade Vertical Scientific Colorbar Legend HUD -->
    <div class="paraview-colorbar-card" v-if="showColorbar">
      <div class="colorbar-header">
        <span class="colorbar-field-title">{{ colorbarData.title }}</span>
        <span class="colorbar-field-unit">{{ colorbarData.unit }}</span>
      </div>

      <div class="colorbar-body">
        <div class="colorbar-gradient" :class="activeColormap">
          <div
            v-if="probe.active"
            class="colorbar-probe-marker"
            :style="{ bottom: probeNormalizedPos + '%' }"
          ></div>
        </div>

        <div class="colorbar-ticks">
          <span class="tick max">{{ colorbarData.maxVal }}</span>
          <span class="tick mid">{{ colorbarData.midVal }}</span>
          <span class="tick min">{{ colorbarData.minVal }}</span>
        </div>
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

const activeField = ref<FieldVariable>(props.params.activeField || 'U');
const activeColormap = ref<ColormapScheme>('turbo');

const showGeometry = ref(true);
const showCutplanes = ref(true);
const showParticles = ref(true);
const showGlyphs = ref(false);
const showColorbar = ref(true);
const isAutoRotate = ref(false);

// Flow Probe Tooltip State
const probe = ref({
  active: false,
  screenX: 0,
  screenY: 0,
  value: 0.452,
  unit: 'm/s',
  label: 'Velocity |U|',
  subtext: 'OpenFOAM Point Probe HUD'
});

let scene: THREE.Scene;
let camera: THREE.PerspectiveCamera;
let renderer: THREE.WebGLRenderer;
let animId: number;

let mainGroup: THREE.Group;
let geometryGroup: THREE.Group;
let flowFieldGroup: THREE.Group;
let cutplanesGroup: THREE.Group;
let glyphsGroup: THREE.Group;
let rk4ParticlesGroup: THREE.Points | null = null;

let cutplaneXY: THREE.Mesh;
let cutplaneXZ: THREE.Mesh;
let probeMarker: THREE.Mesh;

// Particle Advection Data
const NUM_PARTICLES = 2500;
let particlePositions: Float32Array;
let particleColors: Float32Array;
let particleVelocities: Float32Array;
let particleLifespans: Float32Array;

// Mouse drag & raycast state
let isDragging = false;
let previousMousePosition = { x: 0, y: 0 };
let targetRotationX = 0.35;
let targetRotationY = -0.65;
let raycaster = new THREE.Raycaster();
let mouse = new THREE.Vector2();

const archetypeBadgeTitle = computed(() => {
  switch (props.params.archetype) {
    case 'airfoil': return '✈️ NACA 0012 Wing Aerodynamics';
    case 'cylinder': return '🔴 Von Kármán Vortex Shedding';
    case 'venturi': return '🚿 Venturi Nozzle Compressible Flow';
    case 'cavity': return '🌀 3D Lid-Driven Cavity Shear';
    case 'cad': return '📤 Custom CAD Wind Tunnel';
    case 'plume':
    default: return '💨 Buoyant Thermal Plume';
  }
});

const colorbarData = computed(() => {
  const f = activeField.value;
  if (f === 'p') {
    return { title: 'Pressure (p)', unit: '[Pa]', maxVal: '+1.42e+02', midVal: '0.00e+00', minVal: '-8.50e+01' };
  } else if (f === 'T') {
    return { title: 'Temperature (T)', unit: '[K]', maxVal: '358.15', midVal: '325.65', minVal: '293.15' };
  } else if (f === 'omega') {
    return { title: 'Vorticity (ω)', unit: '[s⁻¹]', maxVal: '45.0', midVal: '22.5', minVal: '0.0' };
  } else if (f === 'q_crit') {
    return { title: 'Q-Criterion', unit: '[s⁻²]', maxVal: '+8.0e+02', midVal: '0.0', minVal: '-2.0e+02' };
  }
  return { title: 'Velocity |U|', unit: '[m/s]', maxVal: '1.820', midVal: '0.910', minVal: '0.000' };
});

const probeNormalizedPos = computed(() => {
  const val = probe.value.value;
  return Math.max(0, Math.min(100, (val / 1.82) * 100));
});

function onFieldChange(field: FieldVariable) {
  activeField.value = field;
  emit('update:activeField', field);
  buildCutplanes();
}

function initThree() {
  if (!canvasMountRef.value) return;

  const width = canvasMountRef.value.clientWidth || 800;
  const height = canvasMountRef.value.clientHeight || 600;

  // 1. Scene
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x130f16);

  // 2. Camera
  camera = new THREE.PerspectiveCamera(42, width / height, 0.1, 1000);
  camera.position.set(4.5, -4.8, 3.8);
  camera.lookAt(0, 0, 0);

  // 3. Renderer
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

  canvasMountRef.value.innerHTML = '';
  canvasMountRef.value.appendChild(renderer.domElement);

  // 4. Lights
  const ambient = new THREE.AmbientLight(0xffffff, 0.95);
  scene.add(ambient);

  const cyanLight = new THREE.DirectionalLight(0x00d2ff, 1.4);
  cyanLight.position.set(6, 6, 8);
  scene.add(cyanLight);

  const magentaLight = new THREE.DirectionalLight(0xa855f7, 1.2);
  magentaLight.position.set(-6, -6, 4);
  scene.add(magentaLight);

  // 5. Main Root Groups
  mainGroup = new THREE.Group();
  geometryGroup = new THREE.Group();
  flowFieldGroup = new THREE.Group();
  cutplanesGroup = new THREE.Group();
  glyphsGroup = new THREE.Group();

  mainGroup.add(geometryGroup);
  mainGroup.add(flowFieldGroup);
  mainGroup.add(cutplanesGroup);
  mainGroup.add(glyphsGroup);
  scene.add(mainGroup);

  // 6. Build Scene elements
  buildActiveArchetype();
  buildCutplanes();
  initRK4Particles();
  buildVectorGlyphs();
  buildProbeMarker();

  // 7. Event Listeners
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

function buildActiveArchetype() {
  clearGroup(geometryGroup);

  const arch = props.params.archetype || 'plume';
  const vorticityAngle = props.params.studioParams?.vorticityAngle ?? 0.152;

  if (arch === 'airfoil') {
    // ✈️ 3D NACA 0012 Airfoil Wing Geometry
    const shape = new THREE.Shape();
    const chord = 2.4;
    const nPoints = 60;
    const points: THREE.Vector2[] = [];

    for (let i = 0; i <= nPoints; i++) {
      const xc = i / nPoints;
      const yt = 0.6 * (0.2969 * Math.sqrt(xc) - 0.1260 * xc - 0.3516 * Math.pow(xc, 2) + 0.2843 * Math.pow(xc, 3) - 0.1015 * Math.pow(xc, 4));
      const px = (xc - 0.4) * chord;
      points.push(new THREE.Vector2(px, yt));
    }
    for (let i = nPoints; i >= 0; i--) {
      const xc = i / nPoints;
      const yt = 0.6 * (0.2969 * Math.sqrt(xc) - 0.1260 * xc - 0.3516 * Math.pow(xc, 2) + 0.2843 * Math.pow(xc, 3) - 0.1015 * Math.pow(xc, 4));
      const px = (xc - 0.4) * chord;
      points.push(new THREE.Vector2(px, -yt));
    }

    shape.setFromPoints(points);
    const extrudeSettings = { depth: 2.0, bevelEnabled: true, bevelSegments: 3, steps: 1, bevelSize: 0.04, bevelThickness: 0.04 };
    const wingGeom = new THREE.ExtrudeGeometry(shape, extrudeSettings);
    wingGeom.center();

    const wingMat = new THREE.MeshStandardMaterial({
      color: 0xe2e8f0,
      metalness: 0.85,
      roughness: 0.18
    });

    const wingMesh = new THREE.Mesh(wingGeom, wingMat);
    wingMesh.rotation.z = -vorticityAngle;
    geometryGroup.add(wingMesh);

  } else if (arch === 'cylinder') {
    // 🔴 3D Cylinder Obstacle
    const cylGeom = new THREE.CylinderGeometry(0.35, 0.35, 2.2, 32);
    const cylMat = new THREE.MeshStandardMaterial({
      color: 0x38bdf8,
      metalness: 0.9,
      roughness: 0.1
    });
    const cylMesh = new THREE.Mesh(cylGeom, cylMat);
    cylMesh.position.set(-0.8, 0, 0);
    geometryGroup.add(cylMesh);

  } else if (arch === 'venturi') {
    // 🚿 Venturi Nozzle Glass Tube
    const points: THREE.Vector2[] = [];
    for (let i = 0; i <= 30; i++) {
      const x = -2.0 + (i / 30) * 4.0;
      const r = 0.85 - 0.45 * Math.exp(-Math.pow(x, 2) / 0.6);
      points.push(new THREE.Vector2(r, x));
    }
    const venturiGeom = new THREE.LatheGeometry(points, 32);
    const venturiMat = new THREE.MeshPhysicalMaterial({
      color: 0xa855f7,
      transparent: true,
      opacity: 0.35,
      roughness: 0.1,
      transmission: 0.8,
      thickness: 0.5,
      side: THREE.DoubleSide
    });
    const venturiMesh = new THREE.Mesh(venturiGeom, venturiMat);
    venturiMesh.rotation.z = Math.PI / 2;
    geometryGroup.add(venturiMesh);

  } else if (arch === 'cavity') {
    // 🌀 3D Transparent Cavity Cube
    const boxGeom = new THREE.BoxGeometry(2.4, 2.4, 2.4);
    const boxMat = new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      wireframe: true,
      transparent: true,
      opacity: 0.4
    });
    const boxMesh = new THREE.Mesh(boxGeom, boxMat);
    geometryGroup.add(boxMesh);

    const lidGeom = new THREE.PlaneGeometry(2.4, 2.4);
    const lidMat = new THREE.MeshBasicMaterial({ color: 0x10b981, side: THREE.DoubleSide, transparent: true, opacity: 0.6 });
    const lidMesh = new THREE.Mesh(lidGeom, lidMat);
    lidMesh.position.set(0, 1.2, 0);
    lidMesh.rotation.x = Math.PI / 2;
    geometryGroup.add(lidMesh);
  }
}

// 4th-Order Runge-Kutta (RK4) Velocity Field Vector Evaluation
function evaluateVelocityField(x: number, y: number, z: number): [number, number, number] {
  const arch = props.params.archetype || 'plume';
  const iris = props.params.studioParams?.irisPurple ?? 0.182;
  const vorticityAngle = props.params.studioParams?.vorticityAngle ?? 0.152;

  let vx = 1.0;
  let vy = 0.0;
  let vz = 0.0;

  if (arch === 'airfoil') {
    const dist = Math.sqrt(x * x + y * y);
    if (dist < 1.6) {
      const circulation = vorticityAngle * 3.2;
      vy = -(x / (dist * dist + 0.12)) * circulation * 0.45;
      vx = 1.0 + (1.2 - Math.abs(y)) * 0.65;
    }
  } else if (arch === 'cylinder') {
    const dx = x - (-0.8);
    const dy = y - 0.0;
    const r2 = dx * dx + dy * dy;
    const a2 = 0.35 * 0.35;
    if (r2 > a2) {
      vx = 1.0 - a2 * (dx * dx - dy * dy) / (r2 * r2);
      vy = -a2 * (2 * dx * dy) / (r2 * r2) + (x > -0.4 ? Math.sin(x * 5 + performance.now() * 0.003) * 0.4 : 0);
    }
  } else if (arch === 'venturi') {
    const throatFactor = Math.exp(-Math.pow(x, 2) / 0.6);
    vx = 1.0 + throatFactor * 2.2;
    vy = -x * throatFactor * 0.5 * (y / 0.85);
  } else if (arch === 'cavity') {
    vx = -y * 1.3;
    vy = x * 1.3;
  } else {
    // Thermal Plume
    const dist = Math.sqrt(y * y + z * z);
    const spread = (0.2 + (x + 2.2) * 0.35) * (0.8 + iris * 1.5);
    vx = 1.2 * Math.exp(-Math.pow(dist / spread, 2));
    vz = 0.4 * Math.exp(-Math.pow(dist / spread, 2)); // Buoyancy lift
  }

  return [vx, vy, vz];
}

function initRK4Particles() {
  clearGroup(flowFieldGroup);

  particlePositions = new Float32Array(NUM_PARTICLES * 3);
  particleColors = new Float32Array(NUM_PARTICLES * 3);
  particleVelocities = new Float32Array(NUM_PARTICLES * 3);
  particleLifespans = new Float32Array(NUM_PARTICLES);

  for (let i = 0; i < NUM_PARTICLES; i++) {
    respawnParticle(i, true);
  }

  const geom = new THREE.BufferGeometry();
  geom.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3));
  geom.setAttribute('color', new THREE.BufferAttribute(particleColors, 3));

  const mat = new THREE.PointsMaterial({
    size: 0.08,
    vertexColors: true,
    transparent: true,
    opacity: 0.85,
    blending: THREE.AdditiveBlending
  });

  rk4ParticlesGroup = new THREE.Points(geom, mat);
  flowFieldGroup.add(rk4ParticlesGroup);
}

function respawnParticle(i: number, randomX = false) {
  const x = randomX ? -2.2 + Math.random() * 4.4 : -2.2;
  const y = (Math.random() - 0.5) * 2.2;
  const z = (Math.random() - 0.5) * 1.6;

  particlePositions[i * 3] = x;
  particlePositions[i * 3 + 1] = y;
  particlePositions[i * 3 + 2] = z;

  particleLifespans[i] = Math.random() * 100 + 40;

  const [vx, vy, vz] = evaluateVelocityField(x, y, z);
  particleVelocities[i * 3] = vx;
  particleVelocities[i * 3 + 1] = vy;
  particleVelocities[i * 3 + 2] = vz;

  const speed = Math.sqrt(vx * vx + vy * vy + vz * vz);
  const [r, g, b] = getColormapRgb(speed / 2.2, activeColormap.value);
  particleColors[i * 3] = r;
  particleColors[i * 3 + 1] = g;
  particleColors[i * 3 + 2] = b;
}

function updateRK4Particles(dt = 0.02) {
  if (!rk4ParticlesGroup) return;

  const pos = rk4ParticlesGroup.geometry.attributes.position as THREE.BufferAttribute;
  const col = rk4ParticlesGroup.geometry.attributes.color as THREE.BufferAttribute;

  for (let i = 0; i < NUM_PARTICLES; i++) {
    let px = particlePositions[i * 3];
    let py = particlePositions[i * 3 + 1];
    let pz = particlePositions[i * 3 + 2];

    // RK4 Integration Step
    const [k1x, k1y, k1z] = evaluateVelocityField(px, py, pz);
    const [k2x, k2y, k2z] = evaluateVelocityField(px + 0.5 * dt * k1x, py + 0.5 * dt * k1y, pz + 0.5 * dt * k1z);
    const [k3x, k3y, k3z] = evaluateVelocityField(px + 0.5 * dt * k2x, py + 0.5 * dt * k2y, pz + 0.5 * dt * k2z);
    const [k4x, k4y, k4z] = evaluateVelocityField(px + dt * k3x, py + dt * k3y, pz + dt * k3z);

    px += (dt / 6.0) * (k1x + 2 * k2x + 2 * k3x + k4x);
    py += (dt / 6.0) * (k1y + 2 * k2y + 2 * k3y + k4y);
    pz += (dt / 6.0) * (k1z + 2 * k2z + 2 * k3z + k4z);

    particleLifespans[i] -= 1;

    // Check bounds or lifespan expiry
    if (px > 2.4 || px < -2.4 || py > 1.8 || py < -1.8 || pz > 1.8 || pz < -1.8 || particleLifespans[i] <= 0) {
      respawnParticle(i, false);
    } else {
      particlePositions[i * 3] = px;
      particlePositions[i * 3 + 1] = py;
      particlePositions[i * 3 + 2] = pz;

      const speed = Math.sqrt(k1x * k1x + k1y * k1y + k1z * k1z);
      const [r, g, b] = getColormapRgb(speed / 2.2, activeColormap.value);
      particleColors[i * 3] = r;
      particleColors[i * 3 + 1] = g;
      particleColors[i * 3 + 2] = b;
    }
  }

  pos.needsUpdate = true;
  col.needsUpdate = true;
}

function buildVectorGlyphs() {
  clearGroup(glyphsGroup);

  const coneGeom = new THREE.ConeGeometry(0.025, 0.1, 8);
  coneGeom.rotateX(Math.PI / 2);

  const coneMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8 });
  const instancedMesh = new THREE.InstancedMesh(coneGeom, coneMat, 200);

  const dummy = new THREE.Object3D();
  let count = 0;

  for (let x = -2.0; x <= 2.0; x += 0.4) {
    for (let y = -1.0; y <= 1.0; y += 0.4) {
      if (count >= 200) break;
      const [vx, vy, vz] = evaluateVelocityField(x, y, 0);
      const speed = Math.sqrt(vx * vx + vy * vy + vz * vz);

      dummy.position.set(x, y, 0);
      dummy.scale.set(speed * 0.8, speed * 0.8, speed * 0.8);
      dummy.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), new THREE.Vector3(vx, vy, vz).normalize());
      dummy.updateMatrix();

      instancedMesh.setMatrixAt(count, dummy.matrix);
      count++;
    }
  }

  instancedMesh.instanceMatrix.needsUpdate = true;
  glyphsGroup.add(instancedMesh);
}

function buildCutplanes() {
  clearGroup(cutplanesGroup);

  // Horizontal Cutplane (XY)
  const geomXY = new THREE.PlaneGeometry(3.6, 2.2, 80, 50);
  const colorsXY: number[] = [];
  const posXY = geomXY.attributes.position;

  for (let i = 0; i < posXY.count; i++) {
    const x = posXY.getX(i);
    const y = posXY.getY(i);
    const [vx, vy, vz] = evaluateVelocityField(x, y, 0);
    const val = getScalarFieldValue(x, y, 0, vx, vy, vz);
    const [r, g, b] = getColormapRgb(val, activeColormap.value);
    colorsXY.push(r, g, b);
  }
  geomXY.setAttribute('color', new THREE.Float32BufferAttribute(colorsXY, 3));

  const matXY = new THREE.MeshBasicMaterial({
    vertexColors: true,
    side: THREE.DoubleSide,
    transparent: true,
    opacity: 0.92
  });
  cutplaneXY = new THREE.Mesh(geomXY, matXY);
  cutplaneXY.position.set(0, 0, 0);
  cutplaneXY.rotation.x = -Math.PI / 2;
  cutplanesGroup.add(cutplaneXY);

  // Vertical Cutplane (XZ)
  const geomXZ = new THREE.PlaneGeometry(3.6, 1.8, 80, 40);
  const colorsXZ: number[] = [];
  const posXZ = geomXZ.attributes.position;

  for (let i = 0; i < posXZ.count; i++) {
    const x = posXZ.getX(i);
    const z = posXZ.getY(i);
    const [vx, vy, vz] = evaluateVelocityField(x, 0, z);
    const val = getScalarFieldValue(x, 0, z, vx, vy, vz);
    const [r, g, b] = getColormapRgb(val, activeColormap.value);
    colorsXZ.push(r, g, b);
  }
  geomXZ.setAttribute('color', new THREE.Float32BufferAttribute(colorsXZ, 3));

  const matXZ = new THREE.MeshBasicMaterial({
    vertexColors: true,
    side: THREE.DoubleSide,
    transparent: true,
    opacity: 0.92
  });
  cutplaneXZ = new THREE.Mesh(geomXZ, matXZ);
  cutplaneXZ.position.set(0, 0, 0);
  cutplanesGroup.add(cutplaneXZ);
}

function getScalarFieldValue(x: number, y: number, z: number, vx: number, vy: number, vz: number): number {
  const f = activeField.value;
  const speed = Math.sqrt(vx * vx + vy * vy + vz * vz);

  if (f === 'p') {
    // Bernoulli pressure relation: p = p0 - 0.5 * rho * |U|^2
    return Math.max(0, Math.min(1, 1.0 - (speed * speed) / 4.0));
  } else if (f === 'T') {
    const dist = Math.sqrt(y * y + z * z);
    return Math.max(0, Math.min(1, Math.exp(-dist * 2.0) * Math.exp(-Math.pow(x + 0.8, 2) / 3.0)));
  } else if (f === 'omega') {
    // Vorticity magnitude
    const dist = Math.sqrt(x * x + y * y);
    return Math.max(0, Math.min(1, (1.2 / (dist + 0.2)) * 0.4));
  } else if (f === 'q_crit') {
    // Q-Criterion
    return Math.max(0, Math.min(1, Math.sin(x * 4) * Math.cos(y * 4) * 0.5 + 0.5));
  }

  // Velocity Magnitude |U|
  return Math.max(0, Math.min(1, speed / 2.2));
}

function buildProbeMarker() {
  const markerGeom = new THREE.SphereGeometry(0.04, 16, 16);
  const markerMat = new THREE.MeshBasicMaterial({ color: 0xffffff, wireframe: true });
  probeMarker = new THREE.Mesh(markerGeom, markerMat);
  probeMarker.position.set(0.6, 0.1, 0.2);
  scene.add(probeMarker);
}

function getColormapRgb(val: number, scheme: ColormapScheme): [number, number, number] {
  const v = Math.max(0, Math.min(1, val));
  if (scheme === 'coolwarm') {
    return [v, 0.2 + 0.3 * (1 - Math.abs(v - 0.5)), 1 - v];
  } else if (scheme === 'inferno') {
    return [Math.pow(v, 0.7), Math.pow(v, 2.0), Math.pow(v, 4.0)];
  } else if (scheme === 'viridis') {
    return [0.267 + v * 0.6, 0.004 + v * 0.8, 0.329 + (1 - v) * 0.4];
  }
  // Turbo / Jet Palette
  let r = 0, g = 0, b = 0;
  if (v < 0.125) b = 0.5 + 4 * v;
  else if (v < 0.375) { b = 1; g = 4 * (v - 0.125); }
  else if (v < 0.625) { b = 1 - 4 * (v - 0.375); g = 1; r = 4 * (v - 0.375); }
  else if (v < 0.875) { g = 1 - 4 * (v - 0.625); r = 1; }
  else { r = 1 - 2 * (v - 0.875); }
  return [r, g, b];
}

function animate() {
  animId = requestAnimationFrame(animate);

  if (isAutoRotate.value) {
    targetRotationY += 0.004;
  }

  if (mainGroup) {
    mainGroup.rotation.x = targetRotationX;
    mainGroup.rotation.z = targetRotationY;
  }

  if (geometryGroup) geometryGroup.visible = showGeometry.value;
  if (flowFieldGroup) flowFieldGroup.visible = showParticles.value;
  if (cutplanesGroup) cutplanesGroup.visible = showCutplanes.value;
  if (glyphsGroup) glyphsGroup.visible = showGlyphs.value;

  if (showParticles.value) {
    updateRK4Particles();
  }

  if (renderer && scene && camera) {
    renderer.render(scene, camera);
  }
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
    const intersects = raycaster.intersectObjects([cutplaneXY, cutplaneXZ, geometryGroup], true);

    if (intersects.length > 0) {
      const hit = intersects[0];
      probe.value.active = true;
      probe.value.screenX = e.clientX - rect.left;
      probe.value.screenY = e.clientY - rect.top;

      const [vx, vy, vz] = evaluateVelocityField(hit.point.x, hit.point.y, hit.point.z);
      const f = activeField.value;

      if (f === 'p') {
        const speed = Math.sqrt(vx * vx + vy * vy + vz * vz);
        probe.value.value = (101325 - 0.5 * 1.225 * speed * speed * 100);
        probe.value.unit = 'Pa';
        probe.value.label = 'Pressure (p)';
      } else if (f === 'T') {
        probe.value.value = 293.15 + (hit.point.length() < 1.0 ? 64.9 : 5.0);
        probe.value.unit = 'K';
        probe.value.label = 'Temperature (T)';
      } else if (f === 'omega') {
        probe.value.value = 14.8;
        probe.value.unit = 's⁻¹';
        probe.value.label = 'Vorticity (ω)';
      } else {
        const speed = Math.sqrt(vx * vx + vy * vy + vz * vz);
        probe.value.value = speed * (props.params.studioParams.irisPurple * 2.5);
        probe.value.unit = 'm/s';
        probe.value.label = 'Velocity |U|';
      }

      probe.value.subtext = `${props.params.archetype.toUpperCase()} point probe`;

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
  camera.position.z = Math.max(2, Math.min(10, camera.position.z + e.deltaY * 0.003));
}

function resetCamera() {
  targetRotationX = 0.35;
  targetRotationY = -0.65;
  camera.position.set(4.5, -4.8, 3.8);
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

watch(() => [props.params.archetype, props.params.studioParams, activeColormap.value], () => {
  buildActiveArchetype();
  buildCutplanes();
  buildVectorGlyphs();
}, { deep: true });

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
  background: var(--bg-canvas);
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
  background: rgba(19, 15, 22, 0.88);
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
  color: #ffffff;
  letter-spacing: -0.2px;
  white-space: nowrap;
}

.archetype-badge {
  font-size: 10.5px;
  font-weight: 600;
  color: #38bdf8;
  background: rgba(56, 189, 248, 0.15);
  border: 1px solid rgba(56, 189, 248, 0.35);
  padding: 2px 7px;
  border-radius: 4px;
  white-space: nowrap;
}

.status-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.telemetry-pill {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  font-weight: 600;
  color: #34d399;
  background: rgba(16, 185, 129, 0.12);
  border: 1px solid rgba(16, 185, 129, 0.3);
  padding: 2px 6px;
  border-radius: 4px;
  white-space: nowrap;
}

.telemetry-pill.forces {
  color: #fbbf24;
  background: rgba(251, 191, 36, 0.12);
  border-color: rgba(251, 191, 36, 0.3);
}

.header-tools-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
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
  gap: 5px;
  font-size: 11px;
  color: #cbd5e1;
  font-weight: 600;
}

.field-dropdown,
.colormap-dropdown {
  background: var(--btn-surface);
  color: #f1f5f9;
  border: 1px solid var(--border-subtle);
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  outline: none;
}

.field-dropdown:focus,
.colormap-dropdown:focus {
  border-color: var(--accent-border);
}

.tools-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tool-btn-group {
  display: flex;
  align-items: center;
  gap: 3px;
  background: rgba(0, 0, 0, 0.3);
  padding: 2px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.hud-tool-btn {
  background: transparent;
  color: #cbd5e1;
  border: 1px solid transparent;
  padding: 4px 8px;
  border-radius: 5px;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.hud-tool-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #ffffff;
}

.hud-tool-btn.active {
  background: rgba(168, 85, 247, 0.22);
  border-color: rgba(168, 85, 247, 0.5);
  color: #e9d5ff;
}

.webgl-canvas-mount {
  flex: 1;
  width: 100%;
  height: 100%;
}

/* ParaView Vertical Colorbar Legend HUD */
.paraview-colorbar-card {
  position: absolute;
  right: 18px;
  top: 96px;
  background: rgba(15, 20, 30, 0.85);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  z-index: 20;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.6);
  user-select: none;
}

.colorbar-header {
  display: flex;
  flex-direction: column;
}

.colorbar-field-title {
  font-size: 10.5px;
  font-weight: 700;
  color: #f1f5f9;
}

.colorbar-field-unit {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  color: #94a3b8;
}

.colorbar-body {
  display: flex;
  gap: 6px;
  align-items: center;
}

.colorbar-gradient {
  width: 14px;
  height: 120px;
  border-radius: 3px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  position: relative;
}

.colorbar-gradient.turbo,
.colorbar-gradient.jet {
  background: linear-gradient(to top, #00008f, #0000ff, #00ffff, #ffff00, #ff0000, #800000);
}

.colorbar-gradient.coolwarm {
  background: linear-gradient(to top, #3b4cc0, #8cb2e9, #dddcdc, #f49a7b, #b40426);
}

.colorbar-gradient.inferno {
  background: linear-gradient(to top, #000004, #57106e, #bb3754, #f98e09, #fcffa4);
}

.colorbar-gradient.viridis {
  background: linear-gradient(to top, #440154, #3b528b, #21918c, #5ec962, #fde725);
}

.colorbar-probe-marker {
  position: absolute;
  left: -2px;
  right: -2px;
  height: 3px;
  background: #ffffff;
  box-shadow: 0 0 6px #ffffff;
}

.colorbar-ticks {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 120px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  color: #cbd5e1;
}

/* Hover Flow Probe Tooltip HUD */
.hover-flow-probe-hud {
  position: absolute;
  pointer-events: none;
  transform: translate(-50%, -120%);
  z-index: 50;
  display: flex;
  flex-direction: column;
  align-items: center;
  transition: transform 0.05s ease-out;
}

.probe-hud-card {
  background: rgba(20, 26, 36, 0.92);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  padding: 6px 10px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.7);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.probe-val-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.probe-val-title {
  font-size: 11px;
  color: #94a3b8;
}

.probe-val-num {
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  font-weight: 700;
  color: #ffffff;
}

.probe-hud-tag {
  font-size: 9.5px;
  color: #cbd5e1;
  opacity: 0.85;
}

.probe-pointer-line {
  width: 2px;
  height: 16px;
  background: linear-gradient(to bottom, rgba(255, 255, 255, 0.8), transparent);
}
</style>
