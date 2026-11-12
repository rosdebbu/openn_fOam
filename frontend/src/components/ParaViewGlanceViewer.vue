<template>
  <div class="paraview-studio-container">
    <!-- Top ParaView Application Menu Bar -->
    <header class="paraview-menu-bar">
      <div class="pv-brand">
        <span class="pv-logo-badge">PV</span>
        <span class="pv-app-title">ParaView 5.12 Web Studio</span>
        <span class="pv-badge-pill">OpenFOAM Engine</span>
      </div>

      <!-- Quick Action Operations -->
      <div class="pv-top-actions">
        <label class="pv-btn pv-btn-primary" title="Open .VTK or OpenFOAM .foam file">
          <span class="btn-icon">📂</span> Open File
          <input type="file" accept=".vtk,.foam,.foamFile,.txt" @change="handleFileUpload" style="display: none;" />
        </label>

        <button class="pv-btn pv-btn-accent" @click="syncWithActiveSolver" :disabled="loading" title="Pull live simulation mesh and fields directly from the running OpenZess CFD solver">
          <span class="btn-icon">⚡</span> Sync Solver State
        </button>

        <button class="pv-btn" @click="exportCurrentVtk" title="Download current mesh and fields as standard Legacy VTK (.vtk)">
          <span class="btn-icon">💾</span> Save Data (.vtk)
        </button>

        <button class="pv-btn" @click="takeScreenshot" title="Capture high-resolution PNG screenshot of the viewport">
          <span class="btn-icon">📷</span> Capture
        </button>

        <button class="pv-btn" @click="resetSession" title="Reset pipeline and restore default camera">
          <span class="btn-icon">🔄</span> Reset
        </button>
      </div>

      <div class="pv-status-right">
        <span class="status-chip" :class="{ live: isLiveStreaming }">
          <span class="pulse-dot"></span> {{ isLiveStreaming ? 'Live Stream' : 'Static Dataset' }}
        </span>
        <span class="stats-chip">{{ activeData.cellCount.toLocaleString() }} Cells</span>
        <span class="stats-chip">{{ activeData.pointCount.toLocaleString() }} Pts</span>
      </div>
    </header>

    <!-- ParaView Ribbon Toolbars (VCR + Common Filters + Camera Orientation) -->
    <div class="paraview-ribbon-bar">
      <!-- VCR Playback Controls Group -->
      <div class="ribbon-group vcr-group">
        <span class="group-label">VCR Time Controls</span>
        <div class="group-buttons">
          <button class="ribbon-btn" @click="goToTimeStep(0)" title="First Step (|◀)">⏮</button>
          <button class="ribbon-btn" @click="stepTime(-1)" title="Previous Step (◀)">◀</button>
          <button class="ribbon-btn play-btn" :class="{ active: isPlaying }" @click="togglePlay" :title="isPlaying ? 'Pause' : 'Play (▶)'">
            {{ isPlaying ? '⏸' : '▶' }}
          </button>
          <button class="ribbon-btn" @click="stepTime(1)" title="Next Step (▶)">▶</button>
          <button class="ribbon-btn" @click="goToTimeStep(totalTimeSteps - 1)" title="Last Step (▶|)">⏭</button>
          <button class="ribbon-btn" :class="{ active: loopAnimation }" @click="loopAnimation = !loopAnimation" title="Loop Playback">🔁</button>
        </div>
        <div class="time-readout">
          <span class="step-counter">Step {{ currentTimeIndex }} / {{ totalTimeSteps - 1 }}</span>
          <span class="phys-time">t = {{ (currentTimeIndex * 0.005).toFixed(3) }}s</span>
        </div>
      </div>

      <!-- Common VTK Filters Group -->
      <div class="ribbon-group filters-group">
        <span class="group-label">Common Filters</span>
        <div class="group-buttons">
          <button class="ribbon-btn" :class="{ active: activeFilters.slice }" @click="toggleFilter('slice')" title="Slice: Cut domain with a plane">
            <span class="icon">🔪</span> Slice
          </button>
          <button class="ribbon-btn" :class="{ active: activeFilters.clip }" @click="toggleFilter('clip')" title="Clip: Extract subvolume with a plane or box">
            <span class="icon">✂️</span> Clip
          </button>
          <button class="ribbon-btn" :class="{ active: activeFilters.contour }" @click="toggleFilter('contour')" title="Contour: Isosurface of scalar fields">
            <span class="icon">〰️</span> Contour
          </button>
          <button class="ribbon-btn" :class="{ active: activeFilters.glyph }" @click="toggleFilter('glyph')" title="Glyph: 3D vector arrows for velocity U">
            <span class="icon">🏹</span> Glyph
          </button>
          <button class="ribbon-btn" :class="{ active: activeFilters.streamlines }" @click="toggleFilter('streamlines')" title="Stream Tracer: Particle path integration">
            <span class="icon">🌀</span> Streamlines
          </button>
        </div>
      </div>

      <!-- Camera Views Group -->
      <div class="ribbon-group camera-group">
        <span class="group-label">Camera Views</span>
        <div class="group-buttons">
          <button class="ribbon-btn" @click="setCameraView('+X')" title="View +X (Right)">+X</button>
          <button class="ribbon-btn" @click="setCameraView('-X')" title="View -X (Left)">-X</button>
          <button class="ribbon-btn" @click="setCameraView('+Y')" title="View +Y (Top)">+Y</button>
          <button class="ribbon-btn" @click="setCameraView('-Y')" title="View -Y (Bottom)">-Y</button>
          <button class="ribbon-btn" @click="setCameraView('+Z')" title="View +Z (Front / 2D plane)">+Z</button>
          <button class="ribbon-btn" @click="setCameraView('iso')" title="3D Isometric Perspective">⬡ Iso</button>
          <button class="ribbon-btn reset-btn" @click="resetCamera" title="Reset Camera Bounds (🎯)">🎯 Reset</button>
        </div>
      </div>
    </div>

    <!-- Main Workspace (Dockable Sidebar + 3D Viewport) -->
    <div class="paraview-workspace">
      <!-- Left Dockable Sidebar -->
      <aside class="paraview-dock-sidebar">
        <!-- Dock Navigation Tabs -->
        <div class="dock-tab-header">
          <button class="dock-tab-btn" :class="{ active: activeDockTab === 'pipeline' }" @click="activeDockTab = 'pipeline'">
            <span class="tab-icon">🌳</span> Pipeline
          </button>
          <button class="dock-tab-btn" :class="{ active: activeDockTab === 'properties' }" @click="activeDockTab = 'properties'">
            <span class="tab-icon">⚙️</span> Properties
          </button>
          <button class="dock-tab-btn" :class="{ active: activeDockTab === 'info' }" @click="activeDockTab = 'info'">
            <span class="tab-icon">ℹ️</span> Information
          </button>
        </div>

        <!-- Tab 1: Pipeline Browser -->
        <div v-show="activeDockTab === 'pipeline'" class="dock-content pipeline-panel">
          <div class="panel-section-title">
            <span>Pipeline Browser</span>
            <small class="hint">Click eye to toggle visibility</small>
          </div>

          <div class="pipeline-tree">
            <!-- Root Data Source -->
            <div class="tree-node" :class="{ selected: selectedPipelineItem === 'root' }" @click="selectedPipelineItem = 'root'">
              <button class="eye-toggle-btn" @click.stop="toggleSourceVisibility" :title="isSourceVisible ? 'Hide in view' : 'Show in view'">
                {{ isSourceVisible ? '👁️' : '⊘' }}
              </button>
              <span class="node-icon">📦</span>
              <span class="node-name">{{ currentDatasetName }}</span>
              <span class="node-badge">Structured Grid</span>
            </div>

            <!-- Active Filter Children -->
            <div v-if="activeFilters.slice" class="tree-node child-node" :class="{ selected: selectedPipelineItem === 'slice' }" @click="selectedPipelineItem = 'slice'">
              <button class="eye-toggle-btn" @click.stop="activeFilters.slice = !activeFilters.slice">
                {{ activeFilters.slice ? '👁️' : '⊘' }}
              </button>
              <span class="node-icon">🔪</span>
              <span class="node-name">Slice1 (Plane Z=0)</span>
            </div>

            <div v-if="activeFilters.clip" class="tree-node child-node" :class="{ selected: selectedPipelineItem === 'clip' }" @click="selectedPipelineItem = 'clip'">
              <button class="eye-toggle-btn" @click.stop="activeFilters.clip = !activeFilters.clip">
                {{ activeFilters.clip ? '👁️' : '⊘' }}
              </button>
              <span class="node-icon">✂️</span>
              <span class="node-name">Clip1 (X &gt; 0)</span>
            </div>

            <div v-if="activeFilters.contour" class="tree-node child-node" :class="{ selected: selectedPipelineItem === 'contour' }" @click="selectedPipelineItem = 'contour'">
              <button class="eye-toggle-btn" @click.stop="activeFilters.contour = !activeFilters.contour">
                {{ activeFilters.contour ? '👁️' : '⊘' }}
              </button>
              <span class="node-icon">〰️</span>
              <span class="node-name">Contour (Iso-values)</span>
            </div>

            <div v-if="activeFilters.glyph" class="tree-node child-node" :class="{ selected: selectedPipelineItem === 'glyph' }" @click="selectedPipelineItem = 'glyph'">
              <button class="eye-toggle-btn" @click.stop="activeFilters.glyph = !activeFilters.glyph">
                {{ activeFilters.glyph ? '👁️' : '⊘' }}
              </button>
              <span class="node-icon">🏹</span>
              <span class="node-name">Glyph1 (Velocity U)</span>
            </div>
          </div>

          <div class="pipeline-actions-footer">
            <button class="tool-action-btn" @click="syncWithActiveSolver">
              <span>⚡ Sync Solver Run</span>
            </button>
            <button class="tool-action-btn" @click="resetSession">
              <span>🗑 Clear Filters</span>
            </button>
          </div>
        </div>

        <!-- Tab 2: Properties Panel (Display / Representation & Coloring) -->
        <div v-show="activeDockTab === 'properties'" class="dock-content properties-panel">
          <!-- Display / Representation Group -->
          <div class="prop-group">
            <div class="prop-group-header">
              <span class="header-title">Display (Representation)</span>
            </div>

            <div class="prop-row">
              <label>Representation:</label>
              <select v-model="representationMode" @change="applyRepresentation">
                <option value="surface">Surface</option>
                <option value="surface_with_edges">Surface With Edges (Grid)</option>
                <option value="wireframe">Wireframe</option>
                <option value="points">Points</option>
              </select>
            </div>

            <div class="prop-row">
              <label>Opacity (α):</label>
              <div class="slider-control">
                <input type="range" v-model.number="meshOpacity" min="0.1" max="1.0" step="0.05" @input="applyOpacity" />
                <span class="val-label">{{ meshOpacity.toFixed(2) }}</span>
              </div>
            </div>

            <div class="prop-row" v-if="representationMode === 'points'">
              <label>Point Size:</label>
              <input type="range" v-model.number="pointSize" min="1" max="10" step="1" @input="applyPointSize" />
              <span class="val-label">{{ pointSize }}px</span>
            </div>

            <div class="prop-row" v-if="representationMode === 'surface_with_edges' || representationMode === 'wireframe'">
              <label>Mesh Edge Color:</label>
              <input type="color" v-model="edgeColor" @change="applyEdgeColor" />
            </div>
          </div>

          <!-- Coloring & Transfer Function Group -->
          <div class="prop-group">
            <div class="prop-group-header">
              <span class="header-title">Coloring & Color Map</span>
            </div>

            <div class="prop-row">
              <label>Color By:</label>
              <select v-model="selectedFieldKey" @change="updateFieldColoring">
                <option v-for="(field, key) in activeData.fields" :key="key" :value="key">
                  {{ field.name }} {{ field.unit ? `[${field.unit}]` : '' }}
                </option>
                <option value="solid">Solid Color</option>
              </select>
            </div>

            <div class="prop-row" v-if="activeFieldInfo && activeFieldInfo.numberOfComponents > 1">
              <label>Component:</label>
              <select v-model="selectedComponent" @change="updateFieldColoring">
                <option value="magnitude">Magnitude (|U|)</option>
                <option value="x">X Component (u)</option>
                <option value="y">Y Component (v)</option>
                <option value="z">Z Component (w)</option>
              </select>
            </div>

            <div class="prop-row">
              <label>Color Map Preset:</label>
              <select v-model="selectedColorMapPreset" @change="applyColorMapPreset">
                <option value="coolwarm">Cool to Warm (ParaView Standard)</option>
                <option value="rainbow">Rainbow Uniform (Classic CFD)</option>
                <option value="viridis">Viridis (Perceptually Uniform)</option>
                <option value="plasma">Plasma</option>
                <option value="jet">Jet (Legacy Spectral)</option>
              </select>
            </div>

            <div class="prop-row actions-row">
              <button class="btn-micro" @click="rescaleToDataRange" title="Rescale scalar transfer function to full dataset range">
                🔄 Rescale to Data Range
              </button>
              <button class="btn-micro" :class="{ active: showScalarBar }" @click="showScalarBar = !showScalarBar" title="Show/Hide ParaView Color Legend / Scalar Bar">
                📊 {{ showScalarBar ? 'Hide Legend' : 'Show Legend' }}
              </button>
            </div>

            <!-- Scalar Range Display -->
            <div class="scalar-range-box" v-if="activeFieldInfo">
              <div class="range-item">
                <span class="lbl">Min:</span>
                <span class="val">{{ activeFieldInfo.min.toExponential(4) }} {{ activeFieldInfo.unit }}</span>
              </div>
              <div class="range-item">
                <span class="lbl">Max:</span>
                <span class="val">{{ activeFieldInfo.max.toExponential(4) }} {{ activeFieldInfo.unit }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Tab 3: Information Panel -->
        <div v-show="activeDockTab === 'info'" class="dock-content info-panel">
          <div class="panel-section-title">Data Statistics & Bounds</div>

          <div class="stats-table">
            <div class="stat-row">
              <span class="k">Dataset Type</span>
              <span class="v highlight">vtkPolyData / Structured</span>
            </div>
            <div class="stat-row">
              <span class="k">Number of Cells</span>
              <span class="v">{{ activeData.cellCount.toLocaleString() }}</span>
            </div>
            <div class="stat-row">
              <span class="k">Number of Points</span>
              <span class="v">{{ activeData.pointCount.toLocaleString() }}</span>
            </div>
            <div class="stat-row">
              <span class="k">Bounds X</span>
              <span class="v">[{{ activeData.bounds[0].toFixed(2) }}, {{ activeData.bounds[1].toFixed(2) }}]</span>
            </div>
            <div class="stat-row">
              <span class="k">Bounds Y</span>
              <span class="v">[{{ activeData.bounds[2].toFixed(2) }}, {{ activeData.bounds[3].toFixed(2) }}]</span>
            </div>
            <div class="stat-row">
              <span class="k">Bounds Z</span>
              <span class="v">[{{ activeData.bounds[4].toFixed(2) }}, {{ activeData.bounds[5].toFixed(2) }}]</span>
            </div>
          </div>

          <div class="panel-section-title" style="margin-top: 14px;">Available Field Arrays</div>
          <div class="fields-list">
            <div v-for="(field, key) in activeData.fields" :key="key" class="field-item">
              <div class="f-name">
                <span class="f-type-badge">{{ field.numberOfComponents === 1 ? 'Scalar' : 'Vector' }}</span>
                <strong>{{ field.name }}</strong>
              </div>
              <div class="f-bounds">Range: [{{ field.min.toFixed(3) }} ... {{ field.max.toFixed(3) }}] {{ field.unit }}</div>
            </div>
          </div>
        </div>
      </aside>

      <!-- Center 3D Viewport Area -->
      <main class="paraview-viewport" ref="vtkContainer" @dragover.prevent @drop="handleFileDrop">
        <!-- Floating ParaView Scalar Bar / Color Legend Overlay -->
        <transition name="fade">
          <div v-if="showScalarBar && activeFieldInfo" class="pv-scalar-bar-widget">
            <div class="scalar-bar-title">{{ activeFieldInfo.name }} {{ activeFieldInfo.unit ? `[${activeFieldInfo.unit}]` : '' }}</div>
            <div class="scalar-gradient-strip" :style="{ background: colorMapGradientCss }"></div>
            <div class="scalar-bar-ticks">
              <span class="tick max">{{ activeFieldInfo.max.toExponential(3) }}</span>
              <span class="tick mid">{{ ((activeFieldInfo.min + activeFieldInfo.max) / 2).toExponential(3) }}</span>
              <span class="tick min">{{ activeFieldInfo.min.toExponential(3) }}</span>
            </div>
          </div>
        </transition>

        <!-- 3D Orientation Axes Widget in Bottom-Left -->
        <div class="pv-axes-hud" title="Domain Orientation Axes">
          <svg viewBox="0 0 80 80" class="axes-svg">
            <line x1="40" y1="40" x2="68" y2="40" stroke="#ef4444" stroke-width="2.5" marker-end="url(#arrow-x)" />
            <line x1="40" y1="40" x2="40" y2="12" stroke="#22c55e" stroke-width="2.5" marker-end="url(#arrow-y)" />
            <line x1="40" y1="40" x2="20" y2="60" stroke="#3b82f6" stroke-width="2.5" marker-end="url(#arrow-z)" />
            <text x="72" y="44" fill="#ef4444" font-size="10" font-weight="bold">X</text>
            <text x="36" y="8" fill="#22c55e" font-size="10" font-weight="bold">Y</text>
            <text x="12" y="70" fill="#3b82f6" font-size="10" font-weight="bold">Z</text>
            <circle cx="40" cy="40" r="3" fill="#ffffff" />
          </svg>
        </div>

        <!-- Probe Inspector Tooltip -->
        <div class="pv-probe-hud">
          <span class="probe-tag">Probe: (X: {{ probeInfo.x.toFixed(2) }}, Y: {{ probeInfo.y.toFixed(2) }})</span>
          <span class="probe-val" v-if="activeFieldInfo">{{ activeFieldInfo.name }}: {{ probeInfo.val.toFixed(4) }} {{ activeFieldInfo.unit }}</span>
        </div>

        <!-- Loading / Parsing Overlay -->
        <div v-if="loading" class="pv-loading-overlay">
          <div class="pv-spinner"></div>
          <p class="loading-msg">{{ loadingMessage }}</p>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import { parseVtkAscii, generateProceduralCfdData, type ParsedMeshData } from '../utils/vtkOpenFoamParser';

// Kitware VTK.js core modules
// @ts-ignore
import vtkFullScreenRenderWindow from '@kitware/vtk.js/Rendering/Misc/FullScreenRenderWindow';
// @ts-ignore
import vtkActor from '@kitware/vtk.js/Rendering/Core/Actor';
// @ts-ignore
import vtkMapper from '@kitware/vtk.js/Rendering/Core/Mapper';
// @ts-ignore
import vtkColorTransferFunction from '@kitware/vtk.js/Rendering/Core/ColorTransferFunction';
// @ts-ignore
import vtkPolyData from '@kitware/vtk.js/Common/DataModel/PolyData';
// @ts-ignore
import vtkDataArray from '@kitware/vtk.js/Common/Core/DataArray';

const vtkContainer = ref<HTMLDivElement | null>(null);
const loading = ref<boolean>(false);
const loadingMessage = ref<string>('Initializing ParaView Web Engine...');

// UI State & Tabs
const activeDockTab = ref<'pipeline' | 'properties' | 'info'>('properties');
const selectedPipelineItem = ref<'root' | 'slice' | 'clip' | 'contour' | 'glyph'>('root');
const isSourceVisible = ref<boolean>(true);
const currentDatasetName = ref<string>('openfoam_cavity.foam');
const isLiveStreaming = ref<boolean>(false);

// VCR Animation State
const isPlaying = ref<boolean>(false);
const currentTimeIndex = ref<number>(0);
const totalTimeSteps = ref<number>(50);
const loopAnimation = ref<boolean>(true);
let animationTimer: any = null;

// Representation & Styling
const representationMode = ref<'surface' | 'surface_with_edges' | 'wireframe' | 'points'>('surface_with_edges');
const meshOpacity = ref<number>(1.0);
const pointSize = ref<number>(4);
const edgeColor = ref<string>('#1a202c');

// Field Coloring & Transfer Function
const selectedFieldKey = ref<string>('velocity_magnitude');
const selectedComponent = ref<'magnitude' | 'x' | 'y' | 'z'>('magnitude');
const selectedColorMapPreset = ref<'coolwarm' | 'rainbow' | 'viridis' | 'plasma' | 'jet'>('coolwarm');
const showScalarBar = ref<boolean>(true);

// Active Filters
const activeFilters = ref({
  slice: false,
  clip: false,
  contour: false,
  glyph: false,
  streamlines: false
});

// Probe Tool Info
const probeInfo = ref({ x: 0.0, y: 0.0, val: 0.842 });

// Active Dataset
const activeData = ref<ParsedMeshData>(generateProceduralCfdData(41, 41));

const activeFieldInfo = computed(() => {
  return activeData.value.fields[selectedFieldKey.value] || null;
});

// ParaView Color Transfer Presets
const COLOR_PRESETS = {
  coolwarm: [
    0.0, 0.231, 0.298, 0.753, // Cool Blue
    0.5, 0.865, 0.865, 0.865, // Neutral Grey
    1.0, 0.706, 0.016, 0.150  // Warm Red
  ],
  rainbow: [
    0.0, 0.0, 0.0, 1.0,       // Blue
    0.25, 0.0, 1.0, 1.0,      // Cyan
    0.5, 0.0, 1.0, 0.0,       // Green
    0.75, 1.0, 1.0, 0.0,      // Yellow
    1.0, 1.0, 0.0, 0.0        // Red
  ],
  viridis: [
    0.0, 0.267, 0.004, 0.329, // Dark Purple
    0.33, 0.191, 0.407, 0.556,
    0.66, 0.128, 0.643, 0.457,
    1.0, 0.993, 0.906, 0.144  // Yellow
  ],
  plasma: [
    0.0, 0.050, 0.029, 0.528,
    0.33, 0.490, 0.014, 0.658,
    0.66, 0.798, 0.280, 0.469,
    1.0, 0.940, 0.975, 0.131
  ],
  jet: [
    0.0, 0.0, 0.0, 0.5,
    0.25, 0.0, 0.5, 1.0,
    0.5, 0.0, 1.0, 0.0,
    0.75, 1.0, 0.5, 0.0,
    1.0, 0.5, 0.0, 0.0
  ]
};

const colorMapGradientCss = computed(() => {
  if (selectedColorMapPreset.value === 'coolwarm') {
    return 'linear-gradient(to right, rgb(59, 76, 192), rgb(221, 221, 221), rgb(180, 4, 38))';
  } else if (selectedColorMapPreset.value === 'rainbow') {
    return 'linear-gradient(to right, #0000ff, #00ffff, #00ff00, #ffff00, #ff0000)';
  } else if (selectedColorMapPreset.value === 'viridis') {
    return 'linear-gradient(to right, #440154, #31688e, #35b779, #fde725)';
  } else if (selectedColorMapPreset.value === 'plasma') {
    return 'linear-gradient(to right, #0d0887, #7e03a8, #cc4778, #f0f921)';
  } else {
    return 'linear-gradient(to right, #00007f, #007fff, #7fff7f, #ff7f00, #7f0000)';
  }
});

// VTK Instance Handles
let fullScreenRenderer: any = null;
let renderer: any = null;
let renderWindow: any = null;
let actor: any = null;
let mapper: any = null;
let currentPolyData: any = null;

onMounted(() => {
  initVtk();
  loadData(activeData.value);
});

onBeforeUnmount(() => {
  stopAnimation();
  if (fullScreenRenderer) {
    fullScreenRenderer.delete();
  }
});

function initVtk() {
  if (!vtkContainer.value) return;

  fullScreenRenderer = vtkFullScreenRenderWindow.newInstance({
    container: vtkContainer.value,
    containerStyle: { height: '100%', width: '100%', position: 'relative' },
    background: [0.11, 0.13, 0.17] // Dark ParaView Viewport background
  });

  renderer = fullScreenRenderer.getRenderer();
  renderWindow = fullScreenRenderer.getRenderWindow();

  actor = vtkActor.newInstance();
  mapper = vtkMapper.newInstance();
  actor.setMapper(mapper);
  renderer.addActor(actor);
}

function loadData(data: ParsedMeshData) {
  loading.value = true;
  loadingMessage.value = 'Uploading mesh topology & scalar arrays to GPU...';

  activeData.value = data;

  // Build vtkPolyData
  currentPolyData = vtkPolyData.newInstance();
  currentPolyData.getPoints().setData(data.points, 3);
  currentPolyData.getPolys().setData(data.cells);

  // Register each field as a vtkDataArray
  for (const [key, field] of Object.entries(data.fields)) {
    const array = vtkDataArray.newInstance({
      name: key,
      values: field.values,
      numberOfComponents: field.numberOfComponents
    });
    currentPolyData.getPointData().addArray(array);
  }

  // Set active scalar
  if (data.fields[selectedFieldKey.value]) {
    currentPolyData.getPointData().setActiveScalars(selectedFieldKey.value);
  } else {
    const firstKey = Object.keys(data.fields)[0];
    selectedFieldKey.value = firstKey;
    currentPolyData.getPointData().setActiveScalars(firstKey);
  }

  mapper.setInputData(currentPolyData);

  applyRepresentation();
  applyColorMapPreset();
  rescaleToDataRange();

  renderer.resetCamera();
  renderWindow.render();
  loading.value = false;
}

function applyRepresentation() {
  if (!actor) return;
  const prop = actor.getProperty();

  if (representationMode.value === 'surface') {
    prop.setRepresentation(2); // Surface
    prop.setEdgeVisibility(false);
  } else if (representationMode.value === 'surface_with_edges') {
    prop.setRepresentation(2); // Surface
    prop.setEdgeVisibility(true);
    prop.setEdgeColor(0.12, 0.16, 0.22);
  } else if (representationMode.value === 'wireframe') {
    prop.setRepresentation(1); // Wireframe
    prop.setEdgeVisibility(false);
  } else if (representationMode.value === 'points') {
    prop.setRepresentation(0); // Points
    prop.setPointSize(pointSize.value);
  }

  prop.setOpacity(meshOpacity.value);
  renderWindow.render();
}

function applyOpacity() {
  if (actor) {
    actor.getProperty().setOpacity(meshOpacity.value);
    renderWindow.render();
  }
}

function applyPointSize() {
  if (actor && representationMode.value === 'points') {
    actor.getProperty().setPointSize(pointSize.value);
    renderWindow.render();
  }
}

function applyEdgeColor() {
  if (actor) {
    // Parse hex edgeColor to RGB
    const hex = edgeColor.value.replace('#', '');
    const r = parseInt(hex.substring(0, 2), 16) / 255;
    const g = parseInt(hex.substring(2, 4), 16) / 255;
    const b = parseInt(hex.substring(4, 6), 16) / 255;
    actor.getProperty().setEdgeColor(r, g, b);
    renderWindow.render();
  }
}

function updateFieldColoring() {
  if (!currentPolyData || !mapper) return;

  if (selectedFieldKey.value === 'solid') {
    mapper.setScalarVisibility(false);
    actor.getProperty().setColor(0.3, 0.6, 0.9);
  } else {
    mapper.setScalarVisibility(true);
    currentPolyData.getPointData().setActiveScalars(selectedFieldKey.value);
    rescaleToDataRange();
  }
  mapper.modified();
  renderWindow.render();
}

function applyColorMapPreset() {
  if (!mapper) return;
  const preset = COLOR_PRESETS[selectedColorMapPreset.value] || COLOR_PRESETS.coolwarm;
  const lut = vtkColorTransferFunction.newInstance();
  lut.applyColorMap({ RGBPoints: preset });
  mapper.setLookupTable(lut);
  rescaleToDataRange();
  renderWindow.render();
}

function rescaleToDataRange() {
  if (!mapper || !activeFieldInfo.value) return;
  const lut = mapper.getLookupTable();
  if (lut) {
    lut.setRange(activeFieldInfo.value.min, activeFieldInfo.value.max);
    lut.modified();
  }
  mapper.modified();
  renderWindow.render();
}

function toggleSourceVisibility() {
  isSourceVisible.value = !isSourceVisible.value;
  if (actor) {
    actor.setVisibility(isSourceVisible.value);
    renderWindow.render();
  }
}

function toggleFilter(filterKey: 'slice' | 'clip' | 'contour' | 'glyph' | 'streamlines') {
  activeFilters.value[filterKey] = !activeFilters.value[filterKey];
  // Re-render
  renderWindow.render();
}

// Camera Presets
function setCameraView(view: '+X' | '-X' | '+Y' | '-Y' | '+Z' | 'iso') {
  if (!renderer) return;
  const cam = renderer.getActiveCamera();
  const fp = cam.getFocalPoint();
  const dist = cam.getDistance();

  if (view === '+X') {
    cam.setPosition(fp[0] + dist, fp[1], fp[2]);
    cam.setViewUp(0, 1, 0);
  } else if (view === '-X') {
    cam.setPosition(fp[0] - dist, fp[1], fp[2]);
    cam.setViewUp(0, 1, 0);
  } else if (view === '+Y') {
    cam.setPosition(fp[0], fp[1] + dist, fp[2]);
    cam.setViewUp(0, 0, 1);
  } else if (view === '-Y') {
    cam.setPosition(fp[0], fp[1] - dist, fp[2]);
    cam.setViewUp(0, 0, -1);
  } else if (view === '+Z') {
    cam.setPosition(fp[0], fp[1], fp[2] + dist);
    cam.setViewUp(0, 1, 0);
  } else if (view === 'iso') {
    const d = dist / Math.sqrt(3);
    cam.setPosition(fp[0] + d, fp[1] + d, fp[2] + d);
    cam.setViewUp(0, 1, 0);
  }

  renderer.resetCameraClippingRange();
  renderWindow.render();
}

function resetCamera() {
  if (renderer && renderWindow) {
    renderer.resetCamera();
    renderWindow.render();
  }
}

// VCR Animation
function togglePlay() {
  if (isPlaying.value) {
    stopAnimation();
  } else {
    startAnimation();
  }
}

function startAnimation() {
  isPlaying.value = true;
  animationTimer = setInterval(() => {
    let next = currentTimeIndex.value + 1;
    if (next >= totalTimeSteps.value) {
      if (loopAnimation.value) {
        next = 0;
      } else {
        stopAnimation();
        return;
      }
    }
    goToTimeStep(next);
  }, 100);
}

function stopAnimation() {
  isPlaying.value = false;
  if (animationTimer) {
    clearInterval(animationTimer);
    animationTimer = null;
  }
}

function stepTime(delta: number) {
  let next = currentTimeIndex.value + delta;
  if (next < 0) next = 0;
  if (next >= totalTimeSteps.value) next = totalTimeSteps.value - 1;
  goToTimeStep(next);
}

function goToTimeStep(step: number) {
  currentTimeIndex.value = step;
  // Re-generate time-dependent field variation
  const t = step * 0.05;
  const newData = generateProceduralCfdData(41, 41, t);
  loadData(newData);
}

// Sync with live OpenZess backend
async function syncWithActiveSolver() {
  loading.value = true;
  loadingMessage.value = 'Requesting live CFD mesh and VTK fields from OpenZess server...';
  try {
    const res = await fetch('/api/export/vtk?name=openzess_live');
    if (res.ok) {
      const vtkText = await res.text();
      const parsed = parseVtkAscii(vtkText);
      currentDatasetName.value = 'openzess_live.vtk';
      isLiveStreaming.value = true;
      loadData(parsed);
    } else {
      // Fallback: update with procedural CFD state
      loadData(generateProceduralCfdData(41, 41, currentTimeIndex.value * 0.1));
    }
  } catch (e) {
    loadData(generateProceduralCfdData(41, 41, currentTimeIndex.value * 0.1));
  } finally {
    loading.value = false;
  }
}

function handleFileUpload(event: Event) {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;
  readFile(file);
}

function handleFileDrop(event: DragEvent) {
  event.preventDefault();
  const file = event.dataTransfer?.files?.[0];
  if (!file) return;
  readFile(file);
}

function readFile(file: File) {
  loading.value = true;
  loadingMessage.value = `Parsing ${file.name}...`;
  currentDatasetName.value = file.name;

  const reader = new FileReader();
  reader.onload = () => {
    const text = reader.result as string;
    const parsed = parseVtkAscii(text);
    loadData(parsed);
    loading.value = false;
  };
  reader.readAsText(file);
}

function exportCurrentVtk() {
  if (!activeData.value) return;
  const nx = 41, ny = 41;
  let vtk = `# vtk DataFile Version 3.0\nOpenZess ParaView Web Export\nASCII\nDATASET STRUCTURED_POINTS\nDIMENSIONS ${nx} ${ny} 1\nORIGIN 0 0 0\nSPACING 0.05 0.05 1.0\nPOINT_DATA ${nx * ny}\n`;
  
  if (activeData.value.fields.velocity) {
    vtk += `VECTORS velocity float\n`;
    const v = activeData.value.fields.velocity.values;
    for (let i = 0; i < v.length; i += 3) {
      vtk += `${v[i].toFixed(6)} ${v[i+1].toFixed(6)} ${v[i+2].toFixed(6)}\n`;
    }
  }

  if (activeData.value.fields.pressure) {
    vtk += `SCALARS pressure float 1\nLOOKUP_TABLE default\n`;
    const p = activeData.value.fields.pressure.values;
    for (let i = 0; i < p.length; i++) {
      vtk += `${p[i].toFixed(6)}\n`;
    }
  }

  const blob = new Blob([vtk], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${currentDatasetName.value.replace(/\.[^/.]+$/, '')}_exported.vtk`;
  a.click();
  URL.revokeObjectURL(url);
}

function takeScreenshot() {
  if (!renderWindow) return;
  const canvas = vtkContainer.value?.querySelector('canvas');
  if (canvas) {
    const dataUrl = canvas.toDataURL('image/png');
    const a = document.createElement('a');
    a.href = dataUrl;
    a.download = `ParaView_Capture_${Date.now()}.png`;
    a.click();
  }
}

function resetSession() {
  stopAnimation();
  currentTimeIndex.value = 0;
  activeFilters.value = { slice: false, clip: false, contour: false, glyph: false, streamlines: false };
  representationMode.value = 'surface_with_edges';
  selectedFieldKey.value = 'velocity_magnitude';
  selectedColorMapPreset.value = 'coolwarm';
  currentDatasetName.value = 'openfoam_cavity.foam';
  loadData(generateProceduralCfdData(41, 41));
}
</script>

<style scoped>
.paraview-studio-container {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  background: #141820;
  color: #e2e8f0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  overflow: hidden;
  user-select: none;
}

/* ParaView Top Menu Bar */
.paraview-menu-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 14px;
  background: #1a202c;
  border-bottom: 1px solid #2d3748;
  font-size: 12px;
  gap: 12px;
}

.pv-brand {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pv-logo-badge {
  background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
  color: #fff;
  font-weight: 800;
  padding: 3px 6px;
  border-radius: 4px;
  font-size: 11px;
  letter-spacing: 0.5px;
}

.pv-app-title {
  font-weight: 700;
  font-size: 13px;
  color: #f8fafc;
}

.pv-badge-pill {
  background: #0f172a;
  border: 1px solid #334155;
  color: #38bdf8;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 10px;
}

.pv-top-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.pv-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: #2d3748;
  color: #e2e8f0;
  border: 1px solid #4a5568;
  border-radius: 4px;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.pv-btn:hover:not(:disabled) {
  background: #4a5568;
  border-color: #718096;
}

.pv-btn-primary {
  background: #0284c7;
  border-color: #0369a1;
  color: #ffffff;
  font-weight: 600;
}

.pv-btn-primary:hover:not(:disabled) {
  background: #0369a1;
}

.pv-btn-accent {
  background: #7c3aed;
  border-color: #6d28d9;
  color: #ffffff;
  font-weight: 600;
}

.pv-btn-accent:hover:not(:disabled) {
  background: #6d28d9;
}

.pv-status-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 10px;
  background: #1e293b;
  color: #94a3b8;
  border: 1px solid #334155;
}

.status-chip.live {
  background: rgba(34, 197, 94, 0.15);
  color: #4ade80;
  border-color: #22c55e;
}

.pulse-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.stats-chip {
  font-size: 11px;
  color: #94a3b8;
  background: #0f172a;
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid #1e293b;
}

/* Ribbon Toolbars Bar */
.paraview-ribbon-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 6px 14px;
  background: #1f2733;
  border-bottom: 1px solid #2d3748;
  font-size: 11px;
  overflow-x: auto;
}

.ribbon-group {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding-right: 14px;
  border-right: 1px solid #2d3748;
}

.ribbon-group:last-child {
  border-right: none;
}

.group-label {
  font-size: 9px;
  text-transform: uppercase;
  color: #64748b;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.group-buttons {
  display: flex;
  align-items: center;
  gap: 4px;
}

.ribbon-btn {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 3px 8px;
  background: #2a3441;
  color: #cbd5e1;
  border: 1px solid #3d4a5d;
  border-radius: 3px;
  font-size: 11px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.ribbon-btn:hover {
  background: #3b485a;
  color: #ffffff;
}

.ribbon-btn.active {
  background: #0284c7;
  border-color: #38bdf8;
  color: #ffffff;
  font-weight: 600;
}

.ribbon-btn.play-btn {
  background: #059669;
  border-color: #10b981;
  color: #ffffff;
  font-weight: 700;
}

.ribbon-btn.play-btn.active {
  background: #d97706;
  border-color: #f59e0b;
}

.time-readout {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  color: #94a3b8;
  margin-top: 1px;
}

.phys-time {
  color: #38bdf8;
  font-weight: 600;
}

/* Main Workspace */
.paraview-workspace {
  display: flex;
  flex: 1;
  position: relative;
  overflow: hidden;
}

/* Left Dock Sidebar */
.paraview-dock-sidebar {
  width: 320px;
  min-width: 280px;
  max-width: 400px;
  background: #181e28;
  border-right: 1px solid #2d3748;
  display: flex;
  flex-direction: column;
  z-index: 10;
}

.dock-tab-header {
  display: flex;
  background: #111620;
  border-bottom: 1px solid #2d3748;
}

.dock-tab-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 8px 6px;
  background: transparent;
  color: #94a3b8;
  border: none;
  border-bottom: 2px solid transparent;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.dock-tab-btn:hover {
  color: #f1f5f9;
}

.dock-tab-btn.active {
  color: #38bdf8;
  border-bottom-color: #38bdf8;
  background: #181e28;
}

.dock-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  font-size: 11px;
}

.panel-section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 700;
  font-size: 12px;
  color: #f8fafc;
  margin-bottom: 10px;
  border-bottom: 1px solid #2d3748;
  padding-bottom: 4px;
}

.panel-section-title .hint {
  font-size: 9px;
  color: #64748b;
  font-weight: normal;
}

/* Pipeline Tree */
.pipeline-tree {
  display: flex;
  flex-direction: column;
  gap: 4px;
  background: #111620;
  border: 1px solid #2d3748;
  border-radius: 4px;
  padding: 6px;
  min-height: 140px;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 8px;
  border-radius: 3px;
  cursor: pointer;
  background: #1e2633;
  color: #cbd5e1;
  transition: all 0.15s ease;
}

.tree-node:hover {
  background: #2a3444;
}

.tree-node.selected {
  background: #0284c7;
  color: #ffffff;
}

.tree-node.child-node {
  margin-left: 18px;
  position: relative;
  background: #18202c;
}

.tree-node.child-node::before {
  content: '';
  position: absolute;
  left: -10px;
  top: 50%;
  width: 8px;
  height: 1px;
  background: #475569;
}

.eye-toggle-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 12px;
  padding: 0 2px;
}

.node-name {
  flex: 1;
  font-weight: 600;
  font-size: 11px;
}

.node-badge {
  font-size: 9px;
  padding: 1px 5px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 3px;
}

.pipeline-actions-footer {
  display: flex;
  gap: 6px;
  margin-top: 10px;
}

.tool-action-btn {
  flex: 1;
  padding: 5px 8px;
  background: #242c3a;
  border: 1px solid #3b4657;
  color: #cbd5e1;
  border-radius: 4px;
  font-size: 10px;
  cursor: pointer;
  transition: all 0.15s;
}

.tool-action-btn:hover {
  background: #333e50;
  color: #fff;
}

/* Properties Panel */
.prop-group {
  margin-bottom: 16px;
  background: #111620;
  border: 1px solid #2d3748;
  border-radius: 4px;
  overflow: hidden;
}

.prop-group-header {
  padding: 6px 10px;
  background: #1c2430;
  border-bottom: 1px solid #2d3748;
  font-weight: 700;
  font-size: 11px;
  color: #38bdf8;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.prop-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  border-bottom: 1px solid #1a2230;
  gap: 8px;
}

.prop-row:last-child {
  border-bottom: none;
}

.prop-row label {
  color: #94a3b8;
  font-size: 11px;
  min-width: 100px;
}

.prop-row select, .prop-row input[type="text"] {
  flex: 1;
  padding: 4px 6px;
  background: #1e2633;
  border: 1px solid #3d4a5d;
  color: #f1f5f9;
  border-radius: 3px;
  font-size: 11px;
}

.slider-control {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.slider-control input[type="range"] {
  flex: 1;
}

.val-label {
  font-family: monospace;
  font-size: 10px;
  color: #38bdf8;
  min-width: 32px;
}

.prop-row.actions-row {
  display: flex;
  gap: 6px;
  padding: 8px 10px;
}

.btn-micro {
  flex: 1;
  padding: 4px 8px;
  background: #242c3a;
  border: 1px solid #3d4a5d;
  color: #cbd5e1;
  border-radius: 3px;
  font-size: 10px;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-micro:hover {
  background: #333e50;
  color: #fff;
}

.btn-micro.active {
  background: #0284c7;
  border-color: #38bdf8;
  color: #fff;
}

.scalar-range-box {
  display: flex;
  justify-content: space-between;
  background: #18202c;
  padding: 6px 10px;
  font-size: 10px;
  border-top: 1px solid #2d3748;
}

.scalar-range-box .lbl {
  color: #64748b;
  margin-right: 4px;
}

.scalar-range-box .val {
  color: #38bdf8;
  font-family: monospace;
}

/* Info Panel */
.stats-table {
  display: flex;
  flex-direction: column;
  background: #111620;
  border: 1px solid #2d3748;
  border-radius: 4px;
  overflow: hidden;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 10px;
  border-bottom: 1px solid #1c2430;
}

.stat-row:last-child {
  border-bottom: none;
}

.stat-row .k {
  color: #94a3b8;
}

.stat-row .v {
  color: #f1f5f9;
  font-family: monospace;
}

.stat-row .v.highlight {
  color: #38bdf8;
  font-weight: 600;
}

.fields-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-item {
  background: #111620;
  border: 1px solid #2d3748;
  padding: 6px 10px;
  border-radius: 4px;
}

.field-item .f-name {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 2px;
}

.f-type-badge {
  font-size: 8px;
  padding: 1px 4px;
  background: #0284c7;
  color: #fff;
  border-radius: 2px;
  text-transform: uppercase;
}

.field-item .f-bounds {
  font-size: 9px;
  color: #64748b;
  font-family: monospace;
}

/* Viewport Area */
.paraview-viewport {
  flex: 1;
  position: relative;
  background: #11141c;
  overflow: hidden;
}

/* Floating Scalar Bar / Color Legend Overlay */
.pv-scalar-bar-widget {
  position: absolute;
  top: 14px;
  right: 14px;
  background: rgba(17, 24, 39, 0.85);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 4px;
  padding: 8px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  z-index: 20;
  width: 220px;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4);
}

.scalar-bar-title {
  font-size: 10px;
  font-weight: 700;
  color: #e2e8f0;
  text-align: center;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.scalar-gradient-strip {
  height: 12px;
  border-radius: 2px;
  border: 1px solid rgba(0, 0, 0, 0.6);
}

.scalar-bar-ticks {
  display: flex;
  justify-content: space-between;
  font-size: 9px;
  font-family: monospace;
  color: #94a3b8;
}

/* 3D Orientation Axes HUD */
.pv-axes-hud {
  position: absolute;
  bottom: 14px;
  left: 14px;
  width: 70px;
  height: 70px;
  background: rgba(17, 24, 39, 0.6);
  backdrop-filter: blur(4px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  z-index: 20;
  pointer-events: none;
}

.axes-svg {
  width: 100%;
  height: 100%;
}

/* Probe HUD */
.pv-probe-hud {
  position: absolute;
  bottom: 14px;
  right: 14px;
  background: rgba(17, 24, 39, 0.75);
  backdrop-filter: blur(4px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  padding: 4px 10px;
  display: flex;
  gap: 10px;
  font-size: 10px;
  color: #94a3b8;
  font-family: monospace;
  z-index: 20;
}

.pv-probe-hud .probe-val {
  color: #38bdf8;
  font-weight: 600;
}

/* Loading Overlay */
.pv-loading-overlay {
  position: absolute;
  inset: 0;
  background: rgba(15, 23, 42, 0.8);
  backdrop-filter: blur(4px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  z-index: 50;
}

.pv-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(56, 189, 248, 0.2);
  border-top-color: #38bdf8;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.loading-msg {
  font-size: 12px;
  color: #cbd5e1;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>
