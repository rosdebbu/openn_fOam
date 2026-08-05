<template>
  <div class="three-container">
    <!-- Controls Overlay Bar -->
    <div class="three-toolbar">
      <button class="tool-btn" :class="{ active: isWireframe }" @click="toggleWireframe">
        🕸️ Wireframe
      </button>
      <button class="tool-btn" :class="{ active: isAutoRotate }" @click="isAutoRotate = !isAutoRotate">
        🔄 Auto-Rotate
      </button>
      <div class="height-scale">
        <label>Z-Scale: {{ zScale.toFixed(1) }}x</label>
        <input type="range" min="0.1" max="3" step="0.1" v-model.number="zScale" @input="updateGeometry" />
      </div>
    </div>

    <!-- WebGL Canvas Container -->
    <div ref="canvasHostRef" class="webgl-host"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue';
import * as THREE from 'three';
import type { SimulationStepData, ColormapScheme } from '../types/cfd';
import { getColorRgb } from '../utils/colormaps';

const props = defineProps<{
  data: SimulationStepData | null;
  colormap: ColormapScheme;
}>();

const canvasHostRef = ref<HTMLDivElement | null>(null);

const isWireframe = ref(true);
const isAutoRotate = ref(false);
const zScale = ref(1.0);

let scene: THREE.Scene;
let camera: THREE.PerspectiveCamera;
let renderer: THREE.WebGLRenderer;
let mesh: THREE.Mesh;
let animId: number;

// Basic orbit control parameters
let isDragging = false;
let previousMousePosition = { x: 0, y: 0 };
let targetRotationX = 0.5;
let targetRotationY = -0.5;

function initThree() {
  if (!canvasHostRef.value) return;

  const width = canvasHostRef.value.clientWidth || 600;
  const height = canvasHostRef.value.clientHeight || 600;

  // Scene
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0a0e17);

  // Camera
  camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
  camera.position.set(0, -3.2, 2.5);
  camera.lookAt(0, 0, 0);

  // Renderer
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

  // Clear previous DOM elements if any
  canvasHostRef.value.innerHTML = '';
  canvasHostRef.value.appendChild(renderer.domElement);

  // Lights
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
  scene.add(ambientLight);

  const dirLight1 = new THREE.DirectionalLight(0x00d2ff, 1.2);
  dirLight1.position.set(3, 3, 5);
  scene.add(dirLight1);

  const dirLight2 = new THREE.DirectionalLight(0xff007f, 0.8);
  dirLight2.position.set(-3, -3, -2);
  scene.add(dirLight2);

  // Add mouse interaction listeners
  const dom = renderer.domElement;
  dom.addEventListener('mousedown', onMouseDown);
  dom.addEventListener('mousemove', onMouseMove);
  window.addEventListener('mouseup', onMouseUp);
  dom.addEventListener('wheel', onWheel);

  animate();
}

function updateGeometry() {
  if (!props.data || !props.data.speed || !scene) return;

  const data = props.data;
  const nx = data.speed.length;
  const ny = data.speed[0].length;

  if (mesh) {
    scene.remove(mesh);
    mesh.geometry.dispose();
    if (Array.isArray(mesh.material)) {
      mesh.material.forEach(m => m.dispose());
    } else {
      mesh.material.dispose();
    }
  }

  const geometry = new THREE.PlaneGeometry(2.4, 2.4, nx - 1, ny - 1);
  const posAttr = geometry.attributes.position;
  const colors: number[] = [];

  let minVal = Infinity, maxVal = -Infinity;
  for (let i = 0; i < nx; i++) {
    for (let j = 0; j < ny; j++) {
      const val = data.speed[i][j];
      if (val < minVal) minVal = val;
      if (val > maxVal) maxVal = val;
    }
  }

  for (let j = 0; j < ny; j++) {
    for (let i = 0; i < nx; i++) {
      const idx = j * nx + i;
      const val = data.speed[i][j];

      // Z height corresponds to velocity magnitude
      posAttr.setZ(idx, val * 0.8 * zScale.value);

      const [r, g, b] = getColorRgb(val, minVal, maxVal, props.colormap);
      colors.push(r / 255, g / 255, b / 255);
    }
  }

  geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
  geometry.computeVertexNormals();

  const material = new THREE.MeshPhongMaterial({
    vertexColors: true,
    wireframe: isWireframe.value,
    side: THREE.DoubleSide,
    shininess: 80
  });

  mesh = new THREE.Mesh(geometry, material);
  scene.add(mesh);
}

function toggleWireframe() {
  isWireframe.value = !isWireframe.value;
  if (mesh && mesh.material) {
    (mesh.material as THREE.MeshPhongMaterial).wireframe = isWireframe.value;
  }
}

function animate() {
  animId = requestAnimationFrame(animate);

  if (mesh) {
    if (isAutoRotate.value) {
      targetRotationY += 0.005;
    }
    mesh.rotation.x = targetRotationX;
    mesh.rotation.z = targetRotationY;
  }

  if (renderer && scene && camera) {
    renderer.render(scene, camera);
  }
}

// Mouse Controls
function onMouseDown(e: MouseEvent) {
  isDragging = true;
  previousMousePosition = { x: e.clientX, y: e.clientY };
}

function onMouseMove(e: MouseEvent) {
  if (!isDragging) return;
  const deltaX = e.clientX - previousMousePosition.x;
  const deltaY = e.clientY - previousMousePosition.y;

  targetRotationY += deltaX * 0.01;
  targetRotationX += deltaY * 0.01;

  previousMousePosition = { x: e.clientX, y: e.clientY };
}

function onMouseUp() {
  isDragging = false;
}

function onWheel(e: WheelEvent) {
  camera.position.z = Math.max(1, Math.min(8, camera.position.z + e.deltaY * 0.003));
}

function handleResize() {
  if (!canvasHostRef.value || !renderer || !camera) return;
  const width = canvasHostRef.value.clientWidth;
  const height = canvasHostRef.value.clientHeight;

  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setSize(width, height);
}

watch(() => [props.data, props.colormap], () => {
  updateGeometry();
}, { deep: true });

onMounted(() => {
  initThree();
  updateGeometry();
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  if (animId) cancelAnimationFrame(animId);
  window.removeEventListener('resize', handleResize);
});
</script>

<style scoped>
.three-container {
  width: 100%;
  height: 100%;
  position: relative;
  display: flex;
  flex-direction: column;
}

.three-toolbar {
  position: absolute;
  top: 15px;
  left: 15px;
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(15, 23, 42, 0.85);
  backdrop-filter: blur(8px);
  padding: 8px 14px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  z-index: 10;
}

.tool-btn {
  background: rgba(255, 255, 255, 0.08);
  color: #cbd5e1;
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 5px 10px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.tool-btn.active {
  background: rgba(0, 210, 255, 0.2);
  color: #00d2ff;
  border-color: rgba(0, 210, 255, 0.4);
}

.height-scale {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: #cbd5e1;
}

.height-scale input[type="range"] {
  width: 70px;
  accent-color: #00d2ff;
}

.webgl-host {
  flex: 1;
  width: 100%;
  height: 100%;
}
</style>
