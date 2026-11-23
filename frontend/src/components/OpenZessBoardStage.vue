<template>
  <div
    class="board-stage-root"
    ref="stageRoot"
    @pointerdown="onPointerDown"
    @pointermove="onPointerMove"
    @pointerup="onPointerUp"
    @pointerleave="onPointerLeave"
    @wheel.prevent="onWheel"
  >
    <canvas ref="webglCanvas" class="board-webgl-canvas"></canvas>

    <!-- Crisp 3D-Projected SVG Elbow Leaders & Hotspots (#board style) -->
    <svg v-if="showCallouts" class="board-leaders-svg" aria-hidden="true">
      <g
        v-for="pin in projectedPins"
        :key="'l-' + pin.id"
        class="board-leader-g"
        :class="{ hot: hoveredPinId === pin.id || selectedPinId === pin.id }"
      >
        <path :d="pin.pathD" class="board-leader-path" />
        <circle :cx="pin.ax" :cy="pin.ay" r="10" class="board-dot-halo" />
        <circle :cx="pin.ax" :cy="pin.ay" r="5" class="board-dot-ring" />
        <circle :cx="pin.ax" :cy="pin.ay" r="2.6" class="board-dot-core" />
      </g>
    </svg>

    <!-- Crisp #board Pill Tags -->
    <div v-if="showCallouts" class="board-tags-layer">
      <button
        v-for="pin in projectedPins"
        :key="pin.id"
        class="board-tag-pill"
        :class="{ active: selectedPinId === pin.id, hot: hoveredPinId === pin.id }"
        :style="{ left: pin.lx + 'px', top: pin.ly + 'px', transform: pin.alignRight ? 'translate(-100%, -50%)' : 'translate(0, -50%)' }"
        @pointerenter="hoveredPinId = pin.id"
        @pointerleave="hoveredPinId = null"
        @click.stop="togglePin(pin)"
      >
        <span class="tag-dot"></span>
        <span class="tag-title">{{ pin.label }}</span>
        <span class="tag-val">{{ pin.shortVal }}</span>
      </button>

      <!-- Free-Moving Live Lagrangian Probe Tag -->
      <div
        v-if="showFlow && freeProbeScreen.visible"
        class="board-free-probe-tag"
        :style="{ left: freeProbeScreen.x + 'px', top: freeProbeScreen.y + 'px' }"
      >
        <span class="free-dot"></span>
        <span>FLOW {{ freeProbeScreen.speed }} m/s</span>
      </div>

      <!-- Click-to-Inspect Physics Card -->
      <div v-if="selectedPin" class="board-inspector-card" @pointerdown.stop>
        <div class="insp-head">
          <strong>{{ selectedPin.title }}</strong>
          <button class="insp-close" @click="selectedPinId = null">×</button>
        </div>
        <p class="insp-desc">{{ selectedPin.desc }}</p>
        <div class="insp-metric">{{ selectedPin.metric }}</div>
        <div class="insp-controls">
          <label class="insp-slider">
            <span>Flow Re: <b>{{ reynolds }}</b></span>
            <input
              type="range"
              min="50"
              max="600"
              step="25"
              :value="reynolds"
              @change="onReSliderChange"
            />
          </label>
          <div class="insp-btns">
            <button class="insp-btn" @click="$emit('toggle-run')">{{ isRunning ? 'Pause' : 'Run' }}</button>
            <button class="insp-btn" @click="$emit('break-cfl')">Break CFL</button>
            <button class="insp-btn" @click="$emit('self-heal')">Self-Heal</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Cursor Hover Readout -->
    <div
      v-if="hoverReadout.visible"
      class="board-hover-tip"
      :style="{ left: hoverReadout.x + 'px', top: hoverReadout.y + 'px' }"
    >
      <b>{{ hoverReadout.title }}</b>
      <span>{{ hoverReadout.detail }}</span>
    </div>

    <!-- Exact #board-Style Floating Bottom Viewbar -->
    <div class="board-viewbar" role="toolbar" aria-label="3D view controls" @pointerdown.stop>
      <button class="bvb-btn" @click="rotateAzimuth(-Math.PI / 8)" title="Turn left (Q)">
        <svg viewBox="0 0 24 24"><path d="M4.5 10.5A8 8 0 1 1 6 17" /><path d="M4 5v5.8h5.8" /></svg>
      </button>
      <button class="bvb-btn" @click="rotateAzimuth(Math.PI / 8)" title="Turn right (E)">
        <svg viewBox="0 0 24 24"><path d="M19.5 10.5A8 8 0 1 0 18 17" /><path d="M20 5v5.8h-5.8" /></svg>
      </button>
      <span class="bvb-sep"></span>
      <button class="bvb-btn" @click="zoomBy(0.84)" title="Zoom out (−)">
        <svg viewBox="0 0 24 24"><path d="M5 12h14" /></svg>
      </button>
      <button class="bvb-btn" @click="zoomBy(1.18)" title="Zoom in (+)">
        <svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14" /></svg>
      </button>
      <span class="bvb-sep"></span>
      <button class="bvb-btn" @click="resetIsoView" title="Reset isometric view (R)">
        <svg viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="8.5" />
          <path d="M12 5.5 14 12h-4z" class="svg-fill-accent" />
          <path d="M12 18.5 10 12h4z" class="svg-fill-muted" />
        </svg>
      </button>
      <span class="bvb-sep"></span>
      <button class="bvb-btn toggle" :class="{ active: showFlow }" @click="showFlow = !showFlow" title="Toggle 3D Flow Beads (F)">
        <svg viewBox="0 0 24 24">
          <path d="M2.5 15.5c4.2 0 5.3-7 9.5-7s5.3 7 9.5 7" />
          <circle cx="6.6" cy="13" r="1.7" class="svg-fill-current" />
          <circle cx="12" cy="8.5" r="1.7" class="svg-fill-current" />
          <circle cx="17.4" cy="13" r="1.7" class="svg-fill-current" />
        </svg>
      </button>
      <button class="bvb-btn toggle" :class="{ active: showCallouts }" @click="showCallouts = !showCallouts" title="Toggle Callout Pins (L)">
        <svg viewBox="0 0 24 24">
          <path d="M1.5 12h4.2l1.6-4 2.6 8 2.6-8 2.6 8 1.6-4h5.8" />
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue';
import * as THREE from 'three';
import type { OpenFoamWasmEngine } from '../utils/openfoamWasmBridge';

const props = defineProps<{
  engine: OpenFoamWasmEngine | null;
  preset: number;
  fieldRev: number;
  isPaperTheme: boolean;
  isRunning: boolean;
  reynolds: number;
  colorMap: 'coolwarm' | 'rainbow' | 'viridis' | 'plasma' | 'jet';
  fieldKey: string;
  representation: 'surface' | 'surface_with_edges' | 'wireframe' | 'points';
  opacity: number;
  showSource: boolean;
}>();

const emit = defineEmits<{
  (e: 'update-reynolds', val: number): void;
  (e: 'toggle-run'): void;
  (e: 'break-cfl'): void;
  (e: 'self-heal'): void;
  (e: 'probe-change', info: { x: number; y: number; val: number }): void;
}>();

const stageRoot = ref<HTMLDivElement | null>(null);
const webglCanvas = ref<HTMLCanvasElement | null>(null);

const showFlow = ref<boolean>(true);
const showCallouts = ref<boolean>(true);
const hoveredPinId = ref<string | null>(null);
const selectedPinId = ref<string | null>(null);
const viewRev = ref<number>(0);
const vpSize = ref<{ w: number; h: number }>({ w: 800, h: 520 });
const hoverReadout = ref({ visible: false, x: 0, y: 0, title: '', detail: '' });
const freeProbeScreen = ref({ visible: false, x: 0, y: 0, speed: '0.00' });

// Three.js core handles (kept outside Vue reactivity for 60 FPS zero-GC rendering)
let renderer: THREE.WebGLRenderer | null = null;
let scene: THREE.Scene | null = null;
let camera: THREE.OrthographicCamera | null = null;
let rafId: number | null = null;
let resizeObs: ResizeObserver | null = null;

// Scene groups & dynamic meshes
let groundGridMat: THREE.ShaderMaterial | null = null;
let shadowPlaneMat: THREE.ShadowMaterial | null = null;
let deckMesh: THREE.Mesh | null = null;
let deckCanvas: HTMLCanvasElement | null = null;
let deckCtx: CanvasRenderingContext2D | null = null;
let deckTexture: THREE.CanvasTexture | null = null;
let deckWireframe: THREE.LineSegments | null = null;
let modelGroup: THREE.Group | null = null;
let swayTarget: THREE.Object3D | null = null;
let lidBeltMesh: THREE.Mesh | null = null;

// 3D Flow Beads (InstancedMesh for crisp 60 FPS beads + dark ink rims)
const BEAD_COUNT = 84;
let beadCoreMesh: THREE.InstancedMesh | null = null;
let beadRimMesh: THREE.InstancedMesh | null = null;
let freeProbeMesh: THREE.Group | null = null;
let freeTrailLine: THREE.Line | null = null;
const dummyObj = new THREE.Object3D();

interface BeadState {
  x: number; // domain [-1, 1]
  y: number; // domain [-1, 1]
  z: number; // height above deck
  life: number;
  maxLife: number;
}
const beads: BeadState[] = Array.from({ length: BEAD_COUNT }, () => ({
  x: Math.random() * 2 - 1,
  y: Math.random() * 2 - 1,
  z: 0.35 + Math.random() * 1.4,
  life: Math.random() * 160,
  maxLife: 120 + Math.random() * 80
}));

const freeProbe = {
  x: -0.92,
  y: 0.12,
  z: 0.9,
  trail: [] as THREE.Vector3[]
};

// Isometric Camera Orbit State (#board exact feel)
const camState = {
  azimuth: -0.72,       // ~ -41 deg isometric
  elevation: 0.58,      // ~ 33 deg elevation
  zoom: 1.05,
  target: new THREE.Vector3(0, 0.7, 0),
  targetAz: -0.72,
  targetEl: 0.58,
  targetZoom: 1.05,
  targetLook: new THREE.Vector3(0, 0.7, 0)
};

let dragging: 'orbit' | 'pan' | null = null;
let lastPtr = { x: 0, y: 0 };

// World dimensions of the CFD Wind-Tunnel Test Deck
const DECK_W = 14.0;
const DECK_D = 11.0;
const DECK_H = 0.55;

function domainToWorld(dx: number, dy: number, height: number = 0): THREE.Vector3 {
  // Domain x in [-1, 1] -> World X [-DECK_W/2, DECK_W/2]
  // Domain y in [-1, 1] -> World Z [DECK_D/2, -DECK_D/2] (so +y is up/back)
  return new THREE.Vector3(dx * (DECK_W * 0.46), DECK_H + height, -dy * (DECK_D * 0.46));
}

function addInkOutlinedPart(
  parent: THREE.Object3D,
  geo: THREE.BufferGeometry,
  colorHex: number,
  inkHex: number = 0x18213d,
  opts?: { metalness?: number; roughness?: number; transparent?: boolean; opacity?: number }
): THREE.Mesh {
  const mat = new THREE.MeshStandardMaterial({
    color: colorHex,
    roughness: opts?.roughness ?? 0.78,
    metalness: opts?.metalness ?? 0.08,
    transparent: opts?.transparent ?? false,
    opacity: opts?.opacity ?? 1.0
  });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.castShadow = !opts?.transparent;
  mesh.receiveShadow = true;

  const edges = new THREE.EdgesGeometry(geo, 22);
  const lineMat = new THREE.LineBasicMaterial({
    color: inkHex,
    transparent: true,
    opacity: opts?.transparent ? 0.45 : 0.92
  });
  const outline = new THREE.LineSegments(edges, lineMat);
  mesh.add(outline);
  parent.add(mesh);
  return mesh;
}

/**
 * Build detailed, ink-outlined 3D architectural/aerodynamic CFD models
 * matching learn-arduino-red.vercel.app/#board's tactile CAD diorama style.
 */
function rebuildPresetModel() {
  if (!scene) return;
  if (modelGroup) {
    scene.remove(modelGroup);
    modelGroup.traverse((obj: any) => {
      if (obj.geometry) obj.geometry.dispose();
      if (obj.material) {
        if (Array.isArray(obj.material)) obj.material.forEach((m: any) => m.dispose());
        else obj.material.dispose();
      }
    });
  }

  modelGroup = new THREE.Group();
  swayTarget = null;
  lidBeltMesh = null;
  const ink = props.isPaperTheme ? 0x18213d : 0x111010;

  // 1. Wind-Tunnel Baseplate Frame (Beveled Chamfered Hardware Board)
  const basePlate = addInkOutlinedPart(
    modelGroup,
    new THREE.BoxGeometry(DECK_W + 0.5, DECK_H, DECK_D + 0.5),
    props.isPaperTheme ? 0x3b4866 : 0x2c2929,
    ink,
    { roughness: 0.85 }
  );
  basePlate.position.set(0, DECK_H * 0.5, 0);

  // Corner brass mounting pads (signature #board hardware detail)
  const padGeo = new THREE.CylinderGeometry(0.32, 0.32, 0.12, 16);
  for (const [px, pz] of [[-1, -1], [1, -1], [-1, 1], [1, 1]]) {
    const pad = addInkOutlinedPart(modelGroup, padGeo, 0xc8a97e, ink, { metalness: 0.35, roughness: 0.45 });
    pad.position.set(px * (DECK_W * 0.46), DECK_H + 0.05, pz * (DECK_D * 0.45));
  }

  // Inlet Flow Direction Chevrons on Windward Edge (for non-cavity cases)
  if (props.preset !== 0) {
    for (let k = -1; k <= 1; k++) {
      const arrow = addInkOutlinedPart(modelGroup, new THREE.ConeGeometry(0.24, 0.65, 4), 0x1aa3a1, ink);
      arrow.rotation.z = -Math.PI / 2;
      arrow.position.set(-DECK_W * 0.46, DECK_H + 0.35, k * 2.2);
    }
  }

  // 2. Preset-Specific 3D Architectural / Aerodynamic Model
  const p = props.preset;
  if (p === 4) {
    // Fig. 01 — Simple House (Wind + FSI)
    const house = new THREE.Group();
    house.position.set(-1.3, DECK_H, 0.3);

    // Concrete foundation slab
    const plinth = addInkOutlinedPart(house, new THREE.BoxGeometry(3.4, 0.28, 3.6), 0xb8afa8, ink);
    plinth.position.y = 0.14;

    // Main walls
    const walls = addInkOutlinedPart(house, new THREE.BoxGeometry(2.9, 2.0, 3.1), 0xf0e7dc, ink);
    walls.position.y = 1.28;

    // Pitched triangular prism roof
    const roofShape = new THREE.Shape();
    roofShape.moveTo(-1.75, 0);
    roofShape.lineTo(1.75, 0);
    roofShape.lineTo(0, 1.35);
    roofShape.closePath();
    const roofGeo = new THREE.ExtrudeGeometry(roofShape, { depth: 3.5, bevelEnabled: false });
    roofGeo.center();
    const roof = addInkOutlinedPart(house, roofGeo, 0xa87462, ink);
    roof.position.set(0, 2.95, 0);

    // Chimney
    const chimney = addInkOutlinedPart(house, new THREE.BoxGeometry(0.45, 0.95, 0.45), 0x7a6a62, ink);
    chimney.position.set(0.65, 3.35, -0.75);

    // Front recessed door & side windows (high-contrast CAD detail)
    const door = addInkOutlinedPart(house, new THREE.BoxGeometry(0.12, 1.15, 0.68), 0x4b3d38, ink);
    door.position.set(-1.46, 0.86, 0);
    for (const wz of [-0.95, 0.95]) {
      const win = addInkOutlinedPart(house, new THREE.BoxGeometry(0.1, 0.65, 0.62), 0x5c89a6, ink);
      win.position.set(-1.46, 1.35, wz);
    }
    for (const wx of [-0.65, 0.65]) {
      const winS = addInkOutlinedPart(house, new THREE.BoxGeometry(0.62, 0.65, 0.1), 0x5c89a6, ink);
      winS.position.set(wx, 1.35, 1.56);
    }

    modelGroup.add(house);
    swayTarget = house;
  } else if (p === 3) {
    // Fig. 02 — 20m Glass Tower (FSI)
    const tower = new THREE.Group();
    tower.position.set(-1.5, DECK_H, 0);

    const podium = addInkOutlinedPart(tower, new THREE.BoxGeometry(2.6, 0.45, 2.6), 0x9b928b, ink);
    podium.position.y = 0.225;

    const core = addInkOutlinedPart(tower, new THREE.BoxGeometry(1.75, 4.9, 1.75), 0x5d8299, ink, { roughness: 0.35, metalness: 0.28 });
    core.position.y = 2.9;

    // Horizontal floor slab bands (gives architectural scale)
    for (let fl = 1; fl <= 6; fl++) {
      const band = addInkOutlinedPart(tower, new THREE.BoxGeometry(1.86, 0.1, 1.86), 0xe2dad2, ink);
      band.position.y = 0.5 + fl * 0.72;
    }

    // Rooftop crown & spire
    const crown = addInkOutlinedPart(tower, new THREE.BoxGeometry(1.2, 0.35, 1.2), 0x3a3838, ink);
    crown.position.y = 5.52;
    const spire = addInkOutlinedPart(tower, new THREE.CylinderGeometry(0.05, 0.1, 1.1, 8), 0xa89080, ink);
    spire.position.y = 6.2;

    modelGroup.add(tower);
    swayTarget = tower;
  } else if (p === 1) {
    // Fig. 03 — Cylinder Vortex Shedding
    const cylGroup = new THREE.Group();
    cylGroup.position.set(-1.6, DECK_H, 0);
    const flange = addInkOutlinedPart(cylGroup, new THREE.CylinderGeometry(1.45, 1.55, 0.22, 24), 0x7d7670, ink);
    flange.position.y = 0.11;
    const body = addInkOutlinedPart(cylGroup, new THREE.CylinderGeometry(1.1, 1.1, 3.2, 28), 0xd4c8bc, ink, { roughness: 0.55 });
    body.position.y = 1.82;
    const cap = addInkOutlinedPart(cylGroup, new THREE.CylinderGeometry(1.16, 1.16, 0.16, 28), 0xa89080, ink);
    cap.position.y = 3.48;
    modelGroup.add(cylGroup);
  } else if (p === 5) {
    // Fig. 04 — NACA 0012 Airfoil Section
    const wingGroup = new THREE.Group();
    wingGroup.position.set(-0.6, DECK_H + 1.4, 0);
    const shape = new THREE.Shape();
    const chord = 4.6;
    const pts = 28;
    for (let i = 0; i <= pts; i++) {
      const x = i / pts;
      const yt = 5 * 0.14 * (0.2969 * Math.sqrt(x) - 0.126 * x - 0.3516 * x * x + 0.2843 * x * x * x - 0.1015 * Math.pow(x, 4));
      const px = (x - 0.45) * chord;
      const py = yt * chord;
      if (i === 0) shape.moveTo(px, py);
      else shape.lineTo(px, py);
    }
    for (let i = pts; i >= 0; i--) {
      const x = i / pts;
      const yt = 5 * 0.14 * (0.2969 * Math.sqrt(x) - 0.126 * x - 0.3516 * x * x + 0.2843 * x * x * x - 0.1015 * Math.pow(x, 4));
      shape.lineTo((x - 0.45) * chord, -yt * chord);
    }
    shape.closePath();
    const wingGeo = new THREE.ExtrudeGeometry(shape, { depth: 4.8, bevelEnabled: false });
    wingGeo.center();
    const wing = addInkOutlinedPart(wingGroup, wingGeo, 0xd8cfc6, ink, { roughness: 0.5 });
    wing.rotation.z = -0.14; // 8 deg Angle of Attack
    // Mounting sting
    const sting = addInkOutlinedPart(wingGroup, new THREE.CylinderGeometry(0.18, 0.24, 1.4, 12), 0x5c5754, ink);
    sting.position.set(0, -0.7, 0);
    modelGroup.add(wingGroup);
  } else if (p === 2) {
    // Fig. 05 — Venturi Nozzle (Cutaway Upper/Lower Constriction Walls)
    const ventGroup = new THREE.Group();
    ventGroup.position.set(0, DECK_H, 0);
    for (const side of [-1, 1]) {
      const wallShape = new THREE.Shape();
      wallShape.moveTo(-5.8, 0);
      wallShape.lineTo(5.8, 0);
      wallShape.lineTo(5.8, 1.0);
      wallShape.quadraticCurveTo(0, 3.1, -5.8, 1.0);
      wallShape.closePath();
      const wallGeo = new THREE.ExtrudeGeometry(wallShape, { depth: 2.2, bevelEnabled: false });
      wallGeo.rotateX(Math.PI / 2);
      const wall = addInkOutlinedPart(ventGroup, wallGeo, 0xc7bdb3, ink, { transparent: true, opacity: 0.85 });
      wall.scale.z = side;
      wall.position.set(0, 2.2, side * 4.9);
    }
    modelGroup.add(ventGroup);
  } else {
    // Fig. 06 — Lid-Driven Cavity (Cutaway Acrylic Box + Moving Top Belt)
    const cav = new THREE.Group();
    cav.position.set(0, DECK_H, 0);
    const walls = addInkOutlinedPart(cav, new THREE.BoxGeometry(9.6, 2.6, 8.2), 0xdbe6ed, ink, { transparent: true, opacity: 0.24 });
    walls.position.y = 1.3;
    const belt = addInkOutlinedPart(cav, new THREE.BoxGeometry(9.8, 0.26, 2.2), 0xa89080, ink);
    belt.position.set(0, 2.75, -3.0);
    lidBeltMesh = belt;
    modelGroup.add(cav);
  }

  scene.add(modelGroup);
}

// Color lookup matching ParaView presets
function sampleColorRGB(t: number, preset: string): [number, number, number] {
  const c = Math.max(0, Math.min(1, t));
  if (preset === 'viridis') {
    const r = Math.round(255 * (0.267 + 0.726 * Math.pow(c, 2.1)));
    const g = Math.round(255 * (0.004 + 0.902 * Math.pow(c, 0.85)));
    const b = Math.round(255 * (0.329 + 0.35 * Math.sin(c * Math.PI) - 0.18 * c));
    return [r, g, b];
  }
  if (preset === 'plasma') {
    const r = Math.round(255 * Math.min(1, 0.05 + 1.2 * c));
    const g = Math.round(255 * Math.pow(c, 1.7));
    const b = Math.round(255 * Math.max(0.12, 0.65 - 0.55 * c));
    return [r, g, b];
  }
  if (preset === 'rainbow' || preset === 'jet') {
    const r = Math.round(255 * Math.max(0, Math.min(1, 1.5 - Math.abs(4 * c - 3))));
    const g = Math.round(255 * Math.max(0, Math.min(1, 1.5 - Math.abs(4 * c - 2))));
    const b = Math.round(255 * Math.max(0, Math.min(1, 1.5 - Math.abs(4 * c - 1))));
    return [r, g, b];
  }
  // ParaView Cool-to-Warm (default)
  if (c < 0.5) {
    const k = c * 2;
    return [
      Math.round(59 + (221 - 59) * k),
      Math.round(76 + (221 - 76) * k),
      Math.round(192 + (221 - 192) * k)
    ];
  }
  const k = (c - 0.5) * 2;
  return [
    Math.round(221 + (180 - 221) * k),
    Math.round(221 + (4 - 221) * k),
    Math.round(221 + (38 - 221) * k)
  ];
}

function updateDeckScalarTexture() {
  const eng = props.engine;
  if (!eng || !deckCanvas || !deckCtx || !deckTexture) return;
  const { nx, ny, mask } = eng;
  if (deckCanvas.width !== nx || deckCanvas.height !== ny) {
    deckCanvas.width = nx;
    deckCanvas.height = ny;
  }

  let fieldArr: Float32Array = eng.speed;
  if (props.fieldKey === 'pressure') fieldArr = eng.p;
  else if (props.fieldKey === 'vorticity') fieldArr = eng.vorticity;
  else if (props.fieldKey === 'building_stress_MPa') fieldArr = eng.stress;

  let minV = Infinity, maxV = -Infinity;
  for (let i = 0; i < fieldArr.length; i++) {
    if (fieldArr[i] < minV) minV = fieldArr[i];
    if (fieldArr[i] > maxV) maxV = fieldArr[i];
  }
  const span = Math.max(1e-6, maxV - minV);
  const img = deckCtx.createImageData(nx, ny);
  for (let j = 0; j < ny; j++) {
    for (let i = 0; i < nx; i++) {
      const id = j * nx + i;
      const py = ny - 1 - j;
      const idx = (py * nx + i) * 4;
      if (mask[id] === 1 && props.fieldKey !== 'building_stress_MPa') {
        img.data[idx] = 58;
        img.data[idx + 1] = 56;
        img.data[idx + 2] = 56;
        img.data[idx + 3] = 220;
      } else {
        const t = (fieldArr[id] - minV) / span;
        const [r, g, b] = sampleColorRGB(t, props.colorMap);
        img.data[idx] = r;
        img.data[idx + 1] = g;
        img.data[idx + 2] = b;
        img.data[idx + 3] = Math.round(235 * props.opacity);
      }
    }
  }
  deckCtx.putImageData(img, 0, 0);
  deckTexture.needsUpdate = true;

  if (deckMesh) {
    deckMesh.visible = props.showSource;
    const m = deckMesh.material as THREE.MeshBasicMaterial;
    m.opacity = props.opacity;
    m.wireframe = props.representation === 'wireframe';
  }
  if (deckWireframe) {
    deckWireframe.visible = props.showSource && props.representation === 'surface_with_edges';
  }
}

function sampleFieldAt(dx: number, dy: number) {
  const eng = props.engine;
  if (!eng) return { u: 0.75, v: 0, spd: 0.75, p: 0, solid: false };
  const i = Math.max(0, Math.min(eng.nx - 1, Math.floor(((dx + 1) * 0.5) * (eng.nx - 1))));
  const j = Math.max(0, Math.min(eng.ny - 1, Math.floor(((dy + 1) * 0.5) * (eng.ny - 1))));
  const id = j * eng.nx + i;
  return {
    u: eng.u[id] || 0,
    v: eng.v[id] || 0,
    spd: eng.speed[id] || 0,
    p: eng.p[id] || 0,
    solid: eng.mask[id] === 1
  };
}

function projectToScreen(pos: THREE.Vector3): [number, number] | null {
  if (!camera || !stageRoot.value) return null;
  const w = vpSize.value.w;
  const h = vpSize.value.h;
  if (w <= 0 || h <= 0) return null;
  const p = pos.clone().project(camera);
  return [(p.x * 0.5 + 0.5) * w, (-p.y * 0.5 + 0.5) * h];
}

// Live Simulation-Driven Physics Extrema Pins (updates every WASM step!)
const projectedPins = computed(() => {
  void props.fieldRev;
  void viewRev.value;
  void vpSize.value;
  const eng = props.engine;
  const w = vpSize.value.w || 800;
  const h = vpSize.value.h || 520;
  const scale = Math.min(1, Math.max(0.55, w / 920));

  let maxSpd = -1, spdI = 10, spdJ = 20;
  let maxP = -Infinity, pI = 14, pJ = 20;
  let maxVort = -1, vortI = 26, vortJ = 20;
  let maxStress = -1, strI = 15, strJ = 10;
  let minP = Infinity, minPI = 24, minPJ = 20;

  if (eng) {
    const { nx, ny, speed, p, vorticity, stress, mask } = eng;
    for (let j = 2; j < ny - 2; j++) {
      for (let i = 2; i < nx - 2; i++) {
        const id = j * nx + i;
        if (mask[id] === 0) {
          if (speed[id] > maxSpd) { maxSpd = speed[id]; spdI = i; spdJ = j; }
          if (p[id] > maxP) { maxP = p[id]; pI = i; pJ = j; }
          if (p[id] < minP) { minP = p[id]; minPI = i; minPJ = j; }
          const aw = Math.abs(vorticity[id]);
          if (aw > maxVort) { maxVort = aw; vortI = i; vortJ = j; }
        }
        if (stress[id] > maxStress) { maxStress = stress[id]; strI = i; strJ = j; }
      }
    }
  }

  const gridToW = (i: number, j: number, zH: number) => {
    const nx = eng ? eng.nx : 41;
    const ny = eng ? eng.ny : 41;
    return domainToWorld((i / (nx - 1)) * 2 - 1, (j / (ny - 1)) * 2 - 1, zH);
  };

  const coStr = eng ? eng.maxCourant.toFixed(2) : '0.20';
  const dtStr = eng ? eng.dt.toFixed(4) : '0.0040';

  const defs = [
    {
      id: 'vel',
      pos: gridToW(spdI, spdJ, 1.35),
      ox: -78, oy: -54,
      label: 'VEL PEAK',
      shortVal: `${(maxSpd < 0 ? 1 : maxSpd).toFixed(2)} m/s`,
      title: 'LIVE PEAK VELOCITY CELL',
      desc: 'Tracks the fastest fluid cell in real time as airflow accelerates over the 3D geometry.',
      metric: `|U|_max = ${(maxSpd < 0 ? 1 : maxSpd).toFixed(3)} m/s · Co_max = ${coStr}`
    },
    {
      id: 'pres',
      pos: gridToW(pI, pJ, 1.75),
      ox: -76, oy: 48,
      label: 'STAGNATION',
      shortVal: `${(maxP === -Infinity ? 0 : maxP).toFixed(2)} Pa`,
      title: 'WINDWARD STAGNATION PRESSURE',
      desc: 'Tracks the live maximum static pressure where incoming air decelerates against the obstacle.',
      metric: `p_max = ${(maxP === -Infinity ? 0 : maxP).toFixed(4)} Pa · Re = ${props.reynolds}`
    },
    {
      id: 'vort',
      pos: gridToW(vortI, vortJ, 0.9),
      ox: 82, oy: -48,
      label: 'VORTEX CORE',
      shortVal: `${(maxVort < 0 ? 0 : maxVort).toFixed(1)} /s`,
      title: 'ACTIVE VORTEX CORE (MAX |ω|)',
      desc: 'Moves dynamically downstream with the strongest swirling wake eddy.',
      metric: `|ω|_max = ${(maxVort < 0 ? 0 : maxVort).toFixed(2)} 1/s · dt = ${dtStr} s`
    },
    eng?.fsiActive
      ? {
          id: 'fsi',
          pos: gridToW(strI, strJ, 2.2),
          ox: 78, oy: 52,
          label: 'MAX STRESS',
          shortVal: `${eng.maxStressMpa.toFixed(2)} MPa`,
          title: 'COUPLED FEA BUILDING STRESS',
          desc: 'Live Euler-Bernoulli Von Mises stress & lateral tip drift from fea_structure.wasm.',
          metric: `Stress: ${eng.maxStressMpa.toFixed(3)} MPa · Drift: ${eng.maxDispMm.toFixed(3)} mm`
        }
      : {
          id: 'lowp',
          pos: gridToW(minPI, minPJ, 0.7),
          ox: 78, oy: 52,
          label: 'LOW PRESSURE',
          shortVal: `${(minP === Infinity ? 0 : minP).toFixed(2)} Pa`,
          title: 'SUCTION / LOW-PRESSURE CORE',
          desc: 'Tracks the lowest static pressure zone driving lift or wake suction.',
          metric: `p_min = ${(minP === Infinity ? 0 : minP).toFixed(4)} Pa`
        }
  ];

  return defs.map((d) => {
    const sp = projectToScreen(d.pos);
    const ax = sp ? sp[0] : w * 0.5;
    const ay = sp ? sp[1] : h * 0.5;
    const dirX = ax < w * 0.48 ? -1 : 1;
    const lx = Math.max(92, Math.min(w - 92, ax + Math.abs(d.ox) * scale * dirX));
    const ly = Math.max(26, Math.min(h - 68, ay + d.oy * scale));
    const elbowX = ax + (lx - ax) * 0.52;
    return {
      ...d,
      ax,
      ay,
      lx,
      ly,
      alignRight: lx < ax,
      pathD: `M ${ax.toFixed(1)} ${ay.toFixed(1)} L ${elbowX.toFixed(1)} ${ly.toFixed(1)} L ${lx.toFixed(1)} ${ly.toFixed(1)}`
    };
  });
});

const selectedPin = computed(() => projectedPins.value.find((p) => p.id === selectedPinId.value) || null);

function togglePin(pin: { id: string; pos: THREE.Vector3 }) {
  selectedPinId.value = selectedPinId.value === pin.id ? null : pin.id;
  if (selectedPinId.value) {
    camState.targetLook.set(pin.pos.x * 0.35, 0.85, pin.pos.z * 0.35);
  } else {
    camState.targetLook.set(0, 0.7, 0);
  }
}

function onReSliderChange(e: Event) {
  const val = Number((e.target as HTMLInputElement).value);
  emit('update-reynolds', val);
}

// Camera Controls
function rotateAzimuth(delta: number) {
  camState.targetAz += delta;
}

function zoomBy(factor: number) {
  camState.targetZoom = Math.max(0.55, Math.min(2.6, camState.targetZoom * factor));
}

function resetIsoView() {
  camState.targetAz = -0.72;
  camState.targetEl = 0.58;
  camState.targetZoom = 1.05;
  camState.targetLook.set(0, 0.7, 0);
}

function setNamedView(view: '+X' | '-X' | '+Y' | '-Y' | '+Z' | 'iso') {
  if (view === 'iso') { resetIsoView(); return; }
  if (view === '+X') { camState.targetAz = 0; camState.targetEl = 0.08; }
  else if (view === '-X') { camState.targetAz = Math.PI; camState.targetEl = 0.08; }
  else if (view === '+Y') { camState.targetAz = -Math.PI / 2; camState.targetEl = 1.48; }
  else if (view === '-Y') { camState.targetAz = -Math.PI / 2; camState.targetEl = 0.12; }
  else if (view === '+Z') { camState.targetAz = -Math.PI / 2; camState.targetEl = 0.08; }
}

defineExpose({ setNamedView, resetIsoView });

// Pointer & Wheel Interaction
function onPointerDown(e: PointerEvent) {
  dragging = e.button === 2 || e.shiftKey ? 'pan' : 'orbit';
  lastPtr = { x: e.clientX, y: e.clientY };
}

function onPointerMove(e: PointerEvent) {
  const rect = stageRoot.value?.getBoundingClientRect();
  if (dragging) {
    const dx = e.clientX - lastPtr.x;
    const dy = e.clientY - lastPtr.y;
    lastPtr = { x: e.clientX, y: e.clientY };
    if (dragging === 'orbit') {
      camState.targetAz -= dx * 0.008;
      camState.targetEl = Math.max(0.15, Math.min(1.42, camState.targetEl + dy * 0.007));
    } else {
      camState.targetLook.x -= dx * 0.015;
      camState.targetLook.z -= dy * 0.015;
    }
    return;
  }

  if (rect && props.engine) {
    const nx = ((e.clientX - rect.left) / Math.max(1, rect.width)) * 2 - 1;
    const ny = 1 - ((e.clientY - rect.top) / Math.max(1, rect.height)) * 2;
    const s = sampleFieldAt(nx * 0.9, ny * 0.9);
    emit('probe-change', { x: nx, y: ny, val: s.spd });
    hoverReadout.value = {
      visible: true,
      x: Math.min(rect.width - 175, Math.max(12, e.clientX - rect.left + 14)),
      y: Math.min(rect.height - 56, Math.max(12, e.clientY - rect.top - 10)),
      title: s.solid ? 'SOLID STRUCTURE' : `|U| ${s.spd.toFixed(2)} m/s`,
      detail: `p = ${s.p.toFixed(3)} Pa · Re ${props.reynolds}`
    };
  }
}

function onPointerUp() {
  dragging = null;
}

function onPointerLeave() {
  dragging = null;
  hoverReadout.value.visible = false;
}

function onWheel(e: WheelEvent) {
  zoomBy(e.deltaY > 0 ? 0.92 : 1.09);
}

function onKeyDown(e: KeyboardEvent) {
  const tag = (e.target as HTMLElement)?.tagName;
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
  const k = e.key.toLowerCase();
  if (k === 'q') rotateAzimuth(-Math.PI / 8);
  else if (k === 'e') rotateAzimuth(Math.PI / 8);
  else if (k === 'r') resetIsoView();
  else if (k === 'f') showFlow.value = !showFlow.value;
  else if (k === 'l') showCallouts.value = !showCallouts.value;
  else if (k === '+' || k === '=') zoomBy(1.15);
  else if (k === '-') zoomBy(0.86);
}

function updateThemeColors() {
  if (!scene || !groundGridMat || !shadowPlaneMat) return;
  const bg = props.isPaperTheme ? 0xdfd7ce : 0x1a1818;
  scene.background = new THREE.Color(bg);
  groundGridMat.uniforms.color.value.set(props.isPaperTheme ? '#bda992' : '#3a3838');
  shadowPlaneMat.opacity = props.isPaperTheme ? 0.24 : 0.42;
}

function initThreeStage() {
  const canvas = webglCanvas.value;
  const root = stageRoot.value;
  if (!canvas || !root) return;

  const rect = root.getBoundingClientRect();
  const w = Math.max(300, rect.width);
  const h = Math.max(240, rect.height);
  vpSize.value = { w, h };

  renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setSize(w, h, false);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.outputColorSpace = THREE.SRGBColorSpace;

  scene = new THREE.Scene();
  scene.background = new THREE.Color(props.isPaperTheme ? 0xdfd7ce : 0x1a1818);

  const aspect = w / h;
  const frustum = 9.8;
  camera = new THREE.OrthographicCamera(-frustum * aspect, frustum * aspect, frustum, -frustum, 0.1, 200);

  // Warm #board Lighting + Soft Ground Shadow
  const hemi = new THREE.HemisphereLight(0xfffaf2, 0xc2ae90, 1.05);
  scene.add(hemi);

  const keyLight = new THREE.DirectionalLight(0xfff6ea, 1.25);
  keyLight.position.set(-14, 24, 15);
  keyLight.castShadow = true;
  keyLight.shadow.mapSize.set(2048, 2048);
  keyLight.shadow.camera.left = -14;
  keyLight.shadow.camera.right = 14;
  keyLight.shadow.camera.top = 14;
  keyLight.shadow.camera.bottom = -14;
  keyLight.shadow.bias = -0.0005;
  scene.add(keyLight);

  const rimLight = new THREE.DirectionalLight(0xd9e8f5, 0.45);
  rimLight.position.set(14, 10, -12);
  scene.add(rimLight);

  // World-space fading isometric drafting grid (#board Vs() shader)
  groundGridMat = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    uniforms: {
      color: { value: new THREE.Color(props.isPaperTheme ? '#bda992' : '#3a3838') },
      cell: { value: 1.4 },
      inner: { value: 9.5 },
      outer: { value: 23.0 }
    },
    vertexShader: `
      varying vec2 vPos;
      void main() {
        vec4 wp = modelMatrix * vec4(position, 1.0);
        vPos = wp.xz;
        gl_Position = projectionMatrix * viewMatrix * wp;
      }
    `,
    fragmentShader: `
      uniform vec3 color;
      uniform float cell;
      uniform float inner;
      uniform float outer;
      varying vec2 vPos;
      void main() {
        vec2 g = abs(fract(vPos / cell - 0.5) - 0.5) / fwidth(vPos / cell);
        float line = 1.0 - min(min(g.x, g.y), 1.0);
        float fade = 1.0 - smoothstep(inner, outer, length(vPos));
        gl_FragColor = vec4(color, line * fade * 0.85);
      }
    `
  });
  const gridPlane = new THREE.Mesh(new THREE.PlaneGeometry(80, 80), groundGridMat);
  gridPlane.rotation.x = -Math.PI / 2;
  gridPlane.position.y = -0.02;
  scene.add(gridPlane);

  // Soft cast shadow catcher
  shadowPlaneMat = new THREE.ShadowMaterial({ color: 0x6b4c2e, opacity: props.isPaperTheme ? 0.24 : 0.42 });
  const shadowPlane = new THREE.Mesh(new THREE.PlaneGeometry(80, 80), shadowPlaneMat);
  shadowPlane.rotation.x = -Math.PI / 2;
  shadowPlane.position.y = -0.01;
  shadowPlane.receiveShadow = true;
  scene.add(shadowPlane);

  // Live CFD Scalar Contour Deck Texture
  deckCanvas = document.createElement('canvas');
  deckCanvas.width = 41;
  deckCanvas.height = 41;
  deckCtx = deckCanvas.getContext('2d');
  deckTexture = new THREE.CanvasTexture(deckCanvas);
  deckTexture.colorSpace = THREE.SRGBColorSpace;
  deckTexture.magFilter = THREE.LinearFilter;
  deckTexture.minFilter = THREE.LinearFilter;

  const deckGeo = new THREE.PlaneGeometry(DECK_W * 0.92, DECK_D * 0.92, 40, 40);
  const deckMat = new THREE.MeshBasicMaterial({
    map: deckTexture,
    transparent: true,
    opacity: props.opacity
  });
  deckMesh = new THREE.Mesh(deckGeo, deckMat);
  deckMesh.rotation.x = -Math.PI / 2;
  deckMesh.position.y = DECK_H + 0.015;
  scene.add(deckMesh);

  deckWireframe = new THREE.LineSegments(
    new THREE.WireframeGeometry(deckGeo),
    new THREE.LineBasicMaterial({ color: 0x18213d, transparent: true, opacity: 0.22 })
  );
  deckWireframe.rotation.x = -Math.PI / 2;
  deckWireframe.position.y = DECK_H + 0.02;
  deckWireframe.visible = false;
  scene.add(deckWireframe);

  // 3D Flow Beads (#board dark-rimmed cream spheres advected by live WASM U,V)
  beadRimMesh = new THREE.InstancedMesh(
    new THREE.SphereGeometry(0.145, 10, 10),
    new THREE.MeshBasicMaterial({ color: 0x18213d }),
    BEAD_COUNT
  );
  beadCoreMesh = new THREE.InstancedMesh(
    new THREE.SphereGeometry(0.105, 10, 10),
    new THREE.MeshBasicMaterial({ color: 0xfff6d6 }),
    BEAD_COUNT
  );
  scene.add(beadRimMesh);
  scene.add(beadCoreMesh);

  // Free-Moving 3D Lagrangian Probe Sphere + Ribbon Trail
  freeProbeMesh = new THREE.Group();
  const outer = new THREE.Mesh(
    new THREE.SphereGeometry(0.24, 16, 16),
    new THREE.MeshBasicMaterial({ color: 0x1aa3a1, transparent: true, opacity: 0.35 })
  );
  const inner = new THREE.Mesh(
    new THREE.SphereGeometry(0.14, 16, 16),
    new THREE.MeshBasicMaterial({ color: 0xffffff })
  );
  freeProbeMesh.add(outer, inner);
  scene.add(freeProbeMesh);

  const trailGeo = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3()]);
  freeTrailLine = new THREE.Line(
    trailGeo,
    new THREE.LineBasicMaterial({ color: 0x1aa3a1, transparent: true, opacity: 0.85 })
  );
  scene.add(freeTrailLine);

  rebuildPresetModel();
  updateDeckScalarTexture();

  let frameTick = 0;
  const animate = (now: number) => {
    rafId = requestAnimationFrame(animate);
    if (!renderer || !scene || !camera) return;

    // Smooth camera damping
    const prevAz = camState.azimuth;
    const prevEl = camState.elevation;
    const prevZ = camState.zoom;
    camState.azimuth += (camState.targetAz - camState.azimuth) * 0.14;
    camState.elevation += (camState.targetEl - camState.elevation) * 0.14;
    camState.zoom += (camState.targetZoom - camState.zoom) * 0.14;
    camState.target.lerp(camState.targetLook, 0.14);

    const dist = 28;
    camera.position.set(
      camState.target.x + dist * Math.cos(camState.elevation) * Math.sin(camState.azimuth),
      camState.target.y + dist * Math.sin(camState.elevation),
      camState.target.z + dist * Math.cos(camState.elevation) * Math.cos(camState.azimuth)
    );
    camera.lookAt(camState.target);
    camera.zoom = camState.zoom;
    camera.updateProjectionMatrix();

    if (
      Math.abs(prevAz - camState.azimuth) > 1e-4 ||
      Math.abs(prevEl - camState.elevation) > 1e-4 ||
      Math.abs(prevZ - camState.zoom) > 1e-4
    ) {
      viewRev.value++;
    }

    // Subtle live FSI structural sway proportional to real fea_structure.wasm tip drift
    if (swayTarget && props.engine) {
      const drift = Math.min(0.12, props.engine.maxDispMm * 0.015 + (props.engine.maxCourant > 0.85 ? 0.07 : 0.008));
      swayTarget.rotation.z = -drift * (0.65 + 0.35 * Math.sin(now * 0.006));
    }
    if (lidBeltMesh) {
      lidBeltMesh.position.x = Math.sin(now * 0.004) * 0.35;
    }

    // Advect 3D Flow Beads through live WASM (u, v) field
    if (beadCoreMesh && beadRimMesh) {
      beadCoreMesh.visible = showFlow.value;
      beadRimMesh.visible = showFlow.value;
      if (showFlow.value) {
        for (let i = 0; i < BEAD_COUNT; i++) {
          const b = beads[i];
          b.life += 1;
          const s = sampleFieldAt(b.x, b.y);
          const vx = props.preset === 0 ? s.u : (Math.abs(s.u) + Math.abs(s.v) > 0.02 ? s.u : 0.7);
          const vy = s.v;
          b.x += vx * 0.015;
          b.y += vy * 0.015;

          if (s.solid || b.x > 0.98 || b.x < -0.99 || b.y > 0.98 || b.y < -0.98 || b.life > b.maxLife) {
            b.x = props.preset === 0 ? (Math.random() * 1.6 - 0.8) : -0.96;
            b.y = Math.random() * 1.7 - 0.85;
            b.z = 0.28 + Math.random() * (props.preset === 3 ? 2.6 : 1.5);
            b.life = 0;
          }

          // Lift beads smoothly over obstacles for crisp 3D aerodynamic flow
          const overObstacleBoost = (props.preset === 4 || props.preset === 5) && Math.abs(b.x + 0.18) < 0.36 ? 0.85 : 0;
          const wp = domainToWorld(b.x, b.y, b.z + overObstacleBoost);
          dummyObj.position.copy(wp);
          const scale = 0.75 + Math.min(0.6, s.spd * 0.35);
          dummyObj.scale.setScalar(scale);
          dummyObj.updateMatrix();
          beadRimMesh.setMatrixAt(i, dummyObj.matrix);
          beadCoreMesh.setMatrixAt(i, dummyObj.matrix);
        }
        beadRimMesh.instanceMatrix.needsUpdate = true;
        beadCoreMesh.instanceMatrix.needsUpdate = true;
      }
    }

    // Advect Free-Moving 3D Lagrangian Probe
    if (freeProbeMesh && freeTrailLine) {
      freeProbeMesh.visible = showFlow.value;
      freeTrailLine.visible = showFlow.value;
      if (showFlow.value) {
        const fs = sampleFieldAt(freeProbe.x, freeProbe.y);
        const fvx = props.preset === 0 ? (Math.abs(fs.u) > 0.01 ? fs.u : 0.4) : (Math.abs(fs.u) + Math.abs(fs.v) > 0.02 ? fs.u : 0.65);
        freeProbe.x += fvx * 0.013;
        freeProbe.y += fs.v * 0.013;
        if (fs.solid || freeProbe.x > 0.96 || freeProbe.x < -0.98 || freeProbe.y > 0.95 || freeProbe.y < -0.95) {
          freeProbe.x = props.preset === 0 ? -0.55 : -0.94;
          freeProbe.y = props.preset === 0 ? 0.65 : (Math.random() * 1.1 - 0.55);
          freeProbe.trail = [];
        }
        const fwp = domainToWorld(freeProbe.x, freeProbe.y, 1.15);
        freeProbeMesh.position.copy(fwp);
        freeProbe.trail.push(fwp.clone());
        if (freeProbe.trail.length > 28) freeProbe.trail.shift();
        if (freeProbe.trail.length > 1) {
          freeTrailLine.geometry.dispose();
          freeTrailLine.geometry = new THREE.BufferGeometry().setFromPoints(freeProbe.trail);
        }
        if (frameTick % 2 === 0) {
          const sp = projectToScreen(fwp);
          if (sp) {
            freeProbeScreen.value = {
              visible: true,
              x: Math.max(12, Math.min(vpSize.value.w - 130, sp[0] + 12)),
              y: Math.max(20, Math.min(vpSize.value.h - 60, sp[1] - 14)),
              speed: fs.spd.toFixed(2)
            };
          }
        }
      }
    }

    frameTick++;
    renderer.render(scene, camera);
  };
  rafId = requestAnimationFrame(animate);
}

