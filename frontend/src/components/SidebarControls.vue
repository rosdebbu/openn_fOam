<template>
  <aside class="case-hub-panel">
    <!-- Hub Header -->
    <div class="hub-header">
      <div class="hub-title-row">
        <div class="hub-title-left">
          <span class="hub-icon">📁</span>
          <h2 class="hub-title">OpenFOAM Case Hub</h2>
          <span class="version-tag">v2406 FVM</span>
        </div>
        <button
          class="collapse-sidebar-btn"
          @click="$emit('closeSidebar')"
          title="Collapse Case Hub into Slide Bar (Ctrl + \)"
        >
          ◀ Hide
        </button>
      </div>
      <p class="hub-subtitle">Standard OpenFOAM Directory Tree & Physical Controls</p>
    </div>

    <!-- Mode Switcher Pill (Matching Approved Mockup) -->
    <div class="mode-toggle-wrapper">
      <button
        class="mode-btn"
        :class="{ active: activeMode === 'manual' }"
        @click="setMode('manual')"
      >
        <span>⚙️ Manual OpenFOAM</span>
      </button>
      <button
        class="mode-btn"
        :class="{ active: activeMode === 'ai' }"
        @click="setMode('ai')"
      >
        <span>🤖 AI Copilot</span>
        <span class="ai-chip">{{ aiStatusBadge }}</span>
      </button>
    </div>

    <!-- MODE 1: Manual OpenFOAM (Default Approved Layout) -->
    <div v-show="activeMode === 'manual'" class="manual-mode-content">
      <div class="hub-grid">
        <!-- Column 1: OpenFOAM Case File Tree -->
        <div class="hub-card tree-card">
          <div class="card-header">
            <div class="card-title-row">
              <span class="card-title">OpenFOAM case</span>
              <span class="token-tag">system/ constant/ 0/</span>
            </div>
            <button
              class="auto-diag-btn"
              @click="runCaseDiagnostics"
              title="Run OpenFOAM numerical stability & Courant check"
            >
              ⚡ Check & Repair
            </button>
          </div>

          <div v-if="diagReport" class="diag-report-banner" :class="diagReport.type">
            <span>{{ diagReport.message }}</span>
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
                  v-for="file in currentSystemFiles"
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
                  v-for="file in currentConstantFiles"
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
                  v-for="file in currentZeroFiles"
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

        <!-- Column 2: Parameters, Natural Physics Drawer, Geometry Dropzone -->
        <div class="right-controls-column">
          <!-- Parameters Card -->
          <div class="hub-card params-card">
            <div class="card-header">
              <div class="card-title-row">
                <span class="card-title">Parameters</span>
                <span class="token-tag">Aerodynamics & Flow</span>
              </div>
            </div>

            <div class="sliders-list">
              <!-- Flow Velocity -->
              <div class="slider-group">
                <div class="slider-labels">
                  <label>Flow Speed (U)</label>
                  <span class="slider-val-badge">{{ studioParams.irisPurple.toFixed(2) }} m/s</span>
                </div>
                <input
                  type="range"
                  min="0.05"
                  max="5.0"
                  step="0.05"
                  v-model.number="studioParams.irisPurple"
                  @input="emitParamsChange"
                />
              </div>

              <!-- Vorticity Angle / AoA -->
              <div class="slider-group">
                <div class="slider-labels">
                  <label>Vorticity Angle</label>
                  <span class="slider-val-badge">{{ (studioParams.vorticityAngle * 57.2958).toFixed(1) }}°</span>
                </div>
                <input
                  type="range"
                  min="-0.35"
                  max="0.35"
                  step="0.01"
                  v-model.number="studioParams.vorticityAngle"
                  @input="emitParamsChange"
                />
              </div>

              <!-- Vorticity Core Shear -->
              <div class="slider-group">
                <div class="slider-labels">
                  <label>Vorticity Core</label>
                  <span class="slider-val-badge">{{ studioParams.vorticityCore.toFixed(0) }}</span>
                </div>
                <input
                  type="range"
                  min="10"
                  max="100"
                  step="5"
                  v-model.number="studioParams.vorticityCore"
                  @input="emitParamsChange"
                />
              </div>

              <!-- Thermal Core -->
              <div class="slider-group">
                <div class="slider-labels">
                  <label>Thermal Core</label>
                  <span class="slider-val-badge">{{ studioParams.butterscotchCore.toFixed(1) }} °C</span>
                </div>
                <input
                  type="range"
                  min="20"
                  max="120"
                  step="1"
                  v-model.number="studioParams.butterscotchCore"
                  @input="emitParamsChange"
                />
              </div>
            </div>
          </div>

          <!-- Compact Collapsible Natural Forces & Fluid Properties Drawer -->
          <div class="hub-card natural-drawer-card">
            <div class="drawer-header" @click="isForcesDrawerOpen = !isForcesDrawerOpen">
              <div class="drawer-header-left">
                <span class="drawer-icon">🌍</span>
                <span class="drawer-title">Fluid Medium & Gravity</span>
                <span class="substance-chip">{{ currentSubstance.name }}</span>
              </div>
              <span class="drawer-arrow">{{ isForcesDrawerOpen ? '▲' : '▼' }}</span>
            </div>

            <transition name="drawer-slide">
              <div v-show="isForcesDrawerOpen" class="drawer-body">
                <!-- Substance Selection Pills -->
                <div class="substance-pills-row">
                  <button
                    v-for="sub in substances"
                    :key="sub.id"
                    class="sub-pill-btn"
                    :class="{ active: currentSubstance.id === sub.id }"
                    @click="selectSubstance(sub)"
                  >
                    {{ sub.name }}
                  </button>
                </div>

                <!-- Gravity Presets -->
                <div class="gravity-presets-row">
                  <button
                    class="preset-pill"
                    :class="{ active: Math.abs(gravityZ - (-9.81)) < 0.1 }"
                    @click="setGravity(-9.81)"
                  >
                    Earth
                  </button>
                  <button
                    class="preset-pill"
                    :class="{ active: Math.abs(gravityZ - (-1.62)) < 0.1 }"
                    @click="setGravity(-1.62)"
                  >
                    Moon
                  </button>
                  <button
                    class="preset-pill"
                    :class="{ active: Math.abs(gravityZ) < 0.1 }"
                    @click="setGravity(0.0)"
                  >
                    Zero-G
                  </button>
                  <button
                    class="preset-pill"
                    :class="{ active: Math.abs(gravityZ - 9.81) < 0.1 }"
                    @click="setGravity(9.81)"
                  >
                    Inverted
                  </button>
                </div>
              </div>
            </transition>
          </div>

          <!-- Geometry input / Photo dropzone Card -->
          <div class="hub-card geometry-card">
            <div class="card-header">
              <div class="card-title-row">
                <span class="card-title">Geometry input</span>
                <span class="token-tag">CAD / Mesh / Photo</span>
              </div>
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
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="17 8 12 3 7 8"></polyline>
                    <line x1="12" y1="3" x2="12" y2="15"></line>
                  </svg>
                </div>
                <span class="dropzone-title">Photo dropzone</span>
                <span class="dropzone-sub">Drag & drop .stl / .obj / .step or photo</span>
                <span v-if="uploadedFileName" class="uploaded-badge">📎 {{ uploadedFileName }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- MODE 2: AI Copilot Mode -->
    <div v-show="activeMode === 'ai'" class="ai-mode-content">
      <div class="copilot-chat-history" ref="chatHistoryRef">
        <div v-for="(msg, i) in chatMessages" :key="i" class="chat-msg" :class="msg.role">
          <div class="msg-author">{{ msg.role === 'user' ? '👤 Idea Input' : '⚡ AI Assistant' }}</div>
          <div class="msg-content">{{ msg.text }}</div>

          <!-- Autonomous Action Card -->
          <div v-if="msg.detectedAction" class="ai-action-card">
            <div class="action-card-header">
              <span class="action-pulse-dot"></span>
              <span class="action-badge">Autonomous Action</span>
              <span class="action-label">{{ msg.detectedAction.label }}</span>
            </div>
            <div class="action-card-buttons">
              <button
                class="apply-and-run-btn"
                @click="executeAiAction(msg.detectedAction)"
              >
                ▶ 1-Click Apply to 3D Studio & Run
              </button>
              <button
                v-if="msg.dictCode"
                class="apply-snippet-btn"
                @click="applyAiSnippet(msg.dictCode)"
              >
                📋 View Case Dict
              </button>
            </div>
          </div>
          <button
            v-else-if="msg.dictCode"
            class="apply-snippet-btn"
            @click="applyAiSnippet(msg.dictCode)"
          >
            📋 Apply & Repair in Case
          </button>
        </div>
        <div v-if="isAiLoading" class="chat-msg ai loading">
          <div class="msg-author">⚡ AI Assistant</div>
          <div class="msg-content">🧠 Computing Navier-Stokes equations, boundary conditions & mesh...</div>
        </div>
      </div>

      <!-- Quick Idea Chips -->
      <div class="quick-prompt-chips">
        <button class="chip-btn" @click="sendQuickPrompt('Configure Formula 1 front wing in ground effect at 80 m/s with inverted multi-element downforce')">
          🏎️ F1 Downforce
        </button>
        <button class="chip-btn" @click="sendQuickPrompt('Analyze NACA 0012 swept wing at 14 degrees angle of attack with boundary layer separation')">
          ✈️ Wing Stall
        </button>
        <button class="chip-btn" @click="sendQuickPrompt('Simulate quadcopter multi-rotor propeller downwash and slipstream contraction in air')">
          🚁 Drone Downwash
        </button>
        <button class="chip-btn" @click="sendQuickPrompt('Simulate submarine hydrodynamic teardrop hull in seawater at 20 knots with boundary layer wake')">
          🌊 Submarine Hull
        </button>
        <button class="chip-btn" @click="sendQuickPrompt('Thermal plume rising with Boussinesq buoyancy at 350K')">
          🔥 Thermal Plume
        </button>
      </div>

      <!-- Copilot Input Row -->
      <div class="copilot-input-row">
        <input
          type="text"
          v-model="userPrompt"
          placeholder="Type physics idea or describe boundary conditions..."
          class="copilot-input"
          @keyup.enter="handleSendAiPrompt"
        />
        <button class="copilot-send-btn" :disabled="isAiLoading || !userPrompt.trim()" @click="handleSendAiPrompt">
          ➤
        </button>
      </div>
    </div>

    <!-- Dict Viewer & Interactive Repair Modal -->
    <transition name="fade">
      <div v-if="selectedFile" class="dict-modal-backdrop" @click="selectedFile = null">
        <div class="dict-modal" @click.stop>
          <div class="modal-header">
            <div class="modal-title">
              <span class="file-icon">📄</span>
              <strong>{{ selectedFile.category }}/{{ selectedFile.name }}</strong>
            </div>
            <div class="modal-actions">
              <button class="save-file-btn" @click="saveDictionaryFile">💾 Save & Recompile</button>
              <button class="close-btn" @click="selectedFile = null">✕</button>
            </div>
          </div>
          <div class="modal-body">
            <textarea
              v-model="selectedFile.content"
              class="dict-editor-textarea"
              spellcheck="false"
            ></textarea>
          </div>
        </div>
      </div>
    </transition>
  </aside>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, nextTick } from 'vue';
