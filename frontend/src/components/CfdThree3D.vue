<template>
  <div class="three-viewport-container" ref="containerRef">
    <!-- Viewport Header Label -->
    <div class="viewport-title-bar">
      <span class="viewport-title">Three.js CFD Viewport</span>
    </div>

    <!-- Interactive HUD Toolbar Overlay -->
    <div class="viewport-hud-toolbar">
      <button
        class="hud-tool-btn"
        :class="{ active: showPlume }"
        @click="showPlume = !showPlume"
        title="Toggle Volumetric Thermal Plume"
      >
        💨 Plume
      </button>
      <button
        class="hud-tool-btn"
        :class="{ active: showCutplanes }"
        @click="showCutplanes = !showCutplanes"
        title="Toggle Orthogonal Sliced Cutplanes"
      >
        📐 Cut-Planes
      </button>
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
        🎯 Reset View
      </button>
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
          <span class="probe-val-title">Values</span>
          <span class="probe-val-num">{{ probe.value.toFixed(2) }}</span>
        </div>
        <div class="probe-hud-tag">
          <span>Hever Flow probe HUD</span>
        </div>
      </div>
      <div class="probe-pointer-line"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue';
import * as THREE from 'three';
import type { SimulationStepData, SimulationParams } from '../types/cfd';

const props = defineProps<{
  data: SimulationStepData | null;
  params: SimulationParams;
}>();

const canvasMountRef = ref<HTMLDivElement | null>(null);

const showPlume = ref(true);
const showCutplanes = ref(true);
const isAutoRotate = ref(false);

// Flow Probe Tooltip State
const probe = ref({
  active: false,
  screenX: 0,
  screenY: 0,
  value: 0.22,
  u: 0.22,
  v: 0.04,
  w: 0.01,
  t: 312.4
});

let scene: THREE.Scene;
let camera: THREE.PerspectiveCamera;
let renderer: THREE.WebGLRenderer;
let animId: number;

let plumeGroup: THREE.Group;
let cutplanesGroup: THREE.Group;
let particlesMesh: THREE.Points;
let cutplaneXY: THREE.Mesh;
let cutplaneXZ: THREE.Mesh;
let probeMarker: THREE.Mesh;

// Mouse drag state
let isDragging = false;
let previousMousePosition = { x: 0, y: 0 };
let targetRotationX = 0.35;
let targetRotationY = -0.65;
let raycaster = new THREE.Raycaster();
let mouse = new THREE.Vector2();

function initThree() {
  if (!canvasMountRef.value) return;

  const width = canvasMountRef.value.clientWidth || 800;
  const height = canvasMountRef.value.clientHeight || 600;

  // 1. Scene
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0f131a); // oklch(20.5% 0 0)

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
  const ambient = new THREE.AmbientLight(0xffffff, 0.8);
  scene.add(ambient);

  const cyanLight = new THREE.DirectionalLight(0x00d2ff, 1.5);
  cyanLight.position.set(5, 5, 8);
  scene.add(cyanLight);

  const magentaLight = new THREE.DirectionalLight(0xa855f7, 1.2);
  magentaLight.position.set(-5, -5, 3);
  scene.add(magentaLight);

  // 5. Groups
  plumeGroup = new THREE.Group();
  cutplanesGroup = new THREE.Group();
  scene.add(plumeGroup);
  scene.add(cutplanesGroup);

  // 6. Build Volumetric Plume and Cut-planes
  buildVolumetricPlume();
  buildCutplanes();
  buildProbeMarker();

  // 7. Event Listeners
  const dom = renderer.domElement;
  dom.addEventListener('mousedown', onMouseDown);
  dom.addEventListener('mousemove', onMouseMove);
  window.addEventListener('mouseup', onMouseUp);
  dom.addEventListener('wheel', onWheel, { passive: true });

  animate();
}

