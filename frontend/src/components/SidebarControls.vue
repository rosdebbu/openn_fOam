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

    <!-- AI Copilot Prompt Box (Shown in AI Mode) -->
    <div v-if="activeMode === 'ai'" class="ai-copilot-box">
      <div class="copilot-header">
        <span class="copilot-title">🤖 AI CFD Copilot</span>
        <span class="ai-badge">{{ aiStatusBadge }}</span>
      </div>

      <div class="copilot-chat-history" ref="chatHistoryRef">
        <div v-for="(msg, i) in chatMessages" :key="i" class="chat-msg" :class="msg.role">
          <div class="msg-author">{{ msg.role === 'user' ? '👤 You' : '⚡ AI Copilot' }}</div>
          <div class="msg-content">{{ msg.text }}</div>
          <button
            v-if="msg.dictCode"
            class="apply-snippet-btn"
            @click="applyAiSnippet(msg.dictCode)"
          >
            📋 Apply to OpenFOAM Case
          </button>
        </div>
        <div v-if="isAiLoading" class="chat-msg ai loading">
          <div class="msg-author">⚡ AI Copilot</div>
          <div class="msg-content">🧠 Computing fluid equations & OpenFOAM setup...</div>
        </div>
      </div>

      <!-- Quick Action Chips -->
      <div class="quick-prompt-chips">
        <button class="chip-btn" @click="sendQuickPrompt('Generate NACA 0012 angle of attack 12 deg setup')">
          ✈️ 12° Airfoil
        </button>
        <button class="chip-btn" @click="sendQuickPrompt('Tune GAMG solver tolerances for fast convergence')">
          ⚡ GAMG Tuning
        </button>
        <button class="chip-btn" @click="sendQuickPrompt('Setup Von Kármán vortex shedding at Re=200')">
          🔴 Re=200 Shedding
        </button>
      </div>

      <!-- Copilot Input -->
      <div class="copilot-input-row">
        <input
          type="text"
          v-model="userPrompt"
          placeholder="Ask AI Copilot to modify simulation or generate dicts..."
          class="copilot-input"
          @keyup.enter="handleSendAiPrompt"
        />
        <button class="copilot-send-btn" :disabled="isAiLoading || !userPrompt.trim()" @click="handleSendAiPrompt">
          ➤
        </button>
      </div>
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

      <!-- Right Column: Parameters & Geometry Input Cards -->
      <div class="right-controls-column">
        <!-- Card 2: Parameters Card (Dynamically labeled by Archetype) -->
        <div class="hub-card params-card">
          <div class="card-header">
            <span class="card-title">Parameters</span>
            <span class="token-tag">oklch(67.3% 0.182 278.935)</span>
          </div>

          <div class="sliders-list">
            <!-- Slider 1 -->
            <div class="slider-group">
              <div class="slider-labels">
                <label>{{ sliderLabels.s1 }}</label>
                <span class="slider-val-badge">{{ studioParams.irisPurple.toFixed(3) }}</span>
              </div>
              <input
                type="range"
                min="0.01"
                max="1.5"
                step="0.001"
                v-model.number="studioParams.irisPurple"
                @input="emitParamsChange"
              />
            </div>

            <!-- Slider 2 -->
            <div class="slider-group">
              <div class="slider-labels">
                <label>{{ sliderLabels.s2 }}</label>
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

            <!-- Slider 3 -->
            <div class="slider-group">
              <div class="slider-labels">
                <label>{{ sliderLabels.s3 }}</label>
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

            <!-- Slider 4 -->
            <div class="slider-group">
              <div class="slider-labels">
                <label>{{ sliderLabels.s4 }}</label>
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
import { ref, reactive, computed, watch, nextTick } from 'vue';
import type { SimulationParams, StudioParameters, OpenFoamDictFile, AiProviderConfig } from '../types/cfd';
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

const activeMode = ref<'ai' | 'manual'>('ai');
const isDraggingOver = ref(false);
const uploadedFileName = ref<string | null>(null);
const fileInputRef = ref<HTMLInputElement | null>(null);

// AI Chat State
const userPrompt = ref('');
const isAiLoading = ref(false);
const chatHistoryRef = ref<HTMLDivElement | null>(null);
const chatMessages = ref<{ role: 'user' | 'ai'; text: string; dictCode?: string }[]>([
  {
    role: 'ai',
    text: '⚡ Hello! I am your OpenZess AI Copilot. Ask me to setup boundary conditions, generate OpenFOAM dictionaries, or tune solver tolerances.'
  }
]);

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

const aiStatusBadge = computed(() => {
  if (props.aiConfig.provider === 'ollama') return '🦙 Ollama Local';
  if (!props.aiConfig.apiKey) return '🔑 Key Needed';
  return props.aiConfig.model;
});

