<template>
  <aside class="case-hub-panel">
    <!-- Hub Header -->
    <div class="hub-header">
      <h2 class="hub-title">OpenFOAM Case Hub</h2>
    </div>

    <!-- Mode Switcher Pill -->
    <div class="mode-toggle-wrapper">
      <button
        class="mode-btn"
        :class="{ active: activeMode === 'ai' }"
        @click="setMode('ai')"
      >
        <span>[ 🤖 AI Copilot ]</span>
      </button>
      <button
        class="mode-btn"
        :class="{ active: activeMode === 'manual' }"
        @click="setMode('manual')"
      >
        <span>⚙️ Manual OpenFOAM</span>
      </button>
    </div>

    <!-- Hub Grid: Left Tree & Right Controls -->
    <div class="hub-grid">
      <!-- Card 1: OpenFOAM Case File Tree -->
      <div class="hub-card tree-card">
        <div class="card-header">
          <span class="card-title">OpenFOAM case</span>
          <span class="token-tag">oklch(37.8% 0.015)</span>
        </div>

        <div class="file-tree-container">
          <!-- system/ folder -->
          <div class="tree-folder">
            <div class="folder-header" @click="toggleFolder('system')">
              <span class="folder-arrow">{{ expandedFolders.system ? '▾' : '▸' }}</span>
              <span class="folder-icon">📁</span>
              <span class="folder-name">system/</span>
            </div>
            <div v-show="expandedFolders.system" class="folder-children">
              <div
                v-for="file in systemFiles"
                :key="file.name"
                class="tree-file"
                :class="{ selected: selectedFile?.name === file.name }"
                @click="selectFile(file)"
              >
                <span class="file-icon">📄</span>
                <span class="file-name">{{ file.name }}</span>
              </div>
            </div>
          </div>

          <!-- constant/ folder -->
          <div class="tree-folder">
            <div class="folder-header" @click="toggleFolder('constant')">
              <span class="folder-arrow">{{ expandedFolders.constant ? '▾' : '▸' }}</span>
              <span class="folder-icon">📁</span>
              <span class="folder-name">constant/</span>
            </div>
            <div v-show="expandedFolders.constant" class="folder-children">
              <div
                v-for="file in constantFiles"
                :key="file.name"
                class="tree-file"
                :class="{ selected: selectedFile?.name === file.name }"
                @click="selectFile(file)"
              >
                <span class="file-icon">📄</span>
                <span class="file-name">{{ file.name }}</span>
              </div>
            </div>
          </div>

          <!-- 0/ folder (Boundary Conditions) -->
          <div class="tree-folder">
            <div class="folder-header" @click="toggleFolder('zero')">
              <span class="folder-arrow">{{ expandedFolders.zero ? '▾' : '▸' }}</span>
              <span class="folder-icon">📁</span>
              <span class="folder-name">0/</span>
            </div>
            <div v-show="expandedFolders.zero" class="folder-children">
              <div
                v-for="file in zeroFiles"
                :key="file.name"
                class="tree-file"
                :class="{ selected: selectedFile?.name === file.name }"
                @click="selectFile(file)"
              >
                <span class="file-icon">📄</span>
                <span class="file-name">{{ file.name }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Column: Parameters & Geometry Input Cards -->
      <div class="right-controls-column">
        <!-- Card 2: Parameters Card -->
        <div class="hub-card params-card">
          <div class="card-header">
            <span class="card-title">Parameters</span>
            <span class="token-tag">oklch(67.3% 0.182 278.935)</span>
          </div>

          <div class="sliders-list">
            <!-- Iris Purple Slider -->
            <div class="slider-group">
              <div class="slider-labels">
                <label>Iris Purple</label>
                <span class="slider-val-badge">{{ studioParams.irisPurple.toFixed(3) }}</span>
              </div>
              <input
                type="range"
                min="0.01"
                max="1.0"
                step="0.001"
                v-model.number="studioParams.irisPurple"
                @input="emitParamsChange"
              />
            </div>

            <!-- Vorticity Angle Slider -->
            <div class="slider-group">
              <div class="slider-labels">
                <label>Vorticity angle</label>
                <span class="slider-val-badge">{{ studioParams.vorticityAngle.toFixed(3) }}</span>
              </div>
              <input
                type="range"
                min="0.0"
                max="1.57"
                step="0.005"
                v-model.number="studioParams.vorticityAngle"
                @input="emitParamsChange"
              />
            </div>

            <!-- Vorticity Core Slider -->
            <div class="slider-group">
              <div class="slider-labels">
                <label>Vorticity core</label>
                <span class="slider-val-badge">{{ Math.round(studioParams.vorticityCore) }}</span>
              </div>
              <input
                type="range"
                min="5"
                max="100"
                step="1"
                v-model.number="studioParams.vorticityCore"
                @input="emitParamsChange"
              />
            </div>

            <!-- Butterscotch Core Slider -->
            <div class="slider-group">
              <div class="slider-labels">
                <label>Butterscotch core</label>
                <span class="slider-val-badge">{{ studioParams.butterscotchCore.toFixed(3) }}</span>
              </div>
              <input
                type="range"
                min="10"
                max="150"
                step="0.1"
                v-model.number="studioParams.butterscotchCore"
                @input="emitParamsChange"
              />
            </div>
          </div>
        </div>

        <!-- Card 3: Geometry input / Photo dropzone Card -->
        <div class="hub-card geometry-card">
          <div class="card-header">
            <span class="card-title">Geometry input</span>
            <span class="token-tag">oklch(88.2% 0.059 254.128)</span>
          </div>

          <div
            class="photo-dropzone"
            :class="{ dragging: isDraggingOver, 'has-file': !!uploadedFileName }"
            @dragover.prevent="isDraggingOver = true"
            @dragleave.prevent="isDraggingOver = false"
            @drop.prevent="handleFileDrop"
            @click="triggerFileInput"
          >
            <input
              type="file"
              ref="fileInputRef"
              style="display: none"
              accept=".stl,.obj,.step,.png,.jpg,.jpeg"
              @change="handleFileChange"
            />

            <div class="dropzone-content">
              <div class="upload-icon-wrapper">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="17 8 12 3 7 8"></polyline>
                  <line x1="12" y1="3" x2="12" y2="15"></line>
                </svg>
              </div>
              <span class="dropzone-title">Photo dropzone</span>
              <span class="dropzone-sub">oklch(70.7% 0.022 281.325)</span>
              <span v-if="uploadedFileName" class="uploaded-badge">📎 {{ uploadedFileName }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Dict Viewer Modal -->
    <transition name="fade">
      <div v-if="selectedFile" class="dict-modal-backdrop" @click="selectedFile = null">
        <div class="dict-modal" @click.stop>
          <div class="modal-header">
            <div class="modal-title">
              <span class="file-icon">📄</span>
              <strong>{{ selectedFile.category }}/{{ selectedFile.name }}</strong>
            </div>
            <button class="close-btn" @click="selectedFile = null">✕</button>
          </div>
          <div class="modal-body">
            <pre class="dict-code"><code>{{ selectedFile.content }}</code></pre>
          </div>
        </div>
      </div>
    </transition>
  </aside>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue';
import type { SimulationParams, StudioParameters, OpenFoamDictFile } from '../types/cfd';

const props = defineProps<{
  params: SimulationParams;
  isComputing?: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:params', params: SimulationParams): void;
  (e: 'fileUploaded', file: File): void;
}>();

const activeMode = ref<'ai' | 'manual'>('ai');
const isDraggingOver = ref(false);
const uploadedFileName = ref<string | null>(null);
const fileInputRef = ref<HTMLInputElement | null>(null);

const studioParams = reactive<StudioParameters>({
  irisPurple: props.params.studioParams?.irisPurple ?? 0.182,
  vorticityAngle: props.params.studioParams?.vorticityAngle ?? 0.152,
  vorticityCore: props.params.studioParams?.vorticityCore ?? 30,
  butterscotchCore: props.params.studioParams?.butterscotchCore ?? 84.899
});

const expandedFolders = reactive({
  system: true,
  constant: true,
  zero: true
});

const selectedFile = ref<OpenFoamDictFile | null>(null);

// OpenFOAM Mock Case Tree Files matching the Mockup
const systemFiles: OpenFoamDictFile[] = [
  {
    name: 'controlDict',
    path: 'system/controlDict',
    category: 'system',
    content: `/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2406                                 |
|   \\\\  /    A nd           | Website:  www.openfoam.com                      |
|    \\\\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "system";
    object      controlDict;
}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

application     buoyantBoussinesqSimpleFoam;
startFrom       startTime;
startTime       0;
stopAt          endTime;
endTime         1000;
deltaT          1;
writeControl    timeStep;
writeInterval   50;
purgeWrite      0;
writeFormat     ascii;
writePrecision  6;
writeCompression off;
timeFormat      general;
timePrecision   6;
runTimeModifiable true;`
  },
  {
    name: 'fvSchemes',
    path: 'system/fvSchemes',
    category: 'system',
    content: `FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "system";
    object      fvSchemes;
}
ddtSchemes
{
    default         steadyState;
}
gradSchemes
{
    default         Gauss linear;
}
divSchemes
{
    default         none;
    div(phi,U)      Gauss linearUpwind grad(U);
    div(phi,T)      Gauss linearUpwind grad(T);
}
laplacianSchemes
{
    default         Gauss linear corrected;
}`
  },
  {
    name: 'fvSolution',
    path: 'system/fvSolution',
    category: 'system',
    content: `FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "system";
    object      fvSolution;
}
solvers
{
    p_rgh
    {
        solver          GAMG;
        tolerance       1e-07;
        relTol          0.01;
        smoother        GaussSeidel;
    }
    "(U|T)"
    {
        solver          smoothSolver;
        smoother        symGaussSeidel;
        tolerance       1e-08;
        relTol          0.1;
    }
}
SIMPLE
{
    nNonOrthogonalCorrectors 0;
    consistent      yes;
}`
  },
  {
    name: 'blockMeshDict',
    path: 'system/blockMeshDict',
    category: 'system',
    content: `FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "system";
    object      blockMeshDict;
}
scale   0.1;
vertices
(
    (0 0 0)
    (2 0 0)
    (2 1 0)
    (0 1 0)
    (0 0 0.5)
    (2 0 0.5)
    (2 1 0.5)
    (0 1 0.5)
);
blocks
(
    hex (0 1 2 3 4 5 6 7) (80 40 20) simpleGrading (1 1 1)
);`
  }
];

const constantFiles: OpenFoamDictFile[] = [
  {
    name: 'transportProperties',
    path: 'constant/transportProperties',
    category: 'constant',
    content: `FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "constant";
    object      transportProperties;
}
transportModel  Newtonian;
nu              [0 2 -1 0 0 0 0] 1.5e-05;
beta            [0 0 0 -1 0 0 0] 3.3e-03;
TRef            [0 0 0 1 0 0 0]  293.15;
Pr              [0 0 0 0 0 0 0]  0.71;
Prt             [0 0 0 0 0 0 0]  0.85;`
  },
  {
    name: 'turbulenceProperties',
    path: 'constant/turbulenceProperties',
    category: 'constant',
    content: `FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "constant";
    object      turbulenceProperties;
}
simulationType  RAS;
RAS
{
    RASModel        kEpsilon;
    turbulence      on;
    printCoeffs     on;
}`
  },
  {
    name: 'g',
    path: 'constant/g',
    category: 'constant',
    content: `FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "constant";
    object      g;
}
dimensions      [0 1 -2 0 0 0 0];
value           (0 0 -9.81);`
  }
];

const zeroFiles: OpenFoamDictFile[] = [
  {
    name: 'U',
    path: '0/U',
    category: '0',
    content: `FoamFile
{
    version     2.0;
    format      ascii;
    class       volVectorField;
    location    "0";
    object      U;
}
dimensions      [0 1 -1 0 0 0 0];
internalField   uniform (0 0 0);
boundaryField
{
    inlet
    {
        type            fixedValue;
        value           uniform (0.182 0 0);
    }
    outlet
    {
        type            inletOutlet;
        inletValue      uniform (0 0 0);
        value           uniform (0 0 0);
    }
    walls
    {
        type            noSlip;
    }
}`
  },
  {
    name: 'p_rgh',
    path: '0/p_rgh',
    category: '0',
    content: `FoamFile
{
    version     2.0;
    format      ascii;
    class       volScalarField;
    location    "0";
    object      p_rgh;
}
dimensions      [1 -1 -2 0 0 0 0];
internalField   uniform 0;
boundaryField
{
    inlet
    {
        type            fixedFluxPressure;
        value           uniform 0;
    }
    outlet
    {
        type            fixedValue;
        value           uniform 0;
    }
    walls
    {
        type            fixedFluxPressure;
        value           uniform 0;
    }
}`
  },
  {
    name: 'T',
    path: '0/T',
    category: '0',
    content: `FoamFile
{
    version     2.0;
    format      ascii;
    class       volScalarField;
    location    "0";
    object      T;
}
dimensions      [0 0 0 1 0 0 0];
internalField   uniform 293.15;
boundaryField
{
    inlet
    {
        type            fixedValue;
        value           uniform 293.15;
    }
    heaterSource
    {
        type            fixedValue;
        value           uniform 358.05; // 84.899 C
    }
    walls
    {
        type            zeroGradient;
    }
}`
  }
];

function toggleFolder(folder: 'system' | 'constant' | 'zero') {
  expandedFolders[folder] = !expandedFolders[folder];
}

function selectFile(file: OpenFoamDictFile) {
  selectedFile.value = file;
}

function setMode(mode: 'ai' | 'manual') {
  activeMode.value = mode;
  emit('update:params', {
    ...props.params,
    solverMode: mode === 'ai' ? 'ai' : 'cfd'
  });
}

function emitParamsChange() {
  emit('update:params', {
    ...props.params,
    studioParams: { ...studioParams }
  });
}

function triggerFileInput() {
  fileInputRef.value?.click();
}

function handleFileChange(e: Event) {
  const target = e.target as HTMLInputElement;
  if (target.files && target.files[0]) {
    const file = target.files[0];
    uploadedFileName.value = file.name;
    emit('fileUploaded', file);
  }
}

function handleFileDrop(e: DragEvent) {
  isDraggingOver.value = false;
  if (e.dataTransfer && e.dataTransfer.files[0]) {
    const file = e.dataTransfer.files[0];
    uploadedFileName.value = file.name;
    emit('fileUploaded', file);
  }
}

watch(() => props.params.studioParams, (newParams) => {
  if (newParams) {
    Object.assign(studioParams, newParams);
  }
}, { deep: true });
</script>

<style scoped>
.case-hub-panel {
  width: 480px;
  min-width: 440px;
  height: 100%;
  background: var(--bg-canvas);
  border-right: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  padding: 14px 18px;
  gap: 14px;
  overflow-y: auto;
  user-select: none;
}

.hub-header {
  display: flex;
  align-items: center;
}

.hub-title {
  font-size: 16px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: -0.2px;
}

/* Mode Switcher */
.mode-toggle-wrapper {
  display: flex;
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  padding: 4px;
  gap: 4px;
}

.mode-btn {
  flex: 1;
  padding: 8px 12px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 6px;
  color: var(--text-secondary);
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: center;
}

.mode-btn.active {
  background: rgba(168, 85, 247, 0.18);
  border-color: rgba(168, 85, 247, 0.45);
  color: #d8b4fe;
  box-shadow: 0 0 12px rgba(168, 85, 247, 0.25);
}

.mode-btn:hover:not(.active) {
  background: rgba(255, 255, 255, 0.05);
  color: #ffffff;
}

/* Hub Grid Layout */
.hub-grid {
  display: grid;
  grid-template-columns: 1.15fr 1fr;
  gap: 12px;
  flex: 1;
}

/* Hub Cards */
.hub-card {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  flex-direction: column;
  margin-bottom: 10px;
}

.card-title {
  font-size: 13px;
  font-weight: 700;
  color: #ffffff;
}

.token-tag {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9.5px;
  color: var(--text-secondary);
  opacity: 0.8;
}

/* File Tree */
.tree-card {
  overflow-y: auto;
  max-height: calc(100vh - 170px);
}

.file-tree-container {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11.5px;
}

.tree-folder {
  display: flex;
  flex-direction: column;
}

.folder-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 6px;
  border-radius: 4px;
  cursor: pointer;
  color: #e2e8f0;
  transition: background 0.15s ease;
}

.folder-header:hover {
  background: rgba(255, 255, 255, 0.06);
}

.folder-arrow {
  font-size: 10px;
  color: #94a3b8;
  width: 12px;
}

.folder-icon {
  font-size: 12px;
}

.folder-name {
  font-weight: 600;
  color: #38bdf8;
}

.folder-children {
  margin-left: 20px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  border-left: 1px dashed rgba(255, 255, 255, 0.12);
  padding-left: 8px;
}

.tree-file {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 6px;
  border-radius: 4px;
  cursor: pointer;
  color: #cbd5e1;
  transition: all 0.15s ease;
}

.tree-file:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #ffffff;
}