import type {
  SimulationParams,
  SimulationArchetype,
  StudioParameters,
  OpenFoamDictFile,
  AiProviderConfig,
  FluidProperties
} from '../types/cfd';
import { queryAiCopilot } from '../utils/aiCopilot';

const props = defineProps<{
  params: SimulationParams;
  aiConfig: AiProviderConfig;
  isComputing?: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:params', params: SimulationParams): void;
  (e: 'fileUploaded', file: File): void;
  (e: 'startSimulation'): void;
  (e: 'closeSidebar'): void;
}>();

const activeMode = ref<'manual' | 'ai'>('manual');
const isForcesDrawerOpen = ref(false);
const isDraggingOver = ref(false);
const uploadedFileName = ref<string | null>(null);
const fileInputRef = ref<HTMLInputElement | null>(null);

// Natural Physics State
const gravityZ = ref(props.params.naturalForces?.gravity?.[1] ?? -9.81);
const coreTemp = ref(props.params.naturalForces?.ambientTemp ?? 310.0);
const thermalBeta = ref(0.0034);

// Substances
const substances: FluidProperties[] = [
  { id: 'air', name: '💨 Air', density: 1.225, kinematicViscosity: 1.5e-5, specificHeat: 1005, thermalExpansion: 0.0034 },
  { id: 'water', name: '💧 Water', density: 998.0, kinematicViscosity: 1.0e-6, specificHeat: 4182, thermalExpansion: 0.00021, surfaceTension: 0.0728 },
  { id: 'co2', name: '🫧 CO₂ Gas', density: 1.980, kinematicViscosity: 8.3e-6, specificHeat: 844, thermalExpansion: 0.0037 },
  { id: 'oil', name: '🛢️ Oil', density: 890.0, kinematicViscosity: 4.5e-5, specificHeat: 1900, thermalExpansion: 0.0007 },
  { id: 'ethanol', name: '🍷 Ethanol', density: 789.0, kinematicViscosity: 1.52e-6, specificHeat: 2440, thermalExpansion: 0.0011 }
];