watch(() => props.preset, () => {
  rebuildPresetModel();
  updateDeckScalarTexture();
});

watch(() => [props.fieldRev, props.colorMap, props.fieldKey, props.representation, props.opacity, props.showSource], () => {
  updateDeckScalarTexture();
});

watch(() => props.isPaperTheme, () => {
  updateThemeColors();
  rebuildPresetModel();
});

onMounted(() => {
  initThreeStage();
  window.addEventListener('keydown', onKeyDown);
  if (stageRoot.value && typeof ResizeObserver !== 'undefined') {
    resizeObs = new ResizeObserver(() => {
      if (!stageRoot.value || !renderer || !camera) return;
      const rect = stageRoot.value.getBoundingClientRect();
      const w = Math.max(300, rect.width);
      const h = Math.max(240, rect.height);
      vpSize.value = { w, h };
      const aspect = w / h;
      const frustum = 9.8;
      camera.left = -frustum * aspect;
      camera.right = frustum * aspect;
      camera.top = frustum;
      camera.bottom = -frustum;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h, false);
      viewRev.value++;
    });
    resizeObs.observe(stageRoot.value);
  }
});

onBeforeUnmount(() => {
  if (rafId !== null) cancelAnimationFrame(rafId);
  window.removeEventListener('keydown', onKeyDown);
  if (resizeObs) resizeObs.disconnect();
  if (renderer) renderer.dispose();
});
</script>

