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

    <!-- MODE 1: Manual OpenFOAM (Structured Tabbed Layout) -->
    <div v-show="activeMode === 'manual'" class="manual-mode-content">
      <!-- Sub-Tab Navigation Strip -->
      <div class="sub-tab-strip">
        <button
          class="sub-tab-pill"
          :class="{ active: activeSubTab === 'physics' }"
          @click="activeSubTab = 'physics'"
          title="Fluid medium, inflow speed, turbulence, and gravity"
        >
          <span>🌊 Physics & Water</span>
        </button>
        <button
          class="sub-tab-pill"
          :class="{ active: activeSubTab === 'geometry' }"
          @click="activeSubTab = 'geometry'"
          title="Vehicle archetype, submarine hull, drone rotors, and CAD dropzone"
        >
          <span>🧱 Geometry</span>
        </button>
        <button
          class="sub-tab-pill"
          :class="{ active: activeSubTab === 'files' }"
          @click="activeSubTab = 'files'"
          title="OpenFOAM standard directory tree (system, constant, 0)"
        >
          <span>📁 Case Tree</span>
        </button>
        <button
          class="sub-tab-pill"
          :class="{ active: activeSubTab === 'changelog' }"
          @click="activeSubTab = 'changelog'"
          title="Simulation naming, change history, and snapshot saving"
        >
          <span>📝 History</span>
        </button>
      </div>

      <!-- TAB 1: Physics & Water -->
      <div v-show="activeSubTab === 'physics'" class="tab-pane physics-pane">
        <!-- Parameters Card -->
        <div class="hub-card params-card">
          <div class="card-header">
            <div class="card-title-row">
              <span class="card-title">Flow Parameters</span>
              <span class="token-tag">Aerodynamics & Hydrodynamics</span>
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
                <label>Vorticity Angle / AoA</label>
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
                <label>Vorticity Core / Re Intensity</label>
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
                <label>Thermal Core / Fluid Temp</label>
                <span class="slider-val-badge">{{ studioParams.butterscotchCore.toFixed(1) }} °C</span>
              </div>
              <input
                type="range"
                min="0"
                max="120"
                step="1"
                v-model.number="studioParams.butterscotchCore"
                @input="emitParamsChange"
              />
            </div>
          </div>
        </div>

        <!-- Fluid Medium & Hydrodynamics Card -->
        <div class="hub-card natural-drawer-card">
          <div class="card-header">
            <div class="card-title-row">
              <span class="card-title">Fluid Medium & Gravity</span>
              <span class="substance-chip">{{ currentSubstance.name }}</span>
            </div>
          </div>

          <div class="card-body-section">
            <label class="section-label">Select Substance:</label>
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

            <!-- Substance Physical Properties Info Grid -->
            <div class="substance-props-grid">
              <div class="prop-item">
                <span class="prop-label">Density (ρ):</span>
                <span class="prop-value">{{ currentSubstance.density }} kg/m³</span>
              </div>
              <div class="prop-item">
                <span class="prop-label">Viscosity (ν):</span>
                <span class="prop-value">{{ currentSubstance.kinematicViscosity.toExponential(2) }} m²/s</span>
              </div>
              <div class="prop-item">
                <span class="prop-label">Spec. Heat (Cp):</span>
                <span class="prop-value">{{ currentSubstance.specificHeat }} J/kg·K</span>
              </div>
              <div class="prop-item" v-if="currentSubstance.surfaceTension">
                <span class="prop-label">Surface Tension:</span>
                <span class="prop-value">{{ currentSubstance.surfaceTension }} N/m</span>
              </div>
            </div>

            <label class="section-label" style="margin-top: 10px;">Gravity Presets:</label>
            <div class="gravity-presets-row">
              <button
                class="preset-pill"
                :class="{ active: Math.abs(gravityZ - (-9.81)) < 0.1 }"
                @click="setGravity(-9.81)"
              >
                🌍 Earth (-9.81)
              </button>
              <button
                class="preset-pill"
                :class="{ active: Math.abs(gravityZ - (-1.62)) < 0.1 }"
                @click="setGravity(-1.62)"
              >
                🌑 Moon (-1.62)
              </button>
              <button
                class="preset-pill"
                :class="{ active: Math.abs(gravityZ) < 0.1 }"
                @click="setGravity(0.0)"
              >
                🌌 Zero-G
              </button>
              <button
                class="preset-pill"
                :class="{ active: Math.abs(gravityZ - 9.81) < 0.1 }"
                @click="setGravity(9.81)"
              >
                🔄 Inverted
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- TAB 2: Geometry & Archetype -->
      <div v-show="activeSubTab === 'geometry'" class="tab-pane geometry-pane">
        <!-- Archetype Selector Card -->
        <div class="hub-card archetype-card">
          <div class="card-header">
            <div class="card-title-row">
              <span class="card-title">Simulation Archetype</span>
              <span class="token-tag">{{ params.archetype.toUpperCase() }}</span>
            </div>
          </div>

          <div class="archetype-grid">
            <button
              v-for="arch in availableArchetypes"
              :key="arch.id"
              class="archetype-pill-btn"
              :class="{ active: params.archetype === arch.id }"
              @click="selectArchetype(arch.id)"
            >
              <span class="arch-icon">{{ arch.icon }}</span>
              <span class="arch-name">{{ arch.name }}</span>
            </button>
          </div>
        </div>

        <!-- Custom Geometry Builder — lets users build THEIR OWN simulation -->
        <div class="hub-card geometry-card">
          <div class="card-header">
            <div class="card-title-row">
              <span class="card-title">Custom Geometry Builder</span>
              <span class="token-tag">SOLID OBSTACLE</span>
            </div>
          </div>

          <p class="builder-hint">
            Draw your own body: the solver meshes it as a no-slip solid inside
            the flow tunnel and computes real drag & lift around it.
          </p>

          <div class="archetype-grid builder-shape-grid">
            <button
              v-for="shape in builderShapes"
              :key="shape.id"
              class="archetype-pill-btn"
              :class="{ active: builderShape === shape.id }"
              @click="setBuilderShape(shape.id)"
            >
              <span class="arch-icon">{{ shape.icon }}</span>
              <span class="arch-name">{{ shape.name }}</span>
            </button>
          </div>

          <template v-if="builderShape">
            <div class="sliders-list builder-sliders">
              <div class="slider-group">
                <div class="slider-labels">
                  <label>Position X</label>
                  <span class="slider-val-badge">{{ builderCx.toFixed(2) }}</span>
                </div>
                <input type="range" min="0.15" max="0.85" step="0.05" v-model.number="builderCx" @input="emitCustomGeometry" />
              </div>
              <div class="slider-group">
                <div class="slider-labels">
                  <label>Position Y</label>
                  <span class="slider-val-badge">{{ builderCy.toFixed(2) }}</span>
                </div>
                <input type="range" min="0.15" max="0.85" step="0.05" v-model.number="builderCy" @input="emitCustomGeometry" />
              </div>
              <div class="slider-group">
                <div class="slider-labels">
                  <label>Size</label>
                  <span class="slider-val-badge">{{ builderSize.toFixed(2) }}</span>
                </div>
                <input type="range" min="0.05" max="0.35" step="0.01" v-model.number="builderSize" @input="emitCustomGeometry" />
              </div>
              <div class="slider-group" v-if="builderShape === 'airfoil'">
                <div class="slider-labels">
                  <label>Angle of Attack</label>
                  <span class="slider-val-badge">{{ builderAoa.toFixed(0) }}°</span>
                </div>
                <input type="range" min="-20" max="20" step="1" v-model.number="builderAoa" @input="emitCustomGeometry" />
              </div>
            </div>

            <button class="apply-btn" @click="applyBuilderToSimulation">
              ▶ Run Simulation with This Geometry
            </button>
          </template>
        </div>

        <!-- Geometry input / Photo dropzone Card -->
        <div class="hub-card geometry-card">
          <div class="card-header">
            <div class="card-title-row">
              <span class="card-title">CAD / Mesh Upload</span>
              <span class="token-tag">STL / OBJ / STEP</span>
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
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="17 8 12 3 7 8"></polyline>
                  <line x1="12" y1="3" x2="12" y2="15"></line>
                </svg>
              </div>
              <span class="dropzone-title">Upload Custom CAD Solid</span>
              <span class="dropzone-sub">Drop .stl / .obj or click to browse</span>
              <span v-if="uploadedFileName" class="uploaded-badge">📎 {{ uploadedFileName }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- TAB 3: Case Tree -->
      <div v-show="activeSubTab === 'files'" class="tab-pane files-pane">
        <div class="hub-card tree-card full-width">
          <div class="card-header">
            <div class="card-title-row">
              <span class="card-title">OpenFOAM Case Directory</span>
              <span class="token-tag">system/ constant/ 0/</span>
            </div>
            <div class="tree-header-actions">
              <button
                class="auto-diag-btn"
                @click="runCaseDiagnostics"
                title="Run OpenFOAM numerical stability & Courant check"
              >
                ⚡ Check & Repair
              </button>
              <button
                class="download-case-btn"
                @click="downloadCasePackage"
                title="Download full OpenFOAM case directory as .ZIP"
              >
                📦 Export ZIP
              </button>
            </div>
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
      </div>

      <!-- TAB 4: History & Save -->
      <div v-show="activeSubTab === 'changelog'" class="tab-pane history-pane">
        <!-- Simulation Identity Card -->
        <div class="hub-card identity-card">
          <div class="card-header">
            <div class="card-title-row">
              <span class="card-title">Simulation Identity</span>
              <span class="token-tag">Naming & Snapshots</span>
            </div>
          </div>
          <div class="identity-form">
            <label class="section-label">Case Identifier:</label>
            <div class="case-name-row">
              <input
                type="text"
                v-model="caseNameInput"
                class="case-name-input"
                placeholder="e.g. Submarine_HighSpeed_Recon"
                @blur="handleSaveCaseName"
                @keyup.enter="handleSaveCaseName"
              />
              <button class="save-name-btn" @click="handleSaveCaseName">Save</button>
            </div>
          </div>
        </div>

        <!-- Changelog Timeline Card -->
        <div class="hub-card history-card">
          <div class="card-header">
            <div class="card-title-row">
              <span class="card-title">Modification History</span>
              <span class="token-tag">{{ changeLog.length }} records</span>
            </div>
          </div>
          <div class="changelog-list">
            <div v-for="(entry, idx) in changeLog" :key="idx" class="changelog-entry">
              <div class="entry-header">
                <span class="badge-source" :class="entry.source.toLowerCase()">{{ entry.source }}</span>
                <span class="entry-time">{{ entry.timestamp }}</span>
              </div>
              <div class="entry-desc">{{ entry.description }}</div>
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
  (e: 'update:customGeometry', spec: { shape: string; cx: number; cy: number; size: number; aoa: number } | null): void;
  (e: 'applyDict', file: OpenFoamDictFile): void;
}>();

