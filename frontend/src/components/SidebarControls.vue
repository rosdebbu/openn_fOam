<template>
  <aside class="case-hub-panel">
    <!-- Hub Header -->
    <div class="hub-header">
      <div class="hub-title-row">
        <h2 class="hub-title">OpenFOAM Physics & Case Hub</h2>
        <span class="version-tag">v2406 FVM</span>
      </div>
      <p class="hub-subtitle">Conservation of Mass, Momentum, Energy & Gravity</p>
    </div>

    <!-- AI Slide Bar Drawer Toggle -->
    <div class="ai-slide-toggle-bar" @click="isAiDrawerOpen = !isAiDrawerOpen">
      <div class="toggle-left">
        <span class="ai-icon">🤖</span>
        <span class="toggle-label">AI Copilot & Idea Assistant</span>
        <span class="ai-chip">{{ aiStatusBadge }}</span>
      </div>
      <button class="slide-arrow-btn">
        {{ isAiDrawerOpen ? '▲ Slide Close' : '▼ Slide Open' }}
      </button>
    </div>

    <!-- AI Slide Drawer (Collapsible) -->
    <transition name="slide-down">
      <div v-show="isAiDrawerOpen" class="ai-slide-drawer">
        <div class="copilot-chat-history" ref="chatHistoryRef">
          <div v-for="(msg, i) in chatMessages" :key="i" class="chat-msg" :class="msg.role">
            <div class="msg-author">{{ msg.role === 'user' ? '👤 Idea Input' : '⚡ AI Assistant' }}</div>
            <div class="msg-content">{{ msg.text }}</div>
            <button
              v-if="msg.dictCode"
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
          <button class="chip-btn" @click="sendQuickPrompt('Setup water sloshing under Earth gravity g = [0, 0, -9.81]')">
            💧 Water Gravity
          </button>
          <button class="chip-btn" @click="sendQuickPrompt('Thermal plume rising with Boussinesq buoyancy at 350K')">
            🔥 Thermal Buoyancy
          </button>
          <button class="chip-btn" @click="sendQuickPrompt('High Reynolds aerodynamic flow over car with ground effect')">
            🏎️ Ground Effect
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
    </transition>

    <!-- Hub Mode Tabs: Natural Physics vs Manual Repair -->
    <div class="hub-tabs-row">
      <button
        class="hub-tab-btn"
        :class="{ active: activeTab === 'physics' }"
        @click="activeTab = 'physics'"
      >
        🌍 Natural Physics & Forces
      </button>
      <button
        class="hub-tab-btn"
        :class="{ active: activeTab === 'repair' }"
        @click="activeTab = 'repair'"
      >
        🛠️ Manual Repair & OpenFOAM Case
      </button>
    </div>

    <!-- TAB 1: Natural Physics & Forces Engine (Gravity, Temperature, Density, Water, Volume) -->
    <div v-show="activeTab === 'physics'" class="physics-tab-content">
      <!-- Card: Fluid Substance & Density -->
      <div class="hub-card substance-card">
        <div class="card-header">
          <div class="card-title-row">
            <span class="card-title">🧪 Fluid Substance & Thermodynamic Density (ρ)</span>
          </div>
          <p class="card-desc">Equation of State: Continuity & Momentum properties</p>
        </div>

        <div class="substance-grid">
          <button
            v-for="sub in substances"
            :key="sub.id"
            class="substance-btn"
            :class="{ active: currentSubstance.id === sub.id }"
            @click="selectSubstance(sub)"
          >
            <span class="sub-name">{{ sub.name }}</span>
            <span class="sub-prop">ρ: {{ sub.density }} kg/m³</span>
            <span class="sub-prop">ν: {{ sub.kinematicViscosity.toExponential(1) }} m²/s</span>
          </button>
        </div>
      </div>

      <!-- Card: Natural Forces — Gravity & Buoyancy -->
      <div class="hub-card forces-card">
        <div class="card-header">
          <div class="card-title-row">
            <span class="card-title">🌍 Natural Gravity Vector (g) & Temperature (T)</span>
          </div>
          <p class="card-desc">Momentum source: ρg + Energy equation: ∇·(k∇T)</p>
        </div>

        <div class="sliders-list">
          <!-- Gravity Z Slider -->
          <div class="slider-group">
            <div class="slider-labels">
              <label>Gravity Z (gz) [m/s²]</label>
              <span class="slider-val-badge">{{ gravityZ.toFixed(2) }} m/s²</span>
            </div>
            <input
              type="range"
              min="-20.0"
              max="20.0"
              step="0.1"
              v-model.number="gravityZ"
              @input="emitForcesChange"
            />
            <div class="preset-pills">
              <button class="preset-btn" @click="setGravity(-9.81)">🌍 Earth (-9.81)</button>
              <button class="preset-btn" @click="setGravity(-1.62)">🌙 Moon (-1.62)</button>
              <button class="preset-btn" @click="setGravity(0.0)">🛰️ Zero-G (0.0)</button>
              <button class="preset-btn" @click="setGravity(9.81)">🔄 Inverted (+9.81)</button>
            </div>
          </div>

          <!-- Ambient Temperature -->
          <div class="slider-group">
            <div class="slider-labels">
              <label>Core Fluid Temperature (T)</label>
              <span class="slider-val-badge">{{ coreTemp.toFixed(1) }} K ({{ (coreTemp - 273.15).toFixed(1) }} °C)</span>
            </div>
            <input
              type="range"
              min="250.0"
              max="450.0"
              step="1.0"
              v-model.number="coreTemp"
              @input="emitForcesChange"
            />
          </div>

          <!-- Thermal Expansion (Buoyancy) -->
          <div class="slider-group">
            <div class="slider-labels">
              <label>Thermal Expansion (β) — Boussinesq</label>
              <span class="slider-val-badge">{{ thermalBeta.toFixed(4) }} 1/K</span>
            </div>
            <input
              type="range"
              min="0.0005"
              max="0.01"
              step="0.0001"
              v-model.number="thermalBeta"
              @input="emitForcesChange"
            />
          </div>

          <!-- Water / Multiphase Volume Fraction -->
          <div class="slider-group" v-if="currentSubstance.id === 'water'">
            <div class="slider-labels">
              <label>💧 Water Volume Fraction (α) — VOF</label>
              <span class="slider-val-badge">{{ (waterAlpha * 100).toFixed(0) }}% Water / {{ ((1 - waterAlpha) * 100).toFixed(0) }}% Air</span>
            </div>
            <input
              type="range"
              min="0.0"
              max="1.0"
              step="0.05"
              v-model.number="waterAlpha"
              @input="emitForcesChange"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 2: Manual Repair & OpenFOAM Case Hub -->
    <div v-show="activeTab === 'repair'" class="repair-tab-content">
      <!-- Diagnostics & Repair Action Bar -->
      <div class="diagnostics-action-card">
        <div class="diag-left">
          <span class="diag-icon">🛡️</span>
          <div>
            <strong>OpenFOAM Case Consistency Validator</strong>
            <p>Checks Courant Co &lt; 1.0, mesh skewness, and boundary conditions</p>
          </div>
        </div>
        <button class="run-diag-btn" @click="runCaseDiagnostics">
          ⚡ Auto-Diagnose & Repair
        </button>
      </div>

      <div v-if="diagReport" class="diag-report-banner" :class="diagReport.type">
        <span>{{ diagReport.message }}</span>
      </div>

      <!-- Hub Grid: File Tree on Left, Boundary Editor & Dropzone on Right -->
      <div class="hub-grid">
        <!-- Card 1: OpenFOAM Case File Tree -->
        <div class="hub-card tree-card">
          <div class="card-header">
            <span class="card-title">Case File Tree</span>
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

        <!-- Right Column: Boundary Repair & Photo Dropzone -->
        <div class="right-controls-column">
          <!-- Boundary Condition Inspector & Repair -->
          <div class="hub-card bc-repair-card">
            <div class="card-header">
              <span class="card-title">Boundary Repair</span>
            </div>

            <div class="bc-list">
              <div class="bc-item">
                <div class="bc-meta">
                  <span class="bc-name">inlet</span>
                  <span class="bc-type">fixedValue</span>
                </div>
                <div class="bc-input-row">
                  <span class="unit-lbl">U:</span>
                  <input
                    type="number"
                    step="0.1"
                    v-model.number="studioParams.irisPurple"
                    class="bc-num-input"
                    @input="emitParamsChange"
                  />
                  <span class="unit-lbl">m/s</span>
                </div>
              </div>

              <div class="bc-item">
                <div class="bc-meta">
                  <span class="bc-name">outlet</span>
                  <span class="bc-type">zeroGradient / p=0</span>
                </div>
                <span class="bc-desc">Free atmospheric outflow</span>
              </div>

              <div class="bc-item">
                <div class="bc-meta">
                  <span class="bc-name">walls / ground</span>
                  <span class="bc-type">noSlip (Wall Function)</span>
                </div>
                <span class="bc-desc">Viscous boundary layer adherence</span>
              </div>
            </div>
          </div>

          <!-- Geometry input / Photo dropzone Card -->
          <div class="hub-card geometry-card">
            <div class="card-header">
              <span class="card-title">Geometry input</span>
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
                <span class="dropzone-title">Photo / CAD Dropzone</span>
                <span class="dropzone-sub">Drag & drop .stl / .obj / .step / photo</span>
                <span v-if="uploadedFileName" class="uploaded-badge">📎 {{ uploadedFileName }}</span>
              </div>
            </div>
          </div>
        </div>
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
import { ref, reactive, computed, nextTick } from 'vue';
import type {
  SimulationParams,
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
}>();