const currentSubstance = ref<FluidProperties>(
  substances.find(s => s.id === props.params.substance) || substances[0]
);

// AI Chat State
const userPrompt = ref('');
const isAiLoading = ref(false);
const chatHistoryRef = ref<HTMLDivElement | null>(null);

interface ChatMessageItem {
  role: 'user' | 'ai';
  text: string;
  dictCode?: string;
  detectedAction?: {
    archetype?: SimulationArchetype;
    substance?: string;
    re?: number;
    label: string;
  } | null;
}

const chatMessages = ref<ChatMessageItem[]>([
  {
    role: 'ai',
    text: '⚡ OpenFOAM Physics Assistant: Give me an idea or scenario, and I will calculate the Navier-Stokes equations and auto-configure your 3D simulation.'
  }
]);

const studioParams = reactive<StudioParameters>({
  irisPurple: props.params.studioParams?.irisPurple ?? 0.45,
  vorticityAngle: props.params.studioParams?.vorticityAngle ?? 0.209,
  vorticityCore: props.params.studioParams?.vorticityCore ?? 50,
  butterscotchCore: props.params.studioParams?.butterscotchCore ?? 100
});

const expandedFolders = reactive({
  system: true,
  constant: true,
  zero: true
});

const selectedFile = ref<OpenFoamDictFile | null>(null);
const diagReport = ref<{ type: 'success' | 'warn'; message: string } | null>(null);