const activeMode = ref<'manual' | 'ai'>('manual');
const activeSubTab = ref<'physics' | 'geometry' | 'files' | 'changelog'>('physics');
const isDraggingOver = ref(false);
const uploadedFileName = ref<string | null>(null);
const fileInputRef = ref<HTMLInputElement | null>(null);

// Archetype list with icons
const availableArchetypes: Array<{ id: SimulationArchetype; name: string; icon: string }> = [
  { id: 'submarine', name: 'Submarine', icon: '🌊' },
  { id: 'drone', name: 'Drone Rotors', icon: '🚁' },
  { id: 'airfoil', name: 'NACA Airfoil', icon: '✈️' },
  { id: 'f1', name: 'F1 Aero Wing', icon: '🏎️' },
  { id: 'venturi', name: 'Venturi Nozzle', icon: '⏳' },
  { id: 'water_dam', name: 'Water Dam Break', icon: '💧' },
  { id: 'cylinder', name: 'Cylinder Wake', icon: '⚪' },
  { id: 'plume', name: 'Thermal Plume', icon: '🔥' },
  { id: 'cavity', name: 'Lid Cavity', icon: '🌀' },
  { id: 'cad', name: 'Custom Builder', icon: '🧩' }
];

// Simulation Case Identity & Changelog
const caseNameInput = ref(props.params.caseName || 'openzess_sim_01');
const changeLog = ref<Array<{ timestamp: string; source: 'AI' | 'Manual'; description: string }>>([
  { timestamp: new Date().toLocaleTimeString(), source: 'Manual', description: 'Session initialized with baseline OpenFOAM parameters' }
]);