// Dynamic slider labels per archetype
const sliderLabels = computed(() => {
  switch (props.params.archetype) {
    case 'airfoil':
      return { s1: 'Airspeed U∞ (m/s)', s2: 'Angle of Attack (α)', s3: 'Reynolds Scale', s4: 'Wing Chord (mm)' };
    case 'cylinder':
      return { s1: 'Free-stream U (m/s)', s2: 'Vortex Angle', s3: 'Vortex Core Re', s4: 'Diameter (mm)' };
    case 'venturi':
      return { s1: 'Inlet Velocity', s2: 'Diffuser Angle', s3: 'Throat Ratio', s4: 'Inlet Pressure' };
    case 'cavity':
      return { s1: 'Lid Velocity', s2: 'Shear Angle', s3: 'Grid Resolution', s4: 'Cavity Width' };
    case 'plume':
    default:
      return { s1: 'Iris Purple', s2: 'Vorticity angle', s3: 'Vorticity core', s4: 'Butterscotch core' };
  }
});

// Dynamic OpenFOAM dictionaries based on archetype
const currentSystemFiles = computed<OpenFoamDictFile[]>(() => {
  const solver = props.params.archetype === 'airfoil' ? 'simpleFoam'
    : props.params.archetype === 'cylinder' ? 'pimpleFoam'
    : props.params.archetype === 'venturi' ? 'rhoSimpleFoam'
    : props.params.archetype === 'cavity' ? 'icoFoam'
    : 'buoyantBoussinesqSimpleFoam';

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
deltaT          1;
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
ddtSchemes { default steadyState; }
gradSchemes { default Gauss linear; }
divSchemes {
    default none;
    div(phi,U) Gauss linearUpwind grad(U);
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
blocks ( hex (0 1 2 3 4 5 6 7) (80 40 20) simpleGrading (1 1 1) );`
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
nu              [0 2 -1 0 0 0 0] 1.5e-05;`
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
RAS { RASModel kEpsilon; turbulence on; }`
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

async function handleSendAiPrompt() {
  if (!userPrompt.value.trim() || isAiLoading.value) return;

  const promptText = userPrompt.value.trim();
  userPrompt.value = '';
  chatMessages.value.push({ role: 'user', text: promptText });

  isAiLoading.value = true;
  await nextTick();
  if (chatHistoryRef.value) chatHistoryRef.value.scrollTop = chatHistoryRef.value.scrollHeight;

  const context = `Archetype: ${props.params.archetype}, Re: ${props.params.reynoldsNumber}, Params: ${JSON.stringify(studioParams)}`;
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
  gap: 12px;
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

/* AI Copilot Box */
.ai-copilot-box {
  background: rgba(20, 26, 36, 0.9);
  border: 1px solid rgba(168, 85, 247, 0.3);
  border-radius: 10px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 220px;
}

.copilot-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.copilot-title {
  font-size: 12px;
  font-weight: 700;
  color: #e9d5ff;
}

.ai-badge {
  font-family: 'JetBrains Mono', monospace;
  font-size: 9.5px;
  background: rgba(168, 85, 247, 0.2);
  color: #c084fc;
  padding: 2px 6px;
  border-radius: 4px;
}

.copilot-chat-history {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 90px;
  padding-right: 4px;
}

.chat-msg {
  padding: 6px 8px;
  border-radius: 6px;
  font-size: 11px;
}

.chat-msg.user {
  background: rgba(56, 189, 248, 0.1);
  border-left: 2px solid #38bdf8;
}

.chat-msg.ai {
  background: rgba(168, 85, 247, 0.1);
  border-left: 2px solid #a855f7;
}

.msg-author {
  font-weight: 700;
  font-size: 9.5px;
  color: #94a3b8;
  margin-bottom: 2px;
}

.msg-content {
  color: #e2e8f0;
  white-space: pre-wrap;
}

.apply-snippet-btn {
  margin-top: 4px;
  padding: 3px 8px;
  background: #a855f7;
  color: #ffffff;
  border: none;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
  cursor: pointer;
}

.quick-prompt-chips {
  display: flex;
  gap: 6px;
  overflow-x: auto;
}

.chip-btn {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 3px 8px;
  font-size: 10px;
  color: #cbd5e1;
  cursor: pointer;
  white-space: nowrap;
}

.chip-btn:hover {
  background: rgba(168, 85, 247, 0.2);
  color: #ffffff;
}

.copilot-input-row {
  display: flex;
  gap: 6px;
}

.copilot-input {
  flex: 1;
  background: #0f151e;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  padding: 6px 10px;
  color: #f1f5f9;
  font-size: 11.5px;
  outline: none;
}

.copilot-input:focus {
  border-color: #a855f7;
}

.copilot-send-btn {
  background: linear-gradient(135deg, #a855f7, #6366f1);
  border: none;
  border-radius: 6px;
  color: white;
  padding: 0 12px;
  cursor: pointer;
  font-size: 12px;
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
  max-height: calc(100vh - 200px);
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