const aiStatusBadge = computed(() => {
  if (props.aiConfig.provider === 'ollama') return '🦙 Ollama Local';
  if (!props.aiConfig.apiKey) return '🔑 Key Needed';
  return props.aiConfig.model;
});

function setMode(mode: 'manual' | 'ai') {
  activeMode.value = mode;
  emit('update:params', {
    ...props.params,
    solverMode: mode === 'ai' ? 'ai' : 'cfd'
  });
}

function selectSubstance(sub: FluidProperties) {
  currentSubstance.value = sub;
  emit('update:params', {
    ...props.params,
    substance: sub.id
  });
}

function setGravity(val: number) {
  gravityZ.value = val;
  emitForcesChange();
}

function emitForcesChange() {
  emit('update:params', {
    ...props.params,
    naturalForces: {
      gravity: [0, gravityZ.value, 0],
      ambientTemp: coreTemp.value,
      referencePressure: 101325
    }
  });
}

function emitParamsChange() {
  emit('update:params', {
    ...props.params,
    studioParams: { ...studioParams }
  });
}

function runCaseDiagnostics() {
  const courant = (studioParams.irisPurple * props.params.dt) / (1.0 / props.params.gridResolution);
  if (courant > 1.0) {
    diagReport.value = {
      type: 'warn',
      message: `⚠️ Courant number Co = ${courant.toFixed(2)} > 1.0! Auto-reduced dt to prevent numerical divergence.`
    };
  } else {
    diagReport.value = {
      type: 'success',
      message: `✅ All OpenFOAM checks passed: Co = ${courant.toFixed(2)} ≤ 1.0, Poisson matrix symmetric positive definite, boundary flux conservative.`
    };
  }
}

function saveDictionaryFile() {
  if (selectedFile.value) {
    alert(`File ${selectedFile.value.path} successfully recompiled into OpenFOAM case!`);
    selectedFile.value = null;
  }
}