<style scoped>
.board-stage-root {
  position: absolute;
  inset: 0;
  overflow: hidden;
  user-select: none;
  touch-action: none;
  cursor: grab;
}

.board-stage-root:active {
  cursor: grabbing;
}

.board-webgl-canvas {
  width: 100%;
  height: 100%;
  display: block;
}

.board-leaders-svg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 10;
}

.board-leader-path {
  fill: none;
  stroke: #5c5652;
  stroke-width: 1.5;
  stroke-dasharray: 3 3;
  transition: stroke 0.15s ease, stroke-width 0.15s ease;
}

.board-leader-g.hot .board-leader-path {
  stroke: #1aa3a1;
  stroke-width: 2.2;
  stroke-dasharray: none;
}

.board-dot-halo {
  fill: rgba(26, 163, 161, 0.24);
}

.board-dot-ring {
  fill: #1aa3a1;
}

.board-dot-core {
  fill: #ffffff;
}

.board-tags-layer {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 15;
}

.board-tag-pill {
  position: absolute;
  pointer-events: auto;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px 5px 7px;
  border-radius: 7px;
  background: rgba(250, 244, 236, 0.96);
  color: #18213d;
  border: 1.5px solid #c9beb0;
  font-family: "Barlow Semi Condensed", "Barlow", sans-serif;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.45px;
  cursor: pointer;
  white-space: nowrap;
  box-shadow: 0 3px 10px rgba(24, 33, 61, 0.12);
  transition: background 0.14s ease, border-color 0.14s ease, color 0.14s ease;
}

