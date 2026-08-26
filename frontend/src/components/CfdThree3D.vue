<template>
  <div class="three-viewport-container">
    <!-- Viewport Header Label & Active Archetype Badge -->
    <div class="viewport-title-bar">
      <span class="viewport-title">Three.js CFD Viewport</span>
      <span class="archetype-badge">{{ archetypeBadgeTitle }}</span>
    </div>

    <!-- Interactive HUD Toolbar Overlay -->
    <div class="viewport-hud-toolbar">
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
        :class="{ active: showPlumeOrStreamlines }"
        @click="showPlumeOrStreamlines = !showPlumeOrStreamlines"
        title="Toggle Volumetric Plume / Streamlines"
      >
        💨 Flow Field
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
        🎯 Reset
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
          <span class="probe-val-title">{{ probe.label }}</span>
          <span class="probe-val-num">{{ probe.value.toFixed(2) }} {{ probe.unit }}</span>
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
import type { SimulationStepData, SimulationParams } from '../types/cfd';

const props = defineProps<{
  data: SimulationStepData | null;
  params: SimulationParams;
}>();

const canvasMountRef = ref<HTMLDivElement | null>(null);

const showGeometry = ref(true);
const showPlumeOrStreamlines = ref(true);
const showCutplanes = ref(true);
const isAutoRotate = ref(false);

// Flow Probe Tooltip State
const probe = ref({
  active: false,
  screenX: 0,
  screenY: 0,
  value: 0.22,
  unit: 'm/s',
  label: 'Values',
  subtext: 'Hover Flow probe HUD'
});

let scene: THREE.Scene;
let camera: THREE.PerspectiveCamera;
let renderer: THREE.WebGLRenderer;
let animId: number;

let mainGroup: THREE.Group;
let geometryGroup: THREE.Group;
let flowFieldGroup: THREE.Group;
let cutplanesGroup: THREE.Group;

let cutplaneXY: THREE.Mesh;
let cutplaneXZ: THREE.Mesh;
let probeMarker: THREE.Mesh;
let particlesMesh: THREE.Points | null = null;
let streamlineLines: THREE.LineSegments | null = null;

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

function initThree() {
  if (!canvasMountRef.value) return;

  const width = canvasMountRef.value.clientWidth || 800;
  const height = canvasMountRef.value.clientHeight || 600;

  // 1. Scene
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0f131a);

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
  const ambient = new THREE.AmbientLight(0xffffff, 0.9);
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

  mainGroup.add(geometryGroup);
  mainGroup.add(flowFieldGroup);
  mainGroup.add(cutplanesGroup);
  scene.add(mainGroup);

  // 6. Build Scene elements
  buildActiveArchetype();
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
  clearGroup(flowFieldGroup);

  const arch = props.params.archetype || 'plume';
  const iris = props.params.studioParams?.irisPurple ?? 0.182;
  const vorticityAngle = props.params.studioParams?.vorticityAngle ?? 0.152;
  const butterscotch = props.params.studioParams?.butterscotchCore ?? 84.899;

  if (arch === 'airfoil') {
    // ✈️ 3D NACA 0012 Airfoil Wing Geometry
    const shape = new THREE.Shape();
    const chord = 2.4;
    const nPoints = 60;
    const points: THREE.Vector2[] = [];

    // NACA 0012 thickness distribution
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
      metalness: 0.8,
      roughness: 0.2,
      wireframe: false
    });

    const wingMesh = new THREE.Mesh(wingGeom, wingMat);
    wingMesh.rotation.z = -vorticityAngle; // Angle of attack
    geometryGroup.add(wingMesh);

    // Aerodynamic Streamlines around Wing
    buildStreamlinesAroundObstacle('airfoil', vorticityAngle);

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

    // Von Kármán Vortex Shedding Streamlines
    buildStreamlinesAroundObstacle('cylinder', vorticityAngle);

  } else if (arch === 'venturi') {
    // 🚿 Venturi Nozzle Glass Tube
    const points: THREE.Vector2[] = [];
    for (let i = 0; i <= 30; i++) {
      const x = -2.0 + (i / 30) * 4.0;
      // Converging-diverging throat
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

    // Accelerated Core Streamlines
    buildStreamlinesAroundObstacle('venturi', vorticityAngle);

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

    // Moving Lid Indicator Plate
    const lidGeom = new THREE.PlaneGeometry(2.4, 2.4);
    const lidMat = new THREE.MeshBasicMaterial({ color: 0x10b981, side: THREE.DoubleSide, transparent: true, opacity: 0.6 });
    const lidMesh = new THREE.Mesh(lidGeom, lidMat);
    lidMesh.position.set(0, 1.2, 0);
    lidMesh.rotation.x = Math.PI / 2;
    geometryGroup.add(lidMesh);

    // Recirculation Vortex Streamlines
    buildStreamlinesAroundObstacle('cavity', vorticityAngle);

  } else {
    // 💨 Default: Buoyant Thermal Plume (14,000 particles)
    buildVolumetricPlume(iris, butterscotch);
  }
}