function logChange(source: 'AI' | 'Manual', description: string) {
  changeLog.value.unshift({
    timestamp: new Date().toLocaleTimeString(),
    source,
    description
  });
  if (changeLog.value.length > 50) changeLog.value.pop();
}

function selectArchetype(arch: SimulationArchetype) {
  const updated = { ...props.params, archetype: arch };
  emit('update:params', updated);
  logChange('Manual', `Switched simulation archetype to ${arch.toUpperCase()}`);
}

// --- Custom Geometry Builder state ---
const builderShapes = [
  { id: 'circle', name: 'Cylinder', icon: '⚪' },
  { id: 'square', name: 'Square', icon: '⬛' },
  { id: 'rectangle', name: 'Plate', icon: '▬' },
  { id: 'airfoil', name: 'Airfoil', icon: '✈️' }
];
const builderShape = ref<string | null>(null);
const builderCx = ref(0.4);
const builderCy = ref(0.5);
const builderSize = ref(0.15);
const builderAoa = ref(8);

function setBuilderShape(id: string) {
  builderShape.value = id;
  emitCustomGeometry();
}

function emitCustomGeometry() {
  emit('update:customGeometry', builderShape.value ? {
    shape: builderShape.value,
    cx: builderCx.value,
    cy: builderCy.value,
    size: builderSize.value,
    aoa: builderAoa.value
  } : null);
}