.board-tag-pill:hover,
.board-tag-pill.hot,
.board-tag-pill.active {
  background: #18213d;
  border-color: #18213d;
  color: #faf4ec;
}

.tag-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #1aa3a1;
  border: 2px solid #ffffff;
  flex-shrink: 0;
}

.tag-val {
  font-family: "JetBrains Mono", monospace;
  font-size: 9.5px;
  font-weight: 600;
  opacity: 0.78;
  border-left: 1px solid currentColor;
  padding-left: 6px;
}

.board-free-probe-tag {
  position: absolute;
  pointer-events: none;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 8px;
  border-radius: 999px;
  background: rgba(24, 33, 61, 0.88);
  color: #faf4ec;
  font-family: "JetBrains Mono", monospace;
  font-size: 9.5px;
  font-weight: 700;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
}

.free-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #1aa3a1;
}

.board-inspector-card {
  position: absolute;
  left: 50%;
  bottom: 66px;
  transform: translateX(-50%);
  pointer-events: auto;
  width: 320px;
  background: rgba(249, 242, 229, 0.97);
  color: #18213d;
  border: 1.5px solid #18213d;
  border-radius: 10px;
  padding: 11px 14px;
  box-shadow: 0 8px 24px rgba(24, 33, 61, 0.18);
}