.tree-file.selected {
  background: rgba(168, 85, 247, 0.2);
  color: #e9d5ff;
}

.file-icon {
  font-size: 11px;
}

.file-name {
  font-size: 11px;
}

/* Right Column */
.right-controls-column {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.params-card {
  flex: 1;
}

.sliders-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.slider-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.slider-labels label {
  font-size: 11.5px;
  font-weight: 600;
  color: #cbd5e1;
}

.slider-val-badge {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10.5px;
  font-weight: 600;
  color: #ffffff;
  background: rgba(255, 255, 255, 0.08);
  padding: 2px 6px;
  border-radius: 4px;
}

/* Geometry Card & Dropzone */
.geometry-card {
  min-height: 120px;
}

.photo-dropzone {
  border: 1px dashed rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  padding: 14px 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  cursor: pointer;
  background: rgba(0, 0, 0, 0.2);
  transition: all 0.2s ease;
}

.photo-dropzone:hover,
.photo-dropzone.dragging {
  border-color: #a855f7;
  background: rgba(168, 85, 247, 0.08);
}

.dropzone-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
}

.upload-icon-wrapper {
  color: #94a3b8;
  margin-bottom: 2px;
}

.dropzone-title {
  font-size: 12px;
  font-weight: 600;
  color: #ffffff;
}

.dropzone-sub {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  color: var(--text-secondary);
}

.uploaded-badge {
  margin-top: 4px;
  font-size: 10.5px;
  color: #10b981;
  background: rgba(16, 185, 129, 0.15);
  padding: 2px 8px;
  border-radius: 4px;
}

/* Modal View */
.dict-modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(4px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.dict-modal {
  width: 600px;
  max-width: 90vw;
  max-height: 80vh;
  background: #141b24;
  border: 1px solid var(--border-active);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.8);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 18px;
  background: #19222f;
  border-bottom: 1px solid var(--border-subtle);
}

.modal-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13.5px;
  color: #ffffff;
}

.close-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 16px;
  cursor: pointer;
}

.close-btn:hover {
  color: #ffffff;
}

.modal-body {
  padding: 16px;
  overflow-y: auto;
  background: #0d1219;
}

.dict-code {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11.5px;
  color: #38bdf8;
  white-space: pre-wrap;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