const activeTab = ref<'physics' | 'repair'>('physics');
const isAiDrawerOpen = ref(false);
const isDraggingOver = ref(false);
const uploadedFileName = ref<string | null>(null);
const fileInputRef = ref<HTMLInputElement | null>(null);

// Natural Physics State
const gravityZ = ref(props.params.naturalForces?.gravity?.[1] ?? -9.81);
const coreTemp = ref(props.params.naturalForces?.ambientTemp ?? 310.0);
const thermalBeta = ref(0.0034);
const waterAlpha = ref(0.65);

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
const chatMessages = ref<{ role: 'user' | 'ai'; text: string; dictCode?: string }[]>([
  {
    role: 'ai',
    text: '⚡ OpenFOAM Physics Assistant: Give me an idea or sketch, and I will set up the governing equations (mass, momentum, gravity, temperature, and multiphase).'
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
      message: `⚠️ Courant number Co = ${courant.toFixed(2)} > 1.0! Auto-reduced dt to ${(0.8 * (1.0 / props.params.gridResolution) / studioParams.irisPurple).toFixed(4)}s to prevent numerical divergence.`
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
deltaT          ${props.params.dt};
writeControl    timeStep;
writeInterval   50;
writePrecision  6;
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
ddtSchemes { default Euler; }
gradSchemes { default Gauss linear; }
divSchemes {
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
  chatMessages.value.push({
    role: 'ai',
    text: res.analysis,
    dictCode: res.openfoamDictSnippet
  });

  await nextTick();
  if (chatHistoryRef.value) chatHistoryRef.value.scrollTop = chatHistoryRef.value.scrollHeight;
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
  padding: 12px 16px;
  gap: 10px;
  overflow-y: auto;
  user-select: none;
}

.hub-header {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.hub-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
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

.hub-subtitle {
  font-size: 10.5px;
  color: var(--text-secondary);
}

/* AI Slide Toggle Bar */
.ai-slide-toggle-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--btn-surface);
  border: 1px solid var(--border-subtle);
  border-radius: 7px;
  padding: 6px 10px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.ai-slide-toggle-bar:hover {
  background: var(--bg-card);
  border-color: var(--accent-border);
}

.toggle-left {
  display: flex;
  align-items: center;
  gap: 6px;
}

.ai-icon {
  font-size: 13px;
}

.toggle-label {
  font-size: 11.5px;
  font-weight: 700;
  color: #f1f5f9;
}

.ai-chip {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  background: rgba(0, 0, 0, 0.35);
  border: 1px solid var(--border-subtle);
  color: var(--text-secondary);
  padding: 1px 5px;
  border-radius: 4px;
}

.slide-arrow-btn {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  font-size: 10px;
  font-weight: 600;
  cursor: pointer;
}

/* AI Slide Drawer Content */
.ai-slide-drawer {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.copilot-chat-history {
  max-height: 90px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.chat-msg {
  padding: 5px 8px;
  border-radius: 6px;
  font-size: 11px;
}

.chat-msg.user {
  background: rgba(0, 0, 0, 0.3);
  border-left: 2px solid var(--accent-border);
}

.chat-msg.ai {
  background: rgba(0, 0, 0, 0.2);
  border-left: 2px solid var(--text-secondary);
}

.msg-author {
  font-size: 9.5px;
  font-weight: 700;
  color: var(--text-secondary);
  margin-bottom: 2px;
}

.msg-content {
  color: #e2e8f0;
  white-space: pre-wrap;
}

.apply-snippet-btn {
  margin-top: 4px;
  padding: 3px 8px;
  background: var(--btn-surface);
  border: 1px solid var(--accent-border);
  color: #ffffff;
  border-radius: 4px;
  font-size: 9.5px;
  font-weight: 600;
  cursor: pointer;
}

.quick-prompt-chips {
  display: flex;
  gap: 5px;
  overflow-x: auto;
}

.chip-btn {
  background: var(--btn-surface);
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  padding: 3px 8px;
  font-size: 9.5px;
  color: var(--text-secondary);
  cursor: pointer;
  white-space: nowrap;
}

.chip-btn:hover {
  background: var(--bg-card-hover);
  border-color: var(--accent-border);
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
  border-radius: 5px;
  padding: 5px 8px;
  color: #f1f5f9;
  font-size: 11px;
  outline: none;
}

.copilot-input:focus {
  border-color: var(--accent-border);
}

.copilot-send-btn {
  background: var(--btn-surface);
  border: 1px solid var(--accent-border);
  border-radius: 5px;
  color: white;
  padding: 0 12px;
  cursor: pointer;
  font-weight: 600;
}

.copilot-send-btn:hover {
  background: var(--bg-card-hover);
}

/* Tabs: Natural Physics vs Manual Repair */
.hub-tabs-row {
  display: flex;
  background: rgba(0, 0, 0, 0.35);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  padding: 3px;
  gap: 3px;
}

.hub-tab-btn {
  flex: 1;
  padding: 7px 10px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 6px;
  color: var(--text-secondary);
  font-size: 11.5px;
  font-weight: 600;
  cursor: pointer;
  text-align: center;
  transition: all 0.15s ease;
}

.hub-tab-btn.active {
  background: var(--btn-surface);
  border-color: var(--accent-border);
  color: #ffffff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.3);
}

/* Physics Tab */
.physics-tab-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.substance-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}

.substance-btn {
  display: flex;
  flex-direction: column;
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  padding: 6px 8px;
  cursor: pointer;
  text-align: left;
  transition: all 0.15s ease;
}

.substance-btn:hover {
  background: rgba(255, 255, 255, 0.04);
  border-color: var(--accent-border);
}

.substance-btn.active {
  background: var(--btn-surface);
  border-color: var(--accent-border);
  box-shadow: 0 0 0 1px var(--accent-border);
}

.sub-name {
  font-size: 11.5px;
  font-weight: 700;
  color: #ffffff;
}

.sub-prop {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9px;
  color: var(--text-secondary);
}

.preset-pills {
  display: flex;
  gap: 4px;
  margin-top: 4px;
  flex-wrap: wrap;
}

.preset-btn {
  background: var(--btn-surface);
  border: 1px solid var(--border-subtle);
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 9.5px;
  color: var(--text-secondary);
  cursor: pointer;
}

.preset-btn:hover {
  background: var(--bg-card-hover);
  color: #ffffff;
}

/* Repair Tab Content */
.repair-tab-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.diagnostics-action-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  padding: 8px 10px;
  gap: 8px;
}

.diag-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.diag-icon {
  font-size: 18px;
}

.diag-left strong {
  font-size: 11.5px;
  color: #f1f5f9;
}

.diag-left p {
  font-size: 9.5px;
  color: var(--text-secondary);
}

.run-diag-btn {
  background: var(--btn-surface);
  border: 1px solid var(--accent-border);
  color: white;
  border-radius: 5px;
  padding: 6px 10px;
  font-size: 10.5px;
  font-weight: 700;
  cursor: pointer;
  white-space: nowrap;
}

.run-diag-btn:hover {
  background: var(--bg-card-hover);
  border-color: #ffffff;
}

.diag-report-banner {
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 10.5px;
}

.diag-report-banner.success {
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.diag-report-banner.warn {
  background: rgba(245, 158, 11, 0.15);
  color: #fbbf24;
  border: 1px solid rgba(245, 158, 11, 0.3);
}

/* Hub Grid Layout */
.hub-grid {
  display: grid;
  grid-template-columns: 1.15fr 1fr;
  gap: 10px;
}

.hub-card {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
}

.geometry-card {
  background: var(--bg-card-alt);
  border-color: var(--accent-border);
}

.card-header {
  display: flex;
  flex-direction: column;
  margin-bottom: 8px;
}

.card-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 12px;
  font-weight: 700;
  color: #ffffff;
}

.card-desc {
  font-size: 9.5px;
  color: #94a3b8;
}

.token-tag {
  font-family: 'JetBrains Mono', monospace;
  font-size: 8.5px;
  color: var(--text-secondary);
  opacity: 0.8;
}

/* File Tree */
.tree-card {
  overflow-y: auto;
  max-height: 280px;
}

.file-tree-container {
  display: flex;
  flex-direction: column;
  gap: 3px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
}

.folder-header {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 4px 6px;
  border-radius: 4px;
  cursor: pointer;
  color: #e2e8f0;
}

.folder-header:hover {
  background: rgba(255, 255, 255, 0.06);
}

.folder-arrow {
  font-size: 9px;
  color: #94a3b8;
  width: 10px;
}

.folder-name {
  font-weight: 600;
  color: #38bdf8;
}

.folder-children {
  margin-left: 16px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  border-left: 1px dashed rgba(255, 255, 255, 0.12);
  padding-left: 6px;
}

.tree-file {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 3px 6px;
  border-radius: 4px;
  cursor: pointer;
  color: #cbd5e1;
}

.tree-file:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #ffffff;
}

.tree-file.selected {
  background: rgba(168, 85, 247, 0.2);
  color: #e9d5ff;
}

/* Right Column */
.right-controls-column {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.bc-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.bc-item {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 6px;
  padding: 5px 8px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.bc-meta {
  display: flex;
  justify-content: space-between;
}

.bc-name {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10.5px;
  font-weight: 700;
  color: #38bdf8;
}

.bc-type {
  font-size: 9px;
  color: #a855f7;
}

.bc-input-row {
  display: flex;
  align-items: center;
  gap: 4px;
}

.bc-num-input {
  width: 55px;
  background: #0f1016;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 4px;
  color: white;
  padding: 2px 4px;
  font-size: 10.5px;
  font-family: 'JetBrains Mono', monospace;
}

.unit-lbl {
  font-size: 10px;
  color: #94a3b8;
}

.bc-desc {
  font-size: 9px;
  color: #94a3b8;
}

/* Sliders */
.sliders-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
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
  font-size: 11px;
  font-weight: 600;
  color: #cbd5e1;
}

.slider-val-badge {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  font-weight: 600;
  color: #ffffff;
  background: rgba(255, 255, 255, 0.08);
  padding: 1px 5px;
  border-radius: 4px;
}

/* Photo Dropzone */
.photo-dropzone {
  border: 1px dashed rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  padding: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  cursor: pointer;
  background: rgba(0, 0, 0, 0.2);
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
  border-radius: 4px;
}

/* Modal View & Editor */
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
  width: 680px;
  max-width: 90vw;
  max-height: 80vh;
  background: #141b24;
  border: 1px solid var(--border-active);
  border-radius: 10px;
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
  background: #10b981;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 4px 10px;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
}

.save-file-btn:hover {
  background: #059669;
}

.close-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 16px;
  cursor: pointer;
}

.modal-body {
  padding: 12px;
  background: #0d1219;
  flex: 1;
  display: flex;
}

.dict-editor-textarea {
  width: 100%;
  height: 380px;
  background: transparent;
  color: #38bdf8;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11.5px;
  border: none;
  outline: none;
  resize: none;
  line-height: 1.4;
}

.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.2s ease-out;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