.insp-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  margin-bottom: 4px;
}

.insp-close {
  border: none;
  background: transparent;
  font-size: 16px;
  cursor: pointer;
  color: #696d74;
}

.insp-desc {
  font-size: 11.5px;
  line-height: 1.45;
  color: #4f535b;
  margin: 0 0 6px 0;
}

.insp-metric {
  font-family: "JetBrains Mono", monospace;
  font-size: 10.5px;
  font-weight: 700;
  color: #1aa3a1;
  border-top: 1px solid #d9cebf;
  padding-top: 5px;
}

.insp-controls {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #c9beb0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.insp-slider {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  font-size: 11px;
}

.insp-slider input {
  flex: 1;
  accent-color: #1aa3a1;
}

.insp-btns {
  display: flex;
  gap: 6px;
}

.insp-btn {
  flex: 1;
  padding: 4px 6px;
  border-radius: 5px;
  border: 1px solid #c9beb0;
  background: #efe3d1;
  color: #18213d;
  font-size: 10.5px;
  font-weight: 700;
  cursor: pointer;
}

.insp-btn:hover {
  background: #1aa3a1;
  border-color: #1aa3a1;
  color: #ffffff;
}

.board-hover-tip {
  position: absolute;
  pointer-events: none;
  z-index: 22;
  padding: 5px 9px;
  border-radius: 6px;
  background: rgba(24, 33, 61, 0.92);
  color: #faf4ec;
  font-family: "JetBrains Mono", monospace;
  font-size: 10px;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.board-hover-tip span {
  opacity: 0.82;
  font-size: 9.5px;
}

/* Exact #board Floating Bottom Viewbar */
.board-viewbar {
  position: absolute;
  left: 50%;
  bottom: 14px;
  transform: translateX(-50%);
  z-index: 20;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 10px;
  border-radius: 12px;
  background: rgba(249, 242, 229, 0.94);
  border: 1px solid #cec0ad;
  box-shadow: 0 4px 16px rgba(24, 33, 61, 0.12);
}

.bvb-btn {
  width: 30px;
  height: 28px;
  border: none;
  border-radius: 7px;
  background: transparent;
  color: #18213d;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.14s ease, color 0.14s ease;
}

.bvb-btn svg {
  width: 17px;
  height: 17px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.85;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.bvb-btn .svg-fill-accent {
  fill: #d9534f;
  stroke: none;
}

.bvb-btn .svg-fill-muted {
  fill: #9aa0a8;
  stroke: none;
}

.bvb-btn .svg-fill-current {
  fill: currentColor;
  stroke: none;
}

.bvb-btn:hover {
  background: rgba(24, 33, 61, 0.08);
}

.bvb-btn.toggle.active {
  background: rgba(26, 163, 161, 0.22);
  color: #127876;
}

.bvb-sep {
  width: 1px;
  height: 18px;
  background: #cec0ad;
  margin: 0 2px;
}
</style>