function buildVolumetricPlume(iris: number, butterscotch: number) {
  const particleCount = 14000;
  const geometry = new THREE.BufferGeometry();
  const positions = new Float32Array(particleCount * 3);
  const colors = new Float32Array(particleCount * 3);
  const sizes = new Float32Array(particleCount);
  const coreIntensity = Math.min(1.0, butterscotch / 100.0);

  for (let i = 0; i < particleCount; i++) {
    const t = Math.random();
    const x = -2.2 + t * 4.5;
    const spread = (0.2 + t * 0.95) * (0.8 + iris * 1.5);
    const angle = Math.random() * Math.PI * 2;
    const r = Math.pow(Math.random(), 0.7) * spread;

    const y = Math.cos(angle) * r;
    const z = Math.sin(angle) * r * 0.85 + Math.pow(t, 1.4) * 0.45;

    positions[i * 3] = x;
    positions[i * 3 + 1] = y;
    positions[i * 3 + 2] = z;

    const distFromCore = (r / spread);
    if (distFromCore < 0.35 && t < 0.6) {
      colors[i * 3] = 0.98 * coreIntensity;
      colors[i * 3 + 1] = 0.75 * coreIntensity;
      colors[i * 3 + 2] = 0.14;
    } else if (distFromCore < 0.7) {
      colors[i * 3] = 0.05;
      colors[i * 3 + 1] = 0.75;
      colors[i * 3 + 2] = 0.95;
    } else {
      colors[i * 3] = 0.22;
      colors[i * 3 + 1] = 0.38;
      colors[i * 3 + 2] = 0.92;
    }

    sizes[i] = 1.2 + Math.random() * 2.8;
  }

  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

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
  flowFieldGroup.add(particlesMesh);
}

function buildStreamlinesAroundObstacle(type: string, paramVal: number) {
  const nStreamlines = 36;
  const segmentsPerLine = 40;
  const positions: number[] = [];
  const colors: number[] = [];

  for (let s = 0; s < nStreamlines; s++) {
    const yStart = -1.2 + (s / nStreamlines) * 2.4;
    const zStart = (Math.random() - 0.5) * 1.2;

    let cx = -2.2;
    let cy = yStart;
    let cz = zStart;

    for (let step = 0; step < segmentsPerLine; step++) {
      const x0 = cx;
      const y0 = cy;
      const z0 = cz;

      // Flow velocity field calculation based on obstacle physics
      let vx = 1.0;
      let vy = 0.0;
      let vz = 0.0;

      if (type === 'airfoil') {
        const dx = cx - 0.0;
        const dy = cy - 0.0;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 1.4) {
          // Flow deflection over suction/pressure sides
          const circulation = paramVal * 2.5;
          vy = -(dx / (dist * dist + 0.1)) * circulation * 0.4;
          vx = 1.0 + (1.2 - Math.abs(dy)) * 0.6;
        }
      } else if (type === 'cylinder') {
        const dx = cx - (-0.8);
        const dy = cy - 0.0;
        const r2 = dx * dx + dy * dy;
        const a2 = 0.35 * 0.35;
        if (r2 > a2) {
          // Potential flow dipole around cylinder + wake vortex
          vx = 1.0 - a2 * (dx * dx - dy * dy) / (r2 * r2);
          vy = -a2 * (2 * dx * dy) / (r2 * r2) + (cx > -0.5 ? Math.sin(cx * 4) * 0.3 : 0);
        }
      } else if (type === 'venturi') {
        const throatFactor = Math.exp(-Math.pow(cx, 2) / 0.6);
        vx = 1.0 + throatFactor * 1.8;
        vy = -cx * throatFactor * 0.4 * (cy / 0.85);
      } else if (type === 'cavity') {
        // Cavity vortex circulation
        vx = -cy * 1.2;
        vy = cx * 1.2;
      }

      cx += vx * 0.12;
      cy += vy * 0.12;
      cz += vz * 0.12;

      positions.push(x0, y0, z0, cx, cy, cz);

      // Color based on speed
      const speed = Math.sqrt(vx * vx + vy * vy);
      const [r, g, b] = jetColor(speed / 2.2);
      colors.push(r, g, b, r, g, b);
    }
  }

  const geom = new THREE.BufferGeometry();
  geom.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geom.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));

  const mat = new THREE.LineBasicMaterial({
    vertexColors: true,
    transparent: true,
    opacity: 0.85,
    linewidth: 2
  });

  streamlineLines = new THREE.LineSegments(geom, mat);
  flowFieldGroup.add(streamlineLines);
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
    const dist = Math.sqrt(y * y);
    const intensity = Math.max(0, 1 - dist * 1.4) * Math.exp(-Math.pow(x + 0.6, 2) / 3.2);
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
  cutplaneXY.rotation.x = -Math.PI / 2;
  cutplanesGroup.add(cutplaneXY);

  // Vertical Cutplane (XZ)
  const geomXZ = new THREE.PlaneGeometry(3.6, 1.8, 80, 40);
  const colorsXZ: number[] = [];
  const posXZ = geomXZ.attributes.position;

  for (let i = 0; i < posXZ.count; i++) {
    const x = posXZ.getX(i);
    const z = posXZ.getY(i);
    const dist = Math.sqrt(z * z);
    const intensity = Math.max(0, 1 - dist * 1.6) * Math.exp(-Math.pow(x + 0.6, 2) / 3.2);
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
  cutplanesGroup.add(cutplaneXZ);
}