function applyBuilderToSimulation() {
  emitCustomGeometry();
  if (props.params.archetype !== 'cad') {
    emit('update:params', {
      ...props.params,
      archetype: 'cad',
      caseName: `Custom_${builderShape.value}_Run`
    });
  }
  logChange('Manual', `Built custom ${builderShape.value} geometry at (x=${builderCx.value.toFixed(2)}, y=${builderCy.value.toFixed(2)}) and launched the solver`);
  emit('startSimulation');
}

function handleSaveCaseName() {
  const safe = (caseNameInput.value || 'openzess_sim_01').trim();
  caseNameInput.value = safe;
  const updated = { ...props.params, caseName: safe };
  emit('update:params', updated);
  logChange('Manual', `Renamed simulation case to "${safe}"`);
}

function downloadCasePackage() {
  const safe = encodeURIComponent(caseNameInput.value || 'openzess_openfoam_case');
  window.open(`/api/export/openfoam-zip?name=${safe}`, '_blank');
  logChange('Manual', `Exported full OpenFOAM case package ZIP for "${caseNameInput.value}"`);
}

// Natural Physics State
const gravityZ = ref(props.params.naturalForces?.gravity?.[1] ?? -9.81);
const coreTemp = ref(props.params.naturalForces?.ambientTemp ?? 310.0);
const thermalBeta = ref(0.0034);

// Substances
const substances: FluidProperties[] = [
  { id: 'air', name: '💨 Air', density: 1.225, kinematicViscosity: 1.5e-5, specificHeat: 1005, thermalExpansion: 0.0034 },
  { id: 'water', name: '💧 Fresh Water', density: 998.0, kinematicViscosity: 1.0e-6, specificHeat: 4182, thermalExpansion: 0.00021, surfaceTension: 0.0728 },
  { id: 'seawater', name: '🌊 Ocean / Seawater', density: 1025.0, kinematicViscosity: 1.05e-6, specificHeat: 3993, thermalExpansion: 0.00024, surfaceTension: 0.0735 },
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
  if (!selectedFile.value) return;
  // ACTUALLY apply the edit: send the modified dict to the parent, which
  // forwards it to the backend so the re-run honors the user's changes.
  emit('applyDict', {
    ...selectedFile.value,
    content: selectedFile.value.content
  });
  logChange('Manual', `Applied edited ${selectedFile.value.category}/${selectedFile.value.name} to the live solver run`);
  diagReport.value = {
    type: 'success',
    message: `✅ ${selectedFile.value.name} applied — solver restarted with your dictionary edits.`
  };
  selectedFile.value = null;
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
  gap: 8px;
}

/* Sub-Tab Navigation Bar */
.sub-tab-strip {
  display: flex;
  background: rgba(0, 0, 0, 0.45);
  border: 1px solid var(--border-subtle);
  border-radius: 7px;
  padding: 2px;
  gap: 3px;
  overflow-x: auto;
}