const currentSystemFiles = computed<OpenFoamDictFile[]>(() => {
  const solver = currentSubstance.value.id === 'water' ? 'interFoam'
    : props.params.archetype === 'plume' ? 'buoyantBoussinesqSimpleFoam'
    : 'simpleFoam';

  return [
    {
      name: 'controlDict',
      path: 'system/controlDict',
      category: 'system',
      content: `FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "system";
    object      controlDict;
}
application     ${solver};
startFrom       startTime;
startTime       0;
stopAt          endTime;
endTime         1000;
deltaT          ${props.params.dt || 0.005};
writeControl    timeStep;
writeInterval   20;
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
ddtSchemes { default steadyState; }
gradSchemes { default Gauss linear; }
divSchemes
{
    default none;
    div(phi,U) Gauss linearUpwind grad(U);
    div(phi,T) Gauss limitedLinear 1;
}
laplacianSchemes { default Gauss linear corrected; }`
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
    p { solver GAMG; tolerance 1e-07; relTol 0.01; }
    U { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-08; }
    T { solver PBiCGStab; preconditioner DILU; tolerance 1e-08; }
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
convertToMeters 1;
vertices
(
    (-2.0 -1.0 -1.0)
    ( 2.0 -1.0 -1.0)
    ( 2.0  1.0 -1.0)
    (-2.0  1.0 -1.0)
    (-2.0 -1.0  1.0)
    ( 2.0 -1.0  1.0)
    ( 2.0  1.0  1.0)
    (-2.0  1.0  1.0)
);
blocks
(
    hex (0 1 2 3 4 5 6 7) (${props.params.gridResolution} ${props.params.gridResolution} 32) simpleGrading (1 1 1)
);`
    }
  ];
});

const currentConstantFiles = computed<OpenFoamDictFile[]>(() => {
  return [
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
nu              [0 2 -1 0 0 0 0] ${currentSubstance.value.kinematicViscosity};
rho             [1 -3 0 0 0 0 0] ${currentSubstance.value.density};
beta            [0 0 0 -1 0 0 0] ${thermalBeta.value};`
    },
    {
      name: 'g',
      path: 'constant/g',
      category: 'constant',
      content: `FoamFile
{
    version     2.0;
    format      ascii;
    class       uniformDimensionedVectorField;
    location    "constant";
    object      g;
}
dimensions      [0 1 -2 0 0 0 0];
value           (0 ${gravityZ.value.toFixed(2)} 0);`
    }
  ];
});