function buildVolumetricPlume() {
  const particleCount = 14000;
  const geometry = new THREE.BufferGeometry();
  const positions = new Float32Array(particleCount * 3);
  const colors = new Float32Array(particleCount * 3);
  const sizes = new Float32Array(particleCount);

  const iris = props.params.studioParams?.irisPurple ?? 0.182;
  const butterscotch = props.params.studioParams?.butterscotchCore ?? 84.899;
  const coreIntensity = Math.min(1.0, butterscotch / 100.0);

  for (let i = 0; i < particleCount; i++) {
    // Jet profile expanding along X axis
    const t = Math.random(); // 0 to 1 along plume length
    const x = -2.2 + t * 4.5;
    
    // Spread increases with x
    const spread = (0.2 + t * 0.95) * (0.8 + iris * 1.5);
    const angle = Math.random() * Math.PI * 2;
    const r = Math.pow(Math.random(), 0.7) * spread;

    // Plume core with upward buoyancy lift
    const y = Math.cos(angle) * r;
    const z = Math.sin(angle) * r * 0.85 + Math.pow(t, 1.4) * 0.45;

    positions[i * 3] = x;
    positions[i * 3 + 1] = y;
    positions[i * 3 + 2] = z;

    // Color gradient: Core (Butterscotch Gold #fbbf24) -> Mid (Cyan #06b6d4) -> Outer/Tail (Sapphire #3b82f6)
    const distFromCore = (r / spread);
    if (distFromCore < 0.35 && t < 0.6) {
      // Radiant Golden Core influenced by Butterscotch core setting
      colors[i * 3] = 0.98 * coreIntensity;     // R
      colors[i * 3 + 1] = 0.75 * coreIntensity; // G
      colors[i * 3 + 2] = 0.14;                 // B
    } else if (distFromCore < 0.7) {
      // Luminous Cyan Mid-layer
      colors[i * 3] = 0.05;
      colors[i * 3 + 1] = 0.75;
      colors[i * 3 + 2] = 0.95;
    } else {
      // Translucent Sapphire Blue Billowing Outer Edge
      colors[i * 3] = 0.22;
      colors[i * 3 + 1] = 0.38;
      colors[i * 3 + 2] = 0.92;
    }

    sizes[i] = 1.2 + Math.random() * 2.8;
  }

  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

  // Custom particle texture
  const canvas = document.createElement('canvas');
  canvas.width = 64;
  canvas.height = 64;
  const ctx = canvas.getContext('2d')!;
  const gradient = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
  gradient.addColorStop(0, 'rgba(255,255,255,1)');
  gradient.addColorStop(0.3, 'rgba(255,255,255,0.7)');
  gradient.addColorStop(0.7, 'rgba(255,255,255,0.15)');
  gradient.addColorStop(1, 'rgba(255,255,255,0)');
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 64, 64);

  const texture = new THREE.CanvasTexture(canvas);

  const material = new THREE.PointsMaterial({
    size: 0.18,
    vertexColors: true,
    map: texture,
    transparent: true,
    opacity: 0.65,
    blending: THREE.AdditiveBlending,
    depthWrite: false
  });

  particlesMesh = new THREE.Points(geometry, material);
  plumeGroup.add(particlesMesh);
}