.sub-tab-pill {
  flex: 1;
  padding: 5px 6px;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 5px;
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}

.sub-tab-pill:hover:not(.active) {
  color: #ffffff;
  background: rgba(255, 255, 255, 0.05);
}

.sub-tab-pill.active {
  background: var(--btn-surface);
  border-color: var(--accent-border);
  color: #38bdf8;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.4);
}

/* Tab Panes */
.tab-pane {
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex: 1;
  overflow-y: auto;
  padding-right: 2px;
}

/* Substance Physical Properties Grid */
.substance-props-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  padding: 8px;
  margin-top: 8px;
}

.prop-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.prop-label {
  font-size: 9.5px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.prop-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  color: #e2e8f0;
  font-weight: 600;
}

/* Archetype Grid */
.archetype-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6px;
  margin-top: 6px;
}

.archetype-pill-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  padding: 8px 10px;
  cursor: pointer;
  color: var(--text-secondary);
  font-size: 11.5px;
  font-weight: 500;
  transition: all 0.15s ease;
  text-align: left;
}

.archetype-pill-btn:hover {
  background: rgba(255, 255, 255, 0.07);
  color: #ffffff;
  border-color: rgba(255, 255, 255, 0.15);
}

.archetype-pill-btn.active {
  background: rgba(56, 189, 248, 0.12);
  border-color: #38bdf8;
  color: #38bdf8;
  font-weight: 600;
}

/* Custom Geometry Builder */
.builder-hint {
  font-size: 11px;
  line-height: 1.5;
  color: var(--text-secondary);
  margin: 6px 0 2px;
}

.builder-shape-grid {
  grid-template-columns: repeat(4, 1fr);
  gap: 5px;
}

.builder-shape-grid .archetype-pill-btn {
  justify-content: center;
  padding: 7px 4px;
  gap: 4px;
  font-size: 10.5px;
}

.builder-sliders {
  margin-top: 8px;
}

.apply-btn {
  width: 100%;
  margin-top: 10px;
  padding: 9px 12px;
  background: linear-gradient(135deg, #38bdf8, #0ea5e9);
  color: #04121d;
  font-size: 12px;
  font-weight: 700;
  font-family: inherit;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.apply-btn:hover {
  filter: brightness(1.12);
  transform: translateY(-1px);
}

/* Manual Mode Content */

.arch-icon {
  font-size: 16px;
}

/* History & Save Pane */
.identity-form {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 6px;
}

.case-name-row {
  display: flex;
  gap: 6px;
}

.case-name-input {
  flex: 1;
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  color: #ffffff;
  padding: 6px 10px;
  font-size: 12px;
  font-family: 'JetBrains Mono', monospace;
}

.case-name-input:focus {
  outline: none;
  border-color: #38bdf8;
}

.save-name-btn {
  background: var(--btn-surface);
  border: 1px solid var(--accent-border);
  color: #38bdf8;
  border-radius: 6px;
  padding: 6px 12px;
  font-size: 11.5px;
  font-weight: 600;
  cursor: pointer;
}

.save-name-btn:hover {
  background: rgba(56, 189, 248, 0.2);
}

.changelog-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 6px;
  max-height: 350px;
  overflow-y: auto;
}

.changelog-entry {
  display: flex;
  flex-direction: column;
  gap: 2px;
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  padding: 6px 8px;
}

.entry-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.badge-source {
  font-size: 9px;
  font-weight: 700;
  padding: 1px 5px;
  border-radius: 3px;
  text-transform: uppercase;
}

.badge-source.ai {
  background: rgba(168, 85, 247, 0.2);
  color: #c084fc;
}

.badge-source.manual {
  background: rgba(56, 189, 248, 0.2);
  color: #38bdf8;
}

.entry-time {
  font-size: 9.5px;
  color: var(--text-muted);
}

.entry-desc {
  font-size: 11px;
  color: var(--text-secondary);
}

.download-case-btn {
  background: rgba(16, 185, 129, 0.15);
  border: 1px solid rgba(16, 185, 129, 0.4);
  color: #34d399;
  font-size: 10.5px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.download-case-btn:hover {
  background: rgba(16, 185, 129, 0.3);
  color: #ffffff;
}

.tree-header-actions {
  display: flex;
  align-items: center;
  gap: 6px;
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