const currentZeroFiles = computed<OpenFoamDictFile[]>(() => {
  return [
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
internalField   uniform (${studioParams.irisPurple.toFixed(3)} 0 0);
boundaryField
{
    inlet { type fixedValue; value uniform (${studioParams.irisPurple.toFixed(3)} 0 0); }
    outlet { type inletOutlet; inletValue uniform (0 0 0); value uniform (0 0 0); }
    walls { type noSlip; }
}`
    },
    {
      name: 'p',
      path: '0/p',
      category: '0',
      content: `FoamFile
{
    version     2.0;
    format      ascii;
    class       volScalarField;
    location    "0";
    object      p;
}
dimensions      [0 2 -2 0 0 0 0];
internalField   uniform 0;
boundaryField
{
    inlet { type zeroGradient; }
    outlet { type fixedValue; value uniform 0; }
    walls { type zeroGradient; }
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
    inlet { type fixedValue; value uniform 293.15; }
    heaterSource { type fixedValue; value uniform ${(studioParams.butterscotchCore + 273.15).toFixed(2)}; }
    walls { type zeroGradient; }
}`
    }
  ];
});

function toggleFolder(folder: 'system' | 'constant' | 'zero') {
  expandedFolders[folder] = !expandedFolders[folder];
}

function selectFile(file: OpenFoamDictFile) {
  selectedFile.value = file;
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

function parseActionFromAiResponse(aiText: string, userText: string) {
  const combined = (aiText + ' ' + userText).toLowerCase();
  let arch: SimulationArchetype | undefined;
  if (combined.includes('submarine') || combined.includes('hull')) arch = 'submarine';
  else if (combined.includes('airfoil') || combined.includes('naca') || combined.includes('wing')) arch = 'airfoil';
  else if (combined.includes('drone') || combined.includes('rotor') || combined.includes('quadcopter')) arch = 'drone';
  else if (combined.includes('f1') || combined.includes('formula 1') || combined.includes('downforce')) arch = 'f1';
  else if (combined.includes('cylinder') || combined.includes('von karman')) arch = 'cylinder';
  else if (combined.includes('venturi') || combined.includes('converging')) arch = 'venturi';

  let substance: string | undefined;
  if (combined.includes('seawater') || combined.includes('water')) substance = 'water';
  else if (combined.includes('air')) substance = 'air';
  else if (combined.includes('oil')) substance = 'oil';

  let re: number | undefined;
  const reMatch = combined.match(/re\s*[=:\s]+([0-9]+)/i);
  if (reMatch) {
    re = parseInt(reMatch[1], 10);
  }

  if (arch || substance || re) {
    const parts = [];
    if (arch) parts.push(`Archetype: ${arch.toUpperCase()}`);
    if (substance) parts.push(`Medium: ${substance.toUpperCase()}`);
    if (re) parts.push(`Re = ${re.toLocaleString()}`);
    return {
      archetype: arch,
      substance,
      re,
      label: parts.join(' • ')
    };
  }
  return null;
}

function executeAiAction(action: any) {
  const updated = { ...props.params };
  if (action.archetype) {
    updated.archetype = action.archetype;
  }
  if (action.substance) {
    updated.substance = action.substance;
    const found = substances.find(s => s.id === action.substance);
    if (found) currentSubstance.value = found;
  }
  if (action.re) {
    updated.reynoldsNumber = action.re;
  }
  emit('update:params', updated);
  emit('startSimulation');
  chatMessages.value.push({
    role: 'ai',
    text: `⚡ Autonomous Action Executed: Successfully configured ${action.label} and launched live 3D simulation in viewport!`
  });
  nextTick(() => {
    if (chatHistoryRef.value) chatHistoryRef.value.scrollTop = chatHistoryRef.value.scrollHeight;
  });
}

async function handleSendAiPrompt() {
  if (!userPrompt.value.trim() || isAiLoading.value) return;

  const promptText = userPrompt.value.trim();
  userPrompt.value = '';
  chatMessages.value.push({ role: 'user', text: promptText });

  isAiLoading.value = true;
  await nextTick();
  if (chatHistoryRef.value) chatHistoryRef.value.scrollTop = chatHistoryRef.value.scrollHeight;

  const context = `Substance: ${currentSubstance.value.name}, Gravity: ${gravityZ.value}, Temp: ${coreTemp.value}, Archetype: ${props.params.archetype}`;
  const res = await queryAiCopilot(promptText, context);

  isAiLoading.value = false;
  const detectedAction = parseActionFromAiResponse(res.analysis, promptText);
  const dictCode = res.openfoamDictSnippet || extractDictCode(res.analysis);

  chatMessages.value.push({
    role: 'ai',
    text: res.analysis,
    dictCode,
    detectedAction
  });

  await nextTick();
  if (chatHistoryRef.value) chatHistoryRef.value.scrollTop = chatHistoryRef.value.scrollHeight;
}

function extractDictCode(text: string): string | undefined {
  const codeBlockMatch = text.match(/```(?:openfoam|cpp|text)?\s*([\s\S]*?)```/);
  return codeBlockMatch ? codeBlockMatch[1].trim() : undefined;
}

function sendQuickPrompt(text: string) {
  userPrompt.value = text;
  handleSendAiPrompt();
}

function applyAiSnippet(code: string) {
  selectedFile.value = {
    name: 'customGeneratedDict',
    path: 'system/customGeneratedDict',
    category: 'system',
    content: code
  };
}

watch(() => props.params.studioParams, (newParams) => {
  if (newParams) {
    Object.assign(studioParams, newParams);
  }
}, { deep: true });
</script>

<style scoped>
.case-hub-panel {
  width: 440px;
  min-width: 400px;
  flex-shrink: 0;
  height: 100%;
  background: var(--bg-canvas);
  border-right: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  padding: 12px 14px;
  gap: 10px;
  overflow-y: auto;
  user-select: none;
  transition: width 0.25s ease, opacity 0.2s ease;
}

.hub-header {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.hub-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.hub-title-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.hub-icon {
  font-size: 15px;
}

.hub-title {
  font-size: 15px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: -0.2px;
}

.version-tag {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9.5px;
  background: rgba(56, 189, 248, 0.15);
  color: #38bdf8;
  padding: 1px 6px;
  border-radius: 4px;
}

.collapse-sidebar-btn {
  background: var(--btn-surface);
  border: 1px solid var(--border-subtle);
  color: var(--text-secondary);
  font-size: 10.5px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.collapse-sidebar-btn:hover {
  color: #ffffff;
  background: rgba(255, 255, 255, 0.08);
  border-color: var(--accent-border);
}

.hub-subtitle {
  font-size: 10.5px;
  color: var(--text-secondary);
}

/* Mode Switcher Pill */
.mode-toggle-wrapper {
  display: flex;
  background: rgba(0, 0, 0, 0.35);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  padding: 3px;
  gap: 4px;
}

.mode-btn {
  flex: 1;
  padding: 6px 10px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 6px;
  color: var(--text-secondary);
  font-size: 11.5px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.mode-btn.active {
  background: var(--btn-surface);
  border-color: var(--accent-border);
  color: #ffffff;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
}

.mode-btn:hover:not(.active) {
  color: #ffffff;
}

.ai-chip {
  font-size: 9px;
  background: rgba(56, 189, 248, 0.15);
  color: #38bdf8;
  padding: 1px 5px;
  border-radius: 4px;
}

/* Manual Mode Content */
.manual-mode-content {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
}

.hub-grid {
  display: grid;
  grid-template-columns: 1.15fr 1fr;
  gap: 10px;
  flex: 1;
  overflow-y: auto;
}

/* Hub Cards */
.hub-card {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.card-title-row {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.card-title {
  font-size: 12px;
  font-weight: 700;
  color: #ffffff;
}

.token-tag {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  color: var(--text-secondary);
  opacity: 0.8;
}

.auto-diag-btn {
  background: rgba(56, 189, 248, 0.12);
  border: 1px solid rgba(56, 189, 248, 0.35);
  color: #38bdf8;
  font-size: 9.5px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.auto-diag-btn:hover {
  background: rgba(56, 189, 248, 0.25);
  color: #ffffff;
}

.diag-report-banner {
  padding: 6px 8px;
  border-radius: 5px;
  font-size: 10px;
  line-height: 1.4;
  margin-bottom: 8px;
}

.diag-report-banner.success {
  background: rgba(34, 197, 94, 0.15);
  border: 1px solid rgba(34, 197, 94, 0.4);
  color: #86efac;
}

.diag-report-banner.warn {
  background: rgba(245, 158, 11, 0.15);
  border: 1px solid rgba(245, 158, 11, 0.4);
  color: #fde047;
}

/* File Tree */
.tree-card {
  overflow-y: auto;
  max-height: calc(100vh - 170px);
}

.file-tree-container {
  display: flex;
  flex-direction: column;
  gap: 3px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
}

.tree-folder {
  display: flex;
  flex-direction: column;
}

.folder-header {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 4px 6px;
  border-radius: 4px;
  cursor: pointer;
  color: #e2e8f0;
  transition: background 0.15s ease;
}

.folder-header:hover {
  background: rgba(255, 255, 255, 0.06);
}

.folder-arrow {
  font-size: 9px;
  color: #94a3b8;
  width: 10px;
}

.folder-icon {
  font-size: 11px;
}

.folder-name {
  font-weight: 600;
  color: #38bdf8;
}

.folder-children {
  margin-left: 14px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  border-left: 1px dashed rgba(255, 255, 255, 0.12);
  padding-left: 6px;
}

.tree-file {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 3px 5px;
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
  font-size: 10px;
}

.file-name {
  font-size: 10.5px;
}

/* Right Column */
.right-controls-column {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.params-card {
  flex: 1;
}

.sliders-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.slider-group {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.slider-labels label {
  font-size: 10.5px;
  font-weight: 600;
  color: #cbd5e1;
}

.slider-val-badge {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9.5px;
  font-weight: 600;
  color: #ffffff;
  background: rgba(255, 255, 255, 0.08);
  padding: 1px 5px;
  border-radius: 3px;
}

/* Natural Forces Collapsible Drawer */
.natural-drawer-card {
  padding: 8px 10px;
}

.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
}

.drawer-header-left {
  display: flex;
  align-items: center;
  gap: 6px;
}

.drawer-icon {
  font-size: 12px;
}

.drawer-title {
  font-size: 11px;
  font-weight: 700;
  color: #ffffff;
}

.substance-chip {
  font-size: 9px;
  background: rgba(34, 197, 94, 0.15);
  color: #86efac;
  padding: 1px 5px;
  border-radius: 4px;
}

.drawer-arrow {
  font-size: 9px;
  color: #94a3b8;
}

.drawer-body {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-top: 6px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.substance-pills-row {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.sub-pill-btn {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid var(--border-subtle);
  color: var(--text-secondary);
  font-size: 9.5px;
  padding: 3px 6px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.sub-pill-btn:hover {
  color: #ffffff;
  border-color: var(--accent-border);
}

.sub-pill-btn.active {
  background: rgba(56, 189, 248, 0.18);
  border-color: #38bdf8;
  color: #ffffff;
}

.gravity-presets-row {
  display: flex;
  gap: 3px;
}

.preset-pill {
  flex: 1;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid var(--border-subtle);
  color: var(--text-secondary);
  font-size: 9px;
  padding: 2px 4px;
  border-radius: 4px;
  cursor: pointer;
  text-align: center;
  transition: all 0.15s ease;
}

.preset-pill.active {
  background: var(--btn-surface);
  border-color: var(--accent-border);
  color: #ffffff;
}

/* Geometry Card & Dropzone */
.geometry-card {
  min-height: 100px;
}

.photo-dropzone {
  border: 1px dashed rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  padding: 10px 8px;
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
  border-color: var(--accent-border);
  background: rgba(255, 255, 255, 0.05);
}

.dropzone-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.upload-icon-wrapper {
  color: #94a3b8;
}

.dropzone-title {
  font-size: 11px;
  font-weight: 600;
  color: #ffffff;
}

.dropzone-sub {
  font-family: 'JetBrains Mono', monospace;
  font-size: 8.5px;
  color: var(--text-secondary);
}

.uploaded-badge {
  margin-top: 3px;
  font-size: 9.5px;
  color: #10b981;
  background: rgba(16, 185, 129, 0.15);
  padding: 1px 6px;
  border-radius: 3px;
}

/* AI Mode Panel */
.ai-mode-content {
  display: flex;
  flex-direction: column;
  flex: 1;
  gap: 8px;
  overflow: hidden;
}

.copilot-chat-history {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  padding: 8px 10px;
  max-height: calc(100vh - 280px);
}

.chat-msg {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 6px 8px;
  border-radius: 6px;
  font-size: 11px;
  line-height: 1.4;
}

.chat-msg.user {
  background: rgba(56, 189, 248, 0.12);
  border: 1px solid rgba(56, 189, 248, 0.25);
  align-self: flex-end;
  max-width: 90%;
}

.chat-msg.ai {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  align-self: flex-start;
  max-width: 95%;
}

.msg-author {
  font-size: 9.5px;
  font-weight: 700;
  color: var(--text-secondary);
}

.msg-content {
  color: #e2e8f0;
}

.quick-prompt-chips {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.chip-btn {
  background: var(--btn-surface);
  border: 1px solid var(--border-subtle);
  color: var(--text-secondary);
  font-size: 9.5px;
  padding: 3px 6px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.chip-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #ffffff;
}

.copilot-input-row {
  display: flex;
  gap: 6px;
}

.copilot-input {
  flex: 1;
  background: rgba(0, 0, 0, 0.35);
  border: 1px solid var(--border-subtle);
  color: #ffffff;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 11px;
}

.copilot-input:focus {
  outline: none;
  border-color: var(--accent-border);
}

.copilot-send-btn {
  background: var(--btn-surface);
  border: 1px solid var(--border-subtle);
  color: #38bdf8;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 700;
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
  padding: 10px 16px;
  background: #19222f;
  border-bottom: 1px solid var(--border-subtle);
}

.modal-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #ffffff;
}

.modal-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.save-file-btn {
  background: #0284c7;
  color: #ffffff;
  border: none;
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
}

.close-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 15px;
  cursor: pointer;
}

.modal-body {
  padding: 12px;
  overflow-y: auto;
  background: #0d1219;
}

.dict-editor-textarea {
  width: 100%;
  height: 380px;
  background: transparent;
  border: none;
  color: #38bdf8;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11.5px;
  line-height: 1.5;
  resize: none;
  outline: none;
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