function buildCutplanes() {
  // Horizontal Cutplane (XY)
  const geomXY = new THREE.PlaneGeometry(3.6, 2.2, 80, 50);
  const colorsXY: number[] = [];
  const posXY = geomXY.attributes.position;

  for (let i = 0; i < posXY.count; i++) {
    const x = posXY.getX(i);
    const y = posXY.getY(i);
    const dist = Math.sqrt(y * y);
    const intensity = Math.max(0, 1 - dist * 1.5) * Math.exp(-Math.pow(x + 0.8, 2) / 3.0);
    const [r, g, b] = jetColor(intensity);
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
  cutplaneXY.rotation.x = -Math.PI / 2; // Flat horizontal plane
  cutplanesGroup.add(cutplaneXY);

  // Vertical Cutplane (XZ)
  const geomXZ = new THREE.PlaneGeometry(3.6, 1.8, 80, 40);
  const colorsXZ: number[] = [];
  const posXZ = geomXZ.attributes.position;

  for (let i = 0; i < posXZ.count; i++) {
    const x = posXZ.getX(i);
    const z = posXZ.getY(i);
    const dist = Math.sqrt(z * z);
    const intensity = Math.max(0, 1 - dist * 1.8) * Math.exp(-Math.pow(x + 0.8, 2) / 3.0);
    const [r, g, b] = jetColor(intensity);
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
  cutplaneXZ.rotation.y = 0; // Vertical plane
  cutplanesGroup.add(cutplaneXZ);
}

function buildProbeMarker() {
  const markerGeom = new THREE.SphereGeometry(0.04, 16, 16);
  const markerMat = new THREE.MeshBasicMaterial({
    color: 0xffffff,
    wireframe: true
  });
  probeMarker = new THREE.Mesh(markerGeom, markerMat);
  probeMarker.position.set(0.6, 0.1, 0.2);
  scene.add(probeMarker);
}

// Scientific Jet Heatmap Palette
function jetColor(val: number): [number, number, number] {
  const v = Math.max(0, Math.min(1, val));
  let r = 0, g = 0, b = 0;
  if (v < 0.125) {
    b = 0.5 + 4 * v;
  } else if (v < 0.375) {
    b = 1;
    g = 4 * (v - 0.125);
  } else if (v < 0.625) {
    b = 1 - 4 * (v - 0.375);
    g = 1;
    r = 4 * (v - 0.375);
  } else if (v < 0.875) {
    g = 1 - 4 * (v - 0.625);
    r = 1;
  } else {
    r = 1 - 2 * (v - 0.875);
  }
  return [r, g, b];
}

function animate() {
  animId = requestAnimationFrame(animate);

  const time = performance.now() * 0.001;

  if (isAutoRotate.value) {
    targetRotationY += 0.004;
  }

  // Smooth rotation damping
  if (plumeGroup && cutplanesGroup) {
    plumeGroup.rotation.x = targetRotationX;
    plumeGroup.rotation.z = targetRotationY;
    cutplanesGroup.rotation.x = targetRotationX;
    cutplanesGroup.rotation.z = targetRotationY;
  }

  // Subtle fluid turbulence plume billowing animation
  if (particlesMesh && particlesMesh.geometry) {
    const pos = particlesMesh.geometry.attributes.position as THREE.BufferAttribute;
    const array = pos.array as Float32Array;
    for (let i = 0; i < array.length; i += 3) {
      array[i + 1] += Math.sin(time * 2 + array[i] * 3) * 0.001;
    }
    pos.needsUpdate = true;
  }

  // Visibility toggles
  if (plumeGroup) plumeGroup.visible = showPlume.value;
  if (cutplanesGroup) cutplanesGroup.visible = showCutplanes.value;

  if (renderer && scene && camera) {
    renderer.render(scene, camera);
  }
}

// Mouse Controls & Raycast Flow Probe
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
    // Flow Probe Raycast
    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObjects([cutplaneXY, cutplaneXZ], true);

    if (intersects.length > 0) {
      const hit = intersects[0];
      probe.value.active = true;
      probe.value.screenX = e.clientX - rect.left;
      probe.value.screenY = e.clientY - rect.top;

      // Simulated local fluid velocity calculation
      const dist = hit.point.length();
      const iris = props.params.studioParams?.irisPurple ?? 0.182;
      probe.value.value = Math.max(0.01, 0.22 * (1.2 - dist * 0.3) + iris * 0.15);

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

watch(() => props.params.studioParams, () => {
  if (plumeGroup) {
    while (plumeGroup.children.length > 0) {
      plumeGroup.remove(plumeGroup.children[0]);
    }
    buildVolumetricPlume();
  }
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
  background: #0f131a;
  border-radius: 10px;
  overflow: hidden;
}

/* Viewport Header */
.viewport-title-bar {
  position: absolute;
  top: 14px;
  left: 18px;
  z-index: 10;
  pointer-events: none;
}

.viewport-title {
  font-size: 15px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: -0.2px;
}

/* HUD Toolbar Overlay */
.viewport-hud-toolbar {
  position: absolute;
  top: 14px;
  right: 18px;
  display: flex;
  gap: 8px;
  z-index: 10;
}

.hud-tool-btn {
  background: rgba(25, 30, 40, 0.85);
  backdrop-filter: blur(8px);
  color: #cbd5e1;
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 5px 10px;
  border-radius: 6px;
  font-size: 11.5px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.hud-tool-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #ffffff;
}

.hud-tool-btn.active {
  background: rgba(168, 85, 247, 0.25);
  border-color: rgba(168, 85, 247, 0.6);
  color: #e9d5ff;
}

.webgl-canvas-mount {
  flex: 1;
  width: 100%;
  height: 100%;
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