function buildProbeMarker() {
  const markerGeom = new THREE.SphereGeometry(0.04, 16, 16);
  const markerMat = new THREE.MeshBasicMaterial({ color: 0xffffff, wireframe: true });
  probeMarker = new THREE.Mesh(markerGeom, markerMat);
  probeMarker.position.set(0.6, 0.1, 0.2);
  scene.add(probeMarker);
}

function jetColor(val: number): [number, number, number] {
  const v = Math.max(0, Math.min(1, val));
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
  const time = performance.now() * 0.001;

  if (isAutoRotate.value) {
    targetRotationY += 0.004;
  }

  if (mainGroup) {
    mainGroup.rotation.x = targetRotationX;
    mainGroup.rotation.z = targetRotationY;
  }

  if (geometryGroup) geometryGroup.visible = showGeometry.value;
  if (flowFieldGroup) flowFieldGroup.visible = showPlumeOrStreamlines.value;
  if (cutplanesGroup) cutplanesGroup.visible = showCutplanes.value;

  // Animate particles if in plume mode
  if (particlesMesh && particlesMesh.geometry) {
    const pos = particlesMesh.geometry.attributes.position as THREE.BufferAttribute;
    const array = pos.array as Float32Array;
    for (let i = 0; i < array.length; i += 3) {
      array[i + 1] += Math.sin(time * 2 + array[i] * 3) * 0.001;
    }
    pos.needsUpdate = true;
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

      const dist = hit.point.length();
      const iris = props.params.studioParams?.irisPurple ?? 0.182;
      probe.value.value = Math.max(0.02, 0.22 * (1.3 - dist * 0.3) + iris * 0.18);
      probe.value.unit = 'm/s';
      probe.value.label = 'Values';
      probe.value.subtext = `${props.params.archetype.toUpperCase()} probe HUD`;

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

watch(() => [props.params.archetype, props.params.studioParams], () => {
  buildActiveArchetype();
  buildCutplanes();
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

.viewport-title-bar {
  position: absolute;
  top: 14px;
  left: 18px;
  z-index: 10;
  pointer-events: none;
  display: flex;
  align-items: center;
  gap: 10px;
}

.viewport-title {
  font-size: 15px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: -0.2px;
}

.archetype-badge {
  font-size: 11px;
  font-weight: 600;
  color: #38bdf8;
  background: rgba(56, 189, 248, 0.15);
  border: 1px solid rgba(56, 189, 248, 0.35);
  padding: 2px 8px;
  border-radius: 4px;
}

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
