<template>
  <div class="paraview-studio-container" :class="isPaperTheme ? 'theme-paper' : 'dark theme-earth-dark'">
    <!-- Top Application Bar -->
    <header class="paraview-menu-bar">
      <div class="pv-brand">
        <span class="pv-logo-badge">OZ</span>
        <span class="pv-app-title">OpenZess Workbench</span>
        <span class="pv-badge-pill">C++20 WASM · FVM + FEA</span>
      </div>

      <!-- Quick Action Operations -->
      <div class="pv-top-actions">
        <label class="pv-btn" title="Open .VTK or OpenFOAM .foam file">
          Open File
          <input type="file" accept=".vtk,.foam,.foamFile,.txt" @change="handleFileUpload" style="display: none;" />
        </label>

        <select v-model.number="wasmPreset" class="pv-select-compact" title="Select C++20 WebAssembly CFD / FSI Case Preset">
          <option :value="4">Fig. 01 — Simple House (Wind + FSI)</option>
          <option :value="3">Fig. 02 — 20m Glass Tower (FSI)</option>
          <option :value="1">Fig. 03 — Cylinder (Vortex Shedding)</option>
          <option :value="5">Fig. 04 — NACA Airfoil Flow</option>
          <option :value="2">Fig. 05 — Venturi (Pressure Drop)</option>
          <option :value="0">Fig. 06 — Lid-Driven Cavity</option>
        </select>

        <button class="pv-btn pv-btn-primary" @click="runOpenFoamWasm" :disabled="loading" title="Run real C++20 OpenFOAM icoFoam solver in WebAssembly">
          {{ isWasmRunning ? 'Stop WASM' : 'Run WASM' }}
        </button>

        <button class="pv-btn" @click="triggerBreakCfl" :disabled="!isWasmRunning" title="Break CFL on purpose (dt spike) to inspect instability">
          Break CFL
        </button>

        <button class="pv-btn" @click="triggerSelfHeal" :disabled="!isWasmRunning" title="Re-enable C++20 adaptive CFL self-healing">
          Self-Heal
        </button>

        <button class="pv-btn" @click="useBoardStage = !useBoardStage" title="Switch between Illustrated 3D Diorama (#board style) and Raw ParaView VTK Mesh">
          {{ useBoardStage ? 'VTK Mesh' : '3D Diorama' }}
        </button>

        <button class="pv-btn" @click="togglePaperTheme" title="Switch between Earth Light and Earth Dark mode">
          {{ isPaperTheme ? 'Dark Mode' : 'Light Mode' }}
        </button>

        <button class="pv-btn" @click="exportCurrentVtk" title="Download current mesh and fields as Legacy VTK (.vtk)">
          Save .vtk
        </button>

        <button class="pv-btn" @click="resetSession" title="Reset pipeline and camera">
          Reset
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

      <!-- Laya System-1 AI Simulation Router -->
      <div class="ribbon-group laya-ai-group">
        <span class="group-label">Laya AI Router {{ layaStatusText ? '· ' + layaStatusText : '' }}</span>
        <div class="group-buttons">
          <input
            v-model="layaPrompt"
            @keyup.enter="routeWithLayaAi"
            type="text"
            class="pv-ai-input"
            placeholder="e.g. 120 km/h wind on 20m glass tower"
          />
          <button class="ribbon-btn pv-ai-btn" @click="routeWithLayaAi" :disabled="layaRouting">
            {{ layaRouting ? 'Routing...' : 'AI Run' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Main Workspace (Dockable Sidebar + 3D Viewport) -->
    <div class="paraview-workspace">
      <!-- Left Dockable Sidebar -->
      <aside
        v-show="!isSidebarMinimized"
        class="paraview-dock-sidebar"
        :class="{ maximized: isSidebarMaximized }"
        :style="{ width: sidebarWidth + 'px' }"
      >
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
          <button class="dock-tab-btn" :class="{ active: activeDockTab === 'log' }" @click="activeDockTab = 'log'">
            <span class="tab-icon">📟</span> OpenFOAM Log
          </button>
          <div class="dock-size-actions">
            <button
              class="dock-size-btn"
              @click="toggleSidebarMaximize"
              :title="isSidebarMaximized ? 'Restore sidebar size' : 'Maximize sidebar'"
            >
              {{ isSidebarMaximized ? '⤡' : '⤢' }}
            </button>
            <button
              class="dock-size-btn"
              @click="toggleSidebarMinimize"
              title="Minimize sidebar"
            >
              ◀
            </button>
          </div>
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

        <!-- Tab 4: OpenFOAM WASM Terminal Log -->
        <div v-show="activeDockTab === 'log'" class="dock-content log-panel">
          <div class="panel-section-title">
            <span>OpenFOAM icoFoam Log</span>
            <button class="btn-micro" @click="downloadOpenFoamTimeCase" title="Download OpenFOAM time directories and case dictionaries">
              📦 Export Case
            </button>
          </div>
          <div class="openfoam-console-box">
            <div class="console-header">/* OpenFOAM v2406: icoFoam WebAssembly Execution */</div>
            <div v-for="(line, idx) in wasmLogs" :key="idx" class="console-line" :class="{
              'time-line': line.startsWith('Time ='),
              'solve-line': line.includes('Solving for'),
              'cont-line': line.includes('continuity errors')
            }">
              {{ line }}
            </div>
            <div v-if="wasmLogs.length === 0" class="console-empty">
              Click "🌐 Run WASM icoFoam" in the top ribbon to start live client-side C/WebAssembly CFD execution.
            </div>
          </div>
        </div>
      </aside>

      <!-- Drag-to-resize splitter -->
      <div
        v-show="!isSidebarMinimized"
        class="sidebar-resizer"
        title="Drag to resize sidebar (double-click to maximize/restore)"
        @mousedown="startSidebarResize"
        @dblclick="toggleSidebarMaximize"
      ></div>

      <!-- Center 3D Viewport Area -->
      <main
        class="paraview-viewport"
        ref="vtkContainer"
        @dragover.prevent
        @drop="handleFileDrop"
        @pointermove="handleViewportHover"
        @pointerleave="hoverTip.visible = false"
      >
        <!-- Illustrated 3D CFD Diorama Stage (#board style, powered by live C++20 WASM + FEA) -->
        <OpenZessBoardStage
          v-if="useBoardStage"
          ref="boardStageRef"
          :engine="(wasmEngine as any)"
          :preset="wasmPreset"
          :field-rev="fieldRev"
          :is-paper-theme="isPaperTheme"
          :is-running="isWasmRunning"
          :reynolds="activeReynolds"
          :color-map="selectedColorMapPreset"
          :field-key="selectedFieldKey"
          :representation="representationMode"
          :opacity="meshOpacity"
          :show-source="isSourceVisible"
          @update-reynolds="(val) => { customReynolds = val; applyCustomReynolds(); }"
          @toggle-run="runOpenFoamWasm"
          @break-cfl="triggerBreakCfl"
          @self-heal="triggerSelfHeal"
          @probe-change="(info) => { probeInfo = info; }"
        />

        <div v-show="!useBoardStage" ref="vtkMount" class="pv-vtk-mount"></div>
        <canvas v-show="!useBoardStage && showFlowBeads" ref="flowCanvas" class="pv-flow-canvas"></canvas>

        <button
          v-if="isSidebarMinimized"
          class="pv-sidebar-restore-btn"
          @click="toggleSidebarMinimize"
          title="Expand sidebar"
        >
          ▶ Sidebar
        </button>

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

        <!-- SVG Elbow Leader Lines & Pulsing 3D Hotspots (VTK Mesh fallback mode) -->
        <svg v-if="!useBoardStage && showCalloutPins" class="pv-leaders-svg" aria-hidden="true">
          <g
            v-for="pin in projectedCalloutPins"
            :key="'ldr-' + pin.id"
            class="leader-group"
            :class="{ 'is-hot': hoveredPinId === pin.id || selectedPinId === pin.id }"
          >
            <path :d="pin.pathD" class="leader-path" />
            <circle :cx="pin.ax" :cy="pin.ay" r="11" class="hotspot-halo" />
            <circle :cx="pin.ax" :cy="pin.ay" r="4.5" class="hotspot-anchor" />
            <circle :cx="pin.lx" :cy="pin.ly" r="3" class="leader-end-dot" />
          </g>
        </svg>

        <!-- Interactive 3D Callout Tags & Physics Inspector (VTK Mesh fallback mode) -->
        <div class="pv-callout-layer" v-if="!useBoardStage && showCalloutPins">
          <button
            v-for="pin in projectedCalloutPins"
            :key="pin.id"
            class="pv-callout-pin"
            :class="{ active: selectedPinId === pin.id, hot: hoveredPinId === pin.id }"
            :style="{ left: pin.lx + 'px', top: pin.ly + 'px', transform: pin.alignRight ? 'translate(-100%, -50%)' : 'translate(0, -50%)' }"
            @pointerenter="hoveredPinId = pin.id"
            @pointerleave="hoveredPinId = null"
            @click="selectCalloutPin(pin)"
          >
            <span class="pin-dot"></span>
            <span class="pin-label">{{ pin.label }}</span>
            <span class="pin-sub">{{ pin.shortVal }}</span>
          </button>

          <div v-if="selectedPin" class="pv-callout-card">
            <div class="callout-card-head">
              <strong>{{ selectedPin.title }}</strong>
              <button class="callout-close" @click="selectedPinId = null" title="Close inspector">×</button>
            </div>
            <p class="callout-card-body">{{ selectedPin.desc }}</p>
            <div class="callout-card-metric">{{ selectedPin.metric }}</div>
            <div class="callout-inspector-controls">
              <label class="insp-slider-label">
                <span>Flow Re: <b>{{ activeReynolds }}</b></span>
                <input type="range" min="50" max="600" step="25" v-model.number="customReynolds" @change="applyCustomReynolds" />
              </label>
              <div class="insp-actions">
                <button class="insp-chip-btn" @click="runOpenFoamWasm">{{ isWasmRunning ? 'Pause' : 'Live Run' }}</button>
                <button class="insp-chip-btn" @click="triggerBreakCfl">Break CFL</button>
                <button class="insp-chip-btn" @click="triggerSelfHeal">Self-Heal</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Live Hover Probe Tooltip (VTK Mesh fallback mode) -->
        <div
          v-if="!useBoardStage && hoverTip.visible"
          class="pv-hover-tip"
          :style="{ left: hoverTip.x + 'px', top: hoverTip.y + 'px' }"
        >
          <b>{{ hoverTip.title }}</b>
          <span>{{ hoverTip.detail }}</span>
        </div>

        <!-- Floating Bottom Viewbar (VTK Mesh fallback mode) -->
        <div v-if="!useBoardStage" class="pv-viewbar" role="toolbar" aria-label="3D view controls">
          <button class="vb-btn" @click="orbitCamera(-18)" title="Rotate left (Q)">↺</button>
          <button class="vb-btn" @click="orbitCamera(18)" title="Rotate right (E)">↻</button>
          <span class="vb-sep"></span>
          <button class="vb-btn" @click="zoomCamera(0.84)" title="Zoom out (-)">−</button>
          <button class="vb-btn" @click="zoomCamera(1.18)" title="Zoom in (+)">+</button>
          <span class="vb-sep"></span>
          <button class="vb-btn" @click="setCameraView('iso')" title="Isometric Reset (R)">⌖</button>
          <span class="vb-sep"></span>
          <button class="vb-btn vb-toggle" :class="{ active: showFlowBeads }" @click="toggleFlowBeads" title="Toggle Flow Beads (F)">
            Flow
          </button>
          <button class="vb-btn vb-toggle" :class="{ active: showCalloutPins }" @click="toggleCalloutPins" title="Toggle Callout Leaders (L)">
            Pins
          </button>
        </div>

        <!-- Probe Inspector HUD -->
        <div class="pv-probe-hud">
          <span class="probe-tag">Probe: ({{ probeInfo.x.toFixed(2) }}, {{ probeInfo.y.toFixed(2) }})</span>
          <span class="probe-val" v-if="activeFieldInfo">{{ activeFieldInfo.name }}: {{ probeInfo.val.toFixed(3) }} {{ activeFieldInfo.unit }}</span>
        </div>

        <!-- Loading / Parsing Overlay -->
        <div v-if="loading" class="pv-loading-overlay">
          <div class="pv-spinner"></div>
          <p class="loading-msg">{{ loadingMessage }}</p>
        </div>
      </main>
    </div>

    <!-- Bottom Split Educational Panel: Meet the Physics + Live OpenFOAM Dict -->
    <section class="pv-edu-strip">
      <div class="edu-col edu-physics">
        <div class="edu-heading">MEET THE PHYSICS · {{ activeCaseMeta.title }}</div>
        <p class="edu-desc">{{ activeCaseMeta.explanation }}</p>
      </div>
      <div class="edu-col edu-code">
        <div class="edu-heading">LIVE OPENFOAM DICT · system/controlDict &amp; 0/U</div>
        <pre class="edu-pre">{{ liveDictSnippet }}</pre>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, shallowRef, markRaw, computed, watch, onMounted, onBeforeUnmount } from 'vue';
import { parseVtkAscii, generateProceduralCfdData, type ParsedMeshData } from '../utils/vtkOpenFoamParser';
import { OpenFoamWasmEngine, generateOpenFoamCase } from '../utils/openfoamWasmBridge';
import OpenZessBoardStage from './OpenZessBoardStage.vue';

// Kitware VTK.js core modules
// @ts-ignore
import '@kitware/vtk.js/Rendering/Profiles/Geometry';
// @ts-ignore
import vtkFullScreenRenderWindow from '@kitware/vtk.js/Rendering/Misc/FullScreenRenderWindow';
// @ts-ignore
import vtkActor from '@kitware/vtk.js/Rendering/Core/Actor';
// @ts-ignore
import vtkMapper from '@kitware/vtk.js/Rendering/Core/Mapper';
// @ts-ignore
import vtkCoordinate from '@kitware/vtk.js/Rendering/Core/Coordinate';
// @ts-ignore
import vtkColorTransferFunction from '@kitware/vtk.js/Rendering/Core/ColorTransferFunction';
// @ts-ignore
import vtkPolyData from '@kitware/vtk.js/Common/DataModel/PolyData';
// @ts-ignore
import vtkDataArray from '@kitware/vtk.js/Common/Core/DataArray';

const vtkContainer = ref<HTMLDivElement | null>(null);
const vtkMount = ref<HTMLDivElement | null>(null);
const flowCanvas = ref<HTMLCanvasElement | null>(null);
const useBoardStage = ref<boolean>(true);
const boardStageRef = ref<InstanceType<typeof OpenZessBoardStage> | null>(null);
const loading = ref<boolean>(false);
const loadingMessage = ref<string>('Initializing ParaView Web Engine...');

// UI State & Tabs
const activeDockTab = ref<'pipeline' | 'properties' | 'info' | 'log'>('properties');
const isSidebarMinimized = ref<boolean>(false);
const isSidebarMaximized = ref<boolean>(false);
const sidebarWidth = ref<number>(320);
let prevSidebarWidth = 320;
let viewportResizeObserver: ResizeObserver | null = null;

function syncVtkResize() {
  requestAnimationFrame(() => {
    if (fullScreenRenderer) {
      fullScreenRenderer.resize();
      if (renderWindow) renderWindow.render();
    }
  });
}

function toggleSidebarMinimize() {
  isSidebarMinimized.value = !isSidebarMinimized.value;
  syncVtkResize();
}

function toggleSidebarMaximize() {
  isSidebarMinimized.value = false;
  if (!isSidebarMaximized.value) {
    prevSidebarWidth = sidebarWidth.value;
    sidebarWidth.value = Math.min(640, Math.max(460, Math.round(window.innerWidth * 0.45)));
    isSidebarMaximized.value = true;
  } else {
    sidebarWidth.value = prevSidebarWidth || 320;
    isSidebarMaximized.value = false;
  }
  syncVtkResize();
}

function startSidebarResize(e: MouseEvent) {
  e.preventDefault();
  const onMove = (ev: MouseEvent) => {
    const next = Math.min(720, Math.max(220, ev.clientX));
    sidebarWidth.value = next;
    isSidebarMaximized.value = next >= 460;
    if (fullScreenRenderer) fullScreenRenderer.resize();
  };
  const onUp = () => {
    window.removeEventListener('mousemove', onMove);
    window.removeEventListener('mouseup', onUp);
    syncVtkResize();
  };
  window.addEventListener('mousemove', onMove);
  window.addEventListener('mouseup', onUp);
}
const selectedPipelineItem = ref<'root' | 'slice' | 'clip' | 'contour' | 'glyph'>('root');
const isSourceVisible = ref<boolean>(true);
const currentDatasetName = ref<string>('openfoam_cavity.foam');
const isLiveStreaming = ref<boolean>(false);

// WebAssembly In-Browser OpenFOAM Solver State
const wasmPreset = ref<number>(4); // 0=Cavity, 1=Cylinder, 2=Venturi, 3=Tower FSI, 4=Simple House FSI, 5=Airfoil
const isPaperTheme = ref<boolean>(true);
const showCalloutPins = ref<boolean>(true);
const showFlowBeads = ref<boolean>(true);
const selectedPinId = ref<string | null>(null);
const hoveredPinId = ref<string | null>(null);
const customReynolds = ref<number>(200);
const cameraRev = ref<number>(0);
const fieldRev = ref<number>(0);
const viewportSize = ref<{ w: number; h: number }>({ w: 800, h: 520 });
const hoverTip = ref<{ visible: boolean; x: number; y: number; title: string; detail: string }>({
  visible: false,
  x: 0,
  y: 0,
  title: '',
  detail: ''
});
const layaPrompt = ref<string>('wind on a simple house');
const layaRouting = ref<boolean>(false);
const layaStatusText = ref<string>('');
const wasmEngine = shallowRef<OpenFoamWasmEngine | null>(null);

const CASE_META: Record<number, { key: string; title: string; re: number; dt: number; explanation: string }> = {
  4: { key: 'simple_house', title: 'Fig. 01 — Simple House (Wind + FSI)', re: 200, dt: 0.004, explanation: 'Incompressible air hits the windward wall, accelerates over the pitched roof ridge, forms a low-pressure wake behind the house, and feeds surface pressure into fea_structure.wasm to calculate structural Von Mises stress.' },
  3: { key: 'building_fsi', title: 'Fig. 02 — 20m Glass Tower (FSI)', re: 300, dt: 0.004, explanation: '120 km/h (33.3 m/s) lateral wind load generates stagnation pressure on the windward facade and vortex shedding downstream, coupled live into cantilever bending stress and tip drift.' },
  1: { key: 'cylinder', title: 'Fig. 03 — Cylinder Vortex Shedding', re: 100, dt: 0.005, explanation: 'Flow separates symmetrically then transitions into alternating Kármán vortices behind the circular bluff body, driven by Navier-Stokes momentum advection and PISO pressure projection.' },
  5: { key: 'airfoil', title: 'Fig. 04 — NACA Airfoil Flow', re: 400, dt: 0.003, explanation: 'Cambered airfoil accelerates airflow along the upper suction surface, lowering static pressure via Bernoulli coupling to generate upward aerodynamic lift.' },
  2: { key: 'venturi', title: 'Fig. 05 — Venturi Pressure Drop', re: 250, dt: 0.003, explanation: 'Mass conservation (∇·U = 0) accelerates fluid through the narrow throat, producing a sharp static pressure drop proportional to ½ρU².' },
  0: { key: 'cavity', title: 'Fig. 06 — Lid-Driven Cavity (Ghia 1982)', re: 100, dt: 0.005, explanation: 'Classic CFD benchmark: top moving wall U = (1, 0, 0) shears viscous fluid inside a sealed square box, forming a primary clockwise vortex validated against Ghia et al. (1982).' },
};

const activeCaseMeta = computed(() => CASE_META[wasmPreset.value] || CASE_META[4]);
const activeReynolds = computed(() => customReynolds.value || activeCaseMeta.value.re);

const activeCalloutPins = computed(() => {
  void fieldRev.value;
  const eng = wasmEngine.value;
  const maxCo = eng ? eng.maxCourant.toFixed(2) : '0.20';
  const dtStr = eng ? eng.dt.toFixed(4) : activeCaseMeta.value.dt.toFixed(4);

  // Scan live simulation arrays to locate actual physical extrema for the active case
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

  const toWorld = (i: number, j: number, z: number): [number, number, number] => {
    const nx = eng ? eng.nx : 41;
    const ny = eng ? eng.ny : 41;
    return [(i / (nx - 1)) * 2 - 1, (j / (ny - 1)) * 2 - 1, z];
  };

  const fsiPin = eng?.fsiActive
    ? {
        id: 'stress',
        world: toWorld(strI, strJ, 0.28),
        ox: -72,
        oy: 56,
        label: 'MAX STRESS',
        shortVal: `${eng.maxStressMpa.toFixed(2)} MPa`,
        title: 'COUPLED FEA STRUCTURAL STRESS',
        desc: 'Live Von Mises stress & tip drift tracked at the peak-loaded structural node.',
        metric: `Max Stress: ${eng.maxStressMpa.toFixed(3)} MPa · Drift: ${eng.maxDispMm.toFixed(3)} mm`
      }
    : {
        id: 'low_p',
        world: toWorld(minPI, minPJ, 0.06),
        ox: 76,
        oy: 52,
        label: 'LOW PRESSURE',
        shortVal: `${(minP === Infinity ? 0 : minP).toFixed(2)} Pa`,
        title: 'SUCTION / LOW-PRESSURE CORE',
        desc: 'Tracks the live minimum static pressure cell across the active flow field.',
        metric: `p_min = ${(minP === Infinity ? 0 : minP).toFixed(4)} Pa · Re = ${activeReynolds.value}`
      };

  return [
    {
      id: 'peak_vel',
      world: toWorld(spdI, spdJ, 0.08),
      ox: -76,
      oy: -58,
      label: 'VEL PEAK',
      shortVal: `${(maxSpd < 0 ? 1 : maxSpd).toFixed(2)} m/s`,
      title: 'LIVE PEAK VELOCITY CELL',
      desc: 'Automatically follows the fastest fluid cell in the active simulation domain.',
      metric: `|U|_max = ${(maxSpd < 0 ? 1 : maxSpd).toFixed(3)} m/s · Co_max = ${maxCo}`
    },
    {
      id: 'peak_p',
      world: toWorld(pI, pJ, 0.24),
      ox: -72,
      oy: 48,
      label: 'PRESSURE PEAK',
      shortVal: `${(maxP === -Infinity ? 0 : maxP).toFixed(2)} Pa`,
      title: 'LIVE STAGNATION / MAX PRESSURE',
      desc: 'Tracks the highest static pressure cell where fluid decelerates against boundaries.',
      metric: `p_max = ${(maxP === -Infinity ? 0 : maxP).toFixed(4)} Pa · Preset: ${activeCaseMeta.value.key}`
    },
    {
      id: 'vortex',
      world: toWorld(vortI, vortJ, 0.07),
      ox: 78,
      oy: -52,
      label: 'VORTEX CORE',
      shortVal: `${(maxVort < 0 ? 0 : maxVort).toFixed(1)} /s`,
      title: 'LIVE VORTEX CORE (MAX |ω|)',
      desc: 'Moves dynamically with the strongest swirling eddy / shear layer in real time.',
      metric: `|ω|_max = ${(maxVort < 0 ? 0 : maxVort).toFixed(2)} 1/s · dt = ${dtStr} s`
    },
    fsiPin
  ];
});

function worldToViewportPx(wx: number, wy: number, wz: number): [number, number] | null {
  if (!renderer || !vtkContainer.value) return null;
  const rect = vtkContainer.value.getBoundingClientRect();
  if (rect.width <= 0 || rect.height <= 0) return null;
  const dpr = window.devicePixelRatio || 1;
  const coord = vtkCoordinate.newInstance();
  coord.setCoordinateSystemToWorld();
  coord.setValue(wx, wy, wz);
  const disp = coord.getComputedDisplayValue(renderer);
  if (!disp || !Number.isFinite(disp[0]) || !Number.isFinite(disp[1])) return null;
  const x = disp[0] / dpr;
  const y = rect.height - disp[1] / dpr;
  return [Math.max(16, Math.min(rect.width - 16, x)), Math.max(16, Math.min(rect.height - 16, y))];
}

const projectedCalloutPins = computed(() => {
  void cameraRev.value;
  void viewportSize.value;
  const w = viewportSize.value.w || 800;
  const h = viewportSize.value.h || 520;
  const scale = Math.min(1, Math.max(0.55, w / 920));
  return activeCalloutPins.value.map((pin) => {
    const pt = worldToViewportPx(pin.world[0], pin.world[1], pin.world[2]);
    const ax = pt ? pt[0] : w * 0.5;
    const ay = pt ? pt[1] : h * 0.5;
    const dirX = ax < w * 0.48 ? -1 : 1;
    const ox = Math.abs(pin.ox) * scale * dirX;
    const oy = pin.oy * scale;
    const lx = Math.max(90, Math.min(w - 90, ax + ox));
    const ly = Math.max(24, Math.min(h - 62, ay + oy));
    const elbowX = ax + (lx - ax) * 0.52;
    const pathD = `M ${ax.toFixed(1)} ${ay.toFixed(1)} L ${elbowX.toFixed(1)} ${ly.toFixed(1)} L ${lx.toFixed(1)} ${ly.toFixed(1)}`;
    return {
      ...pin,
      ax,
      ay,
      lx,
      ly,
      alignRight: lx < ax,
      pathD
    };
  });
});

const selectedPin = computed(() => projectedCalloutPins.value.find(p => p.id === selectedPinId.value) || null);

const liveDictSnippet = computed(() => {
  const m = activeCaseMeta.value;
  const dt = wasmEngine.value ? wasmEngine.value.dt.toFixed(5) : m.dt.toFixed(5);
  const nu = (1 / m.re).toFixed(5);
  return `application     icoFoam;\ndeltaT          ${dt};   // Auto-CFL Self-Heal: ${wasmEngine.value?.autoSelfHeal ?? true}\nnu              [0 2 -1 0 0 0 0] ${nu}; // Re = ${m.re}\n// Case: ${m.key} (C++20 WebAssembly + FEA)`;
});
const wasmLogs = ref<string[]>([]);
const wasmTimeHistory = ref<{ time: number; data: ParsedMeshData; files: { [key: string]: string } }[]>([]);
const isWasmRunning = ref<boolean>(false);
let wasmIntervalId: any = null;

// VCR Animation State
const isPlaying = ref<boolean>(false);
const currentTimeIndex = ref<number>(0);
const totalTimeSteps = ref<number>(50);
const loopAnimation = ref<boolean>(true);
let animationTimer: any = null;

// Representation & Styling
const representationMode = ref<'surface' | 'surface_with_edges' | 'wireframe' | 'points'>('surface');
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
let obstacleActor: any = null;
let obstacleMapper: any = null;
let currentPolyData: any = null;
let flowRafId: number | null = null;

interface FlowBead {
  x: number;
  y: number;
  life: number;
  maxLife: number;
}
const flowBeads: FlowBead[] = Array.from({ length: 72 }, () => ({
  x: Math.random() * 2 - 1,
  y: Math.random() * 2 - 1,
  life: Math.random() * 140,
  maxLife: 110 + Math.random() * 70
}));

// Free-moving Lagrangian probe that rides the active simulation flow
const freeTracer = { x: -0.92, y: 0.14, trail: [] as [number, number][] };

function updateObstacleActor() {
  if (!obstacleActor || !obstacleMapper || !renderWindow) return;
  const heightScale = wasmPreset.value === 3 ? 0.54 : wasmPreset.value === 4 ? 0.36 : 0.24;
  const obs = wasmEngine.value ? wasmEngine.value.buildObstacleMesh(heightScale) : null;
  if (!obs) {
    obstacleActor.setVisibility(false);
    return;
  }
  const poly = vtkPolyData.newInstance();
  poly.getPoints().setData(obs.points, 3);
  poly.getPolys().setData(obs.cells);
  obstacleMapper.setInputData(poly);
  obstacleActor.setVisibility(isSourceVisible.value);
  const prop = obstacleActor.getProperty();
  // #board-style matte block with crisp dark ink outlines
  prop.setColor(isPaperTheme.value ? 0.78 : 0.66, isPaperTheme.value ? 0.70 : 0.57, isPaperTheme.value ? 0.63 : 0.50);
  prop.setEdgeVisibility(true);
  prop.setEdgeColor(0.18, 0.16, 0.16);
  prop.setLineWidth(1.4);
}

function sampleVelocityAt(wx: number, wy: number): { u: number; v: number; spd: number; p: number; solid: boolean } {
  const eng = wasmEngine.value;
  if (eng) {
    const gx = Math.max(0, Math.min(eng.nx - 1.001, ((wx + 1) * 0.5) * (eng.nx - 1)));
    const gy = Math.max(0, Math.min(eng.ny - 1.001, ((wy + 1) * 0.5) * (eng.ny - 1)));
    const i = Math.floor(gx);
    const j = Math.floor(gy);
    const id = j * eng.nx + i;
    return {
      u: eng.u[id] || 0,
      v: eng.v[id] || 0,
      spd: eng.speed[id] || 0,
      p: eng.p[id] || 0,
      solid: eng.mask[id] === 1
    };
  }
  return { u: 0.85, v: 0.0, spd: 0.85, p: 0.0, solid: false };
}

function startFlowBeadLoop() {
  if (flowRafId !== null) cancelAnimationFrame(flowRafId);
  const stepBeads = () => {
    flowRafId = requestAnimationFrame(stepBeads);
    const canvas = flowCanvas.value;
    if (!canvas || !vtkContainer.value || !renderer) return;
    const rect = vtkContainer.value.getBoundingClientRect();
    if (rect.width < 10 || rect.height < 10) return;
    if (canvas.width !== Math.round(rect.width) || canvas.height !== Math.round(rect.height)) {
      canvas.width = Math.round(rect.width);
      canvas.height = Math.round(rect.height);
    }
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (!showFlowBeads.value) return;

    const rimCol = isPaperTheme.value ? '#3A3838' : '#1E1C1C';
    const coreCol = isPaperTheme.value ? '#FFF8E8' : '#E2DAD2';
    for (const b of flowBeads) {
      b.life += 1;
      const sample = sampleVelocityAt(b.x, b.y);
      const vx = wasmPreset.value === 0 ? sample.u : (Math.abs(sample.u) + Math.abs(sample.v) > 0.02 ? sample.u : 0.7);
      const vy = sample.v;
      const nx = b.x + vx * 0.016;
      const ny = b.y + vy * 0.016;
      const p0 = worldToViewportPx(b.x, b.y, 0.05);
      const p1 = worldToViewportPx(nx, ny, 0.05);
      b.x = nx;
      b.y = ny;

      if (sample.solid || b.x > 0.98 || b.x < -0.99 || b.y > 0.98 || b.y < -0.98 || b.life > b.maxLife) {
        b.x = wasmPreset.value === 0 ? (Math.random() * 1.6 - 0.8) : -0.96;
        b.y = (Math.random() * 1.72) - 0.86;
        b.life = 0;
        continue;
      }

      if (p0 && p1) {
        ctx.strokeStyle = isPaperTheme.value ? 'rgba(58, 56, 56, 0.45)' : 'rgba(226, 218, 210, 0.42)';
        ctx.lineWidth = 1.6;
        ctx.beginPath();
        ctx.moveTo(p0[0], p0[1]);
        ctx.lineTo(p1[0], p1[1]);
        ctx.stroke();

        ctx.beginPath();
        ctx.arc(p1[0], p1[1], 3.1, 0, Math.PI * 2);
        ctx.fillStyle = coreCol;
        ctx.fill();
        ctx.lineWidth = 1.25;
        ctx.strokeStyle = rimCol;
        ctx.stroke();
      }
    }

    // Update & render free-moving Lagrangian tracer point with live data label
    const ts = sampleVelocityAt(freeTracer.x, freeTracer.y);
    const tvx = wasmPreset.value === 0 ? (Math.abs(ts.u) > 0.01 ? ts.u : 0.4) : (Math.abs(ts.u) + Math.abs(ts.v) > 0.02 ? ts.u : 0.65);
    const tvy = ts.v;
    freeTracer.x += tvx * 0.014;
    freeTracer.y += tvy * 0.014;
    if (ts.solid || freeTracer.x > 0.96 || freeTracer.x < -0.98 || freeTracer.y > 0.95 || freeTracer.y < -0.95) {
      freeTracer.x = wasmPreset.value === 0 ? -0.6 : -0.94;
      freeTracer.y = wasmPreset.value === 0 ? 0.68 : (Math.random() * 1.1 - 0.55);
      freeTracer.trail = [];
    }
    const tp = worldToViewportPx(freeTracer.x, freeTracer.y, 0.09);
    if (tp) {
      freeTracer.trail.push([tp[0], tp[1]]);
      if (freeTracer.trail.length > 26) freeTracer.trail.shift();
      if (freeTracer.trail.length > 1) {
        ctx.strokeStyle = '#A89080';
        ctx.lineWidth = 2.2;
        ctx.beginPath();
        ctx.moveTo(freeTracer.trail[0][0], freeTracer.trail[0][1]);
        for (let k = 1; k < freeTracer.trail.length; k++) {
          ctx.lineTo(freeTracer.trail[k][0], freeTracer.trail[k][1]);
        }
        ctx.stroke();
      }
      ctx.beginPath();
      ctx.arc(tp[0], tp[1], 8.5, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(168, 144, 128, 0.28)';
      ctx.fill();
      ctx.beginPath();
      ctx.arc(tp[0], tp[1], 4.5, 0, Math.PI * 2);
      ctx.fillStyle = '#FFF8E8';
      ctx.fill();
      ctx.lineWidth = 2;
      ctx.strokeStyle = '#3A3838';
      ctx.stroke();

      const tagText = `PROBE |U| ${ts.spd.toFixed(2)} m/s`;
      ctx.font = '700 10px "JetBrains Mono", monospace';
      const tw = ctx.measureText(tagText).width + 12;
      const tx = Math.min(canvas.width - tw - 8, Math.max(8, tp[0] + 10));
      const ty = Math.max(22, tp[1] - 12);
      ctx.fillStyle = isPaperTheme.value ? 'rgba(58, 56, 56, 0.9)' : 'rgba(226, 218, 210, 0.94)';
      ctx.fillRect(tx, ty - 13, tw, 18);
      ctx.fillStyle = isPaperTheme.value ? '#FAF7F4' : '#1E1C1C';
      ctx.fillText(tagText, tx + 6, ty - 1);
    }
  };
  flowRafId = requestAnimationFrame(stepBeads);
}

function handleViewportKeydown(e: KeyboardEvent) {
  if (useBoardStage.value) return;
  const tag = (e.target as HTMLElement)?.tagName;
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
  const k = e.key.toLowerCase();
  if (k === 'q') orbitCamera(-18);
  else if (k === 'e') orbitCamera(18);
  else if (k === 'r') setCameraView('iso');
  else if (k === 'f') toggleFlowBeads();
  else if (k === 'l') toggleCalloutPins();
  else if (k === '=' || k === '+') zoomCamera(1.15);
  else if (k === '-') zoomCamera(0.86);
}

onMounted(async () => {
  initVtk();
  loadData(activeData.value);
  setCameraView('iso');

  if (vtkContainer.value && typeof ResizeObserver !== 'undefined') {
    viewportResizeObserver = new ResizeObserver(() => {
      const rect = vtkContainer.value?.getBoundingClientRect();
      if (rect) viewportSize.value = { w: rect.width, h: rect.height };
      if (fullScreenRenderer) {
        fullScreenRenderer.resize();
        if (renderWindow) renderWindow.render();
      }
      cameraRev.value++;
    });
    viewportResizeObserver.observe(vtkContainer.value);
  }

  window.addEventListener('keydown', handleViewportKeydown);
  startFlowBeadLoop();
  await initPresetPreview(wasmPreset.value);
});

onBeforeUnmount(() => {
  stopAnimation();
  stopWasmSolver();
  if (flowRafId !== null) {
    cancelAnimationFrame(flowRafId);
    flowRafId = null;
  }
  window.removeEventListener('keydown', handleViewportKeydown);
  if (viewportResizeObserver) {
    viewportResizeObserver.disconnect();
    viewportResizeObserver = null;
  }
  if (fullScreenRenderer) {
    fullScreenRenderer.delete();
  }
});

function initVtk() {
  const host = vtkMount.value || vtkContainer.value;
  if (!host) return;

  fullScreenRenderer = vtkFullScreenRenderWindow.newInstance({
    container: host,
    containerStyle: { height: '100%', width: '100%', position: 'relative' },
    background: isPaperTheme.value ? [0.875, 0.843, 0.808] : [0.102, 0.094, 0.094]
  });

  renderer = fullScreenRenderer.getRenderer();
  renderWindow = fullScreenRenderer.getRenderWindow();
  // Orthographic isometric projection matching #board drafting aesthetic
  renderer.getActiveCamera().setParallelProjection(true);

  actor = vtkActor.newInstance();
  mapper = vtkMapper.newInstance();
  actor.setMapper(mapper);
  renderer.addActor(actor);

  obstacleActor = vtkActor.newInstance();
  obstacleMapper = vtkMapper.newInstance();
  obstacleActor.setMapper(obstacleMapper);
  obstacleActor.setVisibility(false);
  renderer.addActor(obstacleActor);

  const interactor = renderWindow.getInteractor();
  if (interactor && typeof interactor.onInteractionEvent === 'function') {
    interactor.onInteractionEvent(() => { cameraRev.value++; });
    interactor.onEndInteractionEvent(() => { cameraRev.value++; });
  }
}

function loadData(data: ParsedMeshData) {
  activeData.value = data;
  if (useBoardStage.value || !mapper || !renderer || !renderWindow) {
    fieldRev.value++;
    loading.value = false;
    return;
  }

  loading.value = true;
  loadingMessage.value = 'Uploading mesh topology & scalar arrays to GPU...';
  try {
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
  } finally {
    fieldRev.value++;
    loading.value = false;
  }
}

/**
 * Fast zero-rebuild scalar update for smooth 60 FPS WebAssembly streaming.
 * Updates existing GPU point-data buffers in place without resetting camera or flashing loaders.
 */
function updateScalarsFast(data: ParsedMeshData) {
  if (useBoardStage.value) {
    activeData.value = data;
    fieldRev.value++;
    return;
  }
  if (!currentPolyData || activeData.value.pointCount !== data.pointCount) {
    loadData(data);
    return;
  }

  activeData.value = data;
  const pointData = currentPolyData.getPointData();
  for (const [key, field] of Object.entries(data.fields)) {
    const existing = pointData.getArrayByName(key);
    if (existing) {
      existing.setData(field.values);
      existing.modified();
    }
  }

  currentPolyData.modified();
  rescaleToDataRange();
  fieldRev.value++;
  renderWindow.render();
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
  if (actor) actor.setVisibility(isSourceVisible.value);
  if (obstacleActor) obstacleActor.setVisibility(isSourceVisible.value);
  if (renderWindow) renderWindow.render();
}

function toggleFilter(filterKey: 'slice' | 'clip' | 'contour' | 'glyph' | 'streamlines') {
  activeFilters.value[filterKey] = !activeFilters.value[filterKey];
  // Re-render
  renderWindow.render();
}

// Camera Presets & #board-style Orbit/Zoom/Inspector
function setCameraView(view: '+X' | '-X' | '+Y' | '-Y' | '+Z' | 'iso') {
  if (useBoardStage.value && boardStageRef.value) {
    boardStageRef.value.setNamedView(view);
    return;
  }
  if (!renderer) return;
  const cam = renderer.getActiveCamera();
  const fp = cam.getFocalPoint();
  const dist = cam.getDistance() || 3.4;

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
    cam.setFocalPoint(0, 0, 0.08);
    cam.setPosition(-1.6, -2.05, 1.85);
    cam.setViewUp(0, 0, 1);
    cam.setParallelScale(1.38);
  }

  renderer.resetCameraClippingRange();
  renderWindow.render();
  cameraRev.value++;
}

function orbitCamera(deg: number) {
  if (!renderer || !renderWindow) return;
  renderer.getActiveCamera().azimuth(deg);
  renderer.resetCameraClippingRange();
  renderWindow.render();
  cameraRev.value++;
}

function zoomCamera(factor: number) {
  if (!renderer || !renderWindow) return;
  renderer.getActiveCamera().zoom(factor);
  renderer.resetCameraClippingRange();
  renderWindow.render();
  cameraRev.value++;
}

function selectCalloutPin(pin: { id: string; world: [number, number, number] }) {
  selectedPinId.value = selectedPinId.value === pin.id ? null : pin.id;
  if (selectedPinId.value && renderer && renderWindow) {
    const cam = renderer.getActiveCamera();
    cam.setFocalPoint(pin.world[0] * 0.45, pin.world[1] * 0.45, pin.world[2] * 0.5);
    renderer.resetCameraClippingRange();
    renderWindow.render();
    cameraRev.value++;
  }
}

function toggleFlowBeads() {
  showFlowBeads.value = !showFlowBeads.value;
}

function toggleCalloutPins() {
  showCalloutPins.value = !showCalloutPins.value;
}

function applyCustomReynolds() {
  initPresetPreview(wasmPreset.value, customReynolds.value);
}

function handleViewportHover(e: MouseEvent) {
  if (!vtkContainer.value || !wasmEngine.value) {
    hoverTip.value.visible = false;
    return;
  }
  const rect = vtkContainer.value.getBoundingClientRect();
  const nx = ((e.clientX - rect.left) / Math.max(1, rect.width)) * 2 - 1;
  const ny = 1 - ((e.clientY - rect.top) / Math.max(1, rect.height)) * 2;
  const sample = sampleVelocityAt(nx * 0.9, ny * 0.9);
  probeInfo.value = { x: nx, y: ny, val: sample.spd };
  hoverTip.value = {
    visible: true,
    x: Math.min(rect.width - 170, Math.max(12, e.clientX - rect.left + 14)),
    y: Math.min(rect.height - 56, Math.max(12, e.clientY - rect.top - 12)),
    title: sample.solid ? `${activeCaseMeta.value.key.toUpperCase()} SOLID` : `|U| ${sample.spd.toFixed(2)} m/s`,
    detail: `p = ${sample.p.toFixed(3)} Pa · Re ${activeReynolds.value}`
  };
}

function resetCamera() {
  setCameraView('iso');
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
  if (wasmTimeHistory.value.length > step) {
    loadData(wasmTimeHistory.value[step].data);
    return;
  }
  // Re-generate time-dependent field variation
  const t = step * 0.05;
  const newData = generateProceduralCfdData(41, 41, t);
  loadData(newData);
}

function startWasmStepLoop() {
  if (wasmIntervalId) clearInterval(wasmIntervalId);
  isLiveStreaming.value = true;
  isWasmRunning.value = true;
  wasmIntervalId = setInterval(() => {
    if (!wasmEngine.value || !isWasmRunning.value) return;
    const out = wasmEngine.value.step(2);
    wasmLogs.value.push(...out.openfoamLog);
    if (wasmLogs.value.length > 150) {
      wasmLogs.value = wasmLogs.value.slice(-150);
    }
    wasmTimeHistory.value.push({ time: out.time, data: out.meshData, files: {} });
    if (wasmTimeHistory.value.length > 120) {
      wasmTimeHistory.value = wasmTimeHistory.value.slice(-120);
    }
    currentTimeIndex.value = wasmTimeHistory.value.length - 1;
    totalTimeSteps.value = Math.max(50, wasmTimeHistory.value.length);
    updateScalarsFast(out.meshData);
  }, 75);
}

async function initPresetPreview(presetId: number, reOverride?: number) {
  stopWasmSolver();
  const meta = CASE_META[presetId] || CASE_META[4];
  const re = reOverride ?? meta.re;
  customReynolds.value = re;

  const engine = markRaw(new OpenFoamWasmEngine(41, 41, re, meta.dt));
  await engine.initNativeWasm(presetId);
  const out = engine.step(14);
  wasmEngine.value = engine;
  wasmTimeHistory.value = [{ time: out.time, data: out.meshData, files: {} }];
  currentDatasetName.value = `openfoam_${meta.key}.foam`;
  wasmLogs.value = out.openfoamLog;
  loadData(out.meshData);
  updateObstacleActor();
  setCameraView('iso');
  startWasmStepLoop();
}

watch(wasmPreset, (nextPreset) => {
  initPresetPreview(nextPreset);
});

watch(useBoardStage, (isBoard) => {
  if (!isBoard && activeData.value) {
    requestAnimationFrame(() => {
      if (fullScreenRenderer) fullScreenRenderer.resize();
      loadData(activeData.value);
      updateObstacleActor();
      setCameraView('iso');
    });
  }
});

// In-Browser OpenFOAM icoFoam WebAssembly Solver
async function runOpenFoamWasm() {
  if (isWasmRunning.value) {
    stopWasmSolver();
    return;
  }

  loading.value = true;
  loadingMessage.value = 'Instantiating C++20 OpenFOAM icoFoam WebAssembly FVM Solver...';
  activeDockTab.value = 'log';

  try {
    const meta = activeCaseMeta.value;
    const engine = markRaw(new OpenFoamWasmEngine(41, 41, activeReynolds.value, meta.dt));
    const usingNativeWasm = await engine.initNativeWasm(wasmPreset.value);
    const presetLabel = meta.key;

    wasmLogs.value = [
      '/*--------------------------------*- C++ -*----------------------------------*\\',
      '| =========                 |                                                 |',
      '| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |',
      '|  \\\\    /   O peration     | Version:  v2406 (WebAssembly Build)             |',
      '|   \\\\  /    A nd           | Website:  www.openfoam.com                      |',
      '|    \\\\/     M anipulation  | Solver:   icoFoam (PISO Transient Incompressible)|',
      '\\*---------------------------------------------------------------------------*/',
      usingNativeWasm
        ? `[WASM] Native C++20 Emscripten binary (/wasm/fvm_solver.wasm) active [${presetLabel}]`
        : `[JS] Clean-room TypeScript FVM engine initialized [${presetLabel}]`,
      'Create time',
      'Create mesh for time = 0 (41 x 41 cells = 1600)',
      `Reading transportProperties: nu [0 2 -1 0 0 0 0] ${(1 / activeReynolds.value).toFixed(5)}`,
      'Reading field p [0 2 -2 0 0 0 0]',
      'Reading field U [0 1 -1 0 0 0 0]',
      'Starting time loop (PISO algorithm)'
    ];

    const out = engine.step(2);
    wasmEngine.value = engine;
    wasmTimeHistory.value = [{ time: out.time, data: out.meshData, files: {} }];
    currentDatasetName.value = `openfoam_wasm_${presetLabel}.foam`;
    loadData(out.meshData);
    updateObstacleActor();
    setCameraView('iso');
    startWasmStepLoop();
  } catch (err: any) {
    wasmLogs.value.push(`[WASM Error] ${err?.message || err}`);
  } finally {
    loading.value = false;
  }
}

function stopWasmSolver() {
  isWasmRunning.value = false;
  if (wasmIntervalId) {
    clearInterval(wasmIntervalId);
    wasmIntervalId = null;
  }
}

function togglePaperTheme() {
  isPaperTheme.value = !isPaperTheme.value;
  updateObstacleActor();
  if (renderer && renderWindow) {
    if (isPaperTheme.value) {
      renderer.setBackground(0.875, 0.843, 0.808); // Dimmed Warm Earth Stone (#DFD7CE)
    } else {
      renderer.setBackground(0.102, 0.094, 0.094); // Dimmed Earth Near Black (#1A1818)
    }
    renderWindow.render();
  }
}

function triggerBreakCfl() {
  if (!wasmEngine.value) return;
  wasmEngine.value.autoSelfHeal = false;
  wasmEngine.value.dt = 0.08; // Intentional CFL violation (> 1.0)
  wasmLogs.value.unshift('[Break-on-Purpose] Disabled Self-Heal & spiked dt = 0.080s (Co > 1.0)! Click "Self-Heal" to recover.');
  activeDockTab.value = 'log';
}

function triggerSelfHeal() {
  if (!wasmEngine.value) return;
  wasmEngine.value.autoSelfHeal = true;
  wasmEngine.value.dt = activeCaseMeta.value.dt;
  wasmLogs.value.unshift(`[Self-Heal] Re-enabled C++20 adaptive CFL guard & restored safe dt = ${wasmEngine.value.dt.toFixed(4)}s.`);
  activeDockTab.value = 'log';
}

async function routeWithLayaAi() {
  const prompt = layaPrompt.value.trim();
  if (!prompt || layaRouting.value) return;
  layaRouting.value = true;
  layaStatusText.value = 'Routing...';
  activeDockTab.value = 'log';

  try {
    const apiBase = `http://${window.location.hostname}:8000`;
    const resp = await fetch(`${apiBase}/api/ai/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt })
    });
    const data = await resp.json();
    if (data.ok && (data.preset || data.simulation_spec)) {
      const geoType = data.simulation_spec?.geometry?.type || data.route || 'simple_house';
      const geoToPreset: Record<string, number> = {
        house: 4, simple_house: 4, tower: 3, building_fsi: 3,
        cylinder: 1, airfoil: 5, venturi: 2, cavity: 0
      };
      wasmPreset.value = data.preset?.preset_id ?? geoToPreset[geoType] ?? 4;
      const reVal = data.preset?.reynolds ?? data.simulation_spec?.fluid?.reynolds ?? activeCaseMeta.value.re;
      const dtVal = data.preset?.dt ?? data.simulation_spec?.numerics?.dt ?? activeCaseMeta.value.dt;
      layaStatusText.value = `${geoType} (Re=${reVal})`;
      if (isWasmRunning.value) stopWasmSolver();
      await runOpenFoamWasm();
      wasmLogs.value.unshift(
        `[OpenZess AI] "${prompt}" -> shape=${geoType} (preset_id=${wasmPreset.value}, Re=${reVal}, dt=${dtVal})`
      );
    } else {
      layaStatusText.value = 'Error';
      wasmLogs.value.push(`[OpenZess AI Error] ${data.error || 'Unknown error'}`);
    }
  } catch (err: any) {
    layaStatusText.value = 'Offline';
    wasmLogs.value.push(`[OpenZess AI Error] ${err?.message || err}`);
  } finally {
    layaRouting.value = false;
  }
}

function downloadOpenFoamTimeCase() {
  const baseFiles = generateOpenFoamCase(100.0);
  let caseContent = '# OpenFOAM v2406 WebAssembly Export\n';
  caseContent += 'Case generated live in-browser using WebAssembly icoFoam solver.\n\n';
  
  for (const [path, content] of Object.entries(baseFiles)) {
    caseContent += `\n=== FILE: ${path} ===\n${content}\n`;
  }

  // Include latest time directory files if available
  if (wasmTimeHistory.value.length > 0) {
    const latest = wasmTimeHistory.value[wasmTimeHistory.value.length - 1];
    for (const [path, content] of Object.entries(latest.files)) {
      caseContent += `\n=== FILE: ${path} ===\n${content}\n`;
    }
  }

  const blob = new Blob([caseContent], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `openfoam_wasm_case_${Date.now()}.txt`;
  a.click();
  URL.revokeObjectURL(url);
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
  representationMode.value = 'surface';
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
  padding: 8px 16px;
  background: #1b212c;
  border-bottom: 1px solid #2d3748;
  font-size: 12px;
  gap: 14px;
}

.pv-brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.pv-logo-badge {
  background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
  color: #fff;
  font-weight: 800;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  letter-spacing: 0.5px;
}

.pv-app-title {
  font-weight: 700;
  font-size: 14px;
  color: #f8fafc;
}

.pv-badge-pill {
  background: #0f172a;
  border: 1px solid #334155;
  color: #38bdf8;
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 12px;
}

.pv-top-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pv-select-compact {
  background: #232b38;
  color: #e2e8f0;
  border: 1px solid #3b475c;
  border-radius: 5px;
  padding: 5px 10px;
  font-size: 12px;
  cursor: pointer;
  outline: none;
  transition: border-color 0.2s ease, background 0.2s ease;
}

.pv-select-compact:hover,
.pv-select-compact:focus {
  border-color: #60a5fa;
  background: #2a3444;
}

.pv-ai-input {
  width: 210px;
  padding: 4px 9px;
  background: #171d27;
  color: #f1f5f9;
  border: 1px solid #3b475c;
  border-radius: 4px;
  font-size: 11.5px;
  outline: none;
  transition: border-color 0.2s ease;
}

.pv-ai-input:focus {
  border-color: #38bdf8;
}

.pv-ai-btn {
  background: #0284c7 !important;
  border-color: #38bdf8 !important;
  color: #ffffff !important;
  font-weight: 600;
}

.pv-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #283140;
  color: #e2e8f0;
  border: 1px solid #3c485c;
  border-radius: 5px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.18s cubic-bezier(0.22, 1, 0.36, 1),
              border-color 0.18s cubic-bezier(0.22, 1, 0.36, 1),
              transform 0.12s ease;
}

.pv-btn:active:not(:disabled) {
  transform: scale(0.98);
}

.pv-btn:hover:not(:disabled) {
  background: #3b495e;
  border-color: #64748b;
  color: #ffffff;
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
  background: #2563eb;
  border-color: #1d4ed8;
  color: #ffffff;
  font-weight: 600;
}

.pv-btn-accent:hover:not(:disabled) {
  background: #1d4ed8;
}

.pv-btn-wasm {
  background: #059669;
  border-color: #047857;
  color: #ffffff;
  font-weight: 600;
}

.pv-btn-wasm:hover:not(:disabled) {
  background: #047857;
}

.pv-status-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 12px;
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
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
}

.stats-chip {
  font-size: 12px;
  color: #cbd5e1;
  background: #1e293b;
  padding: 3px 8px;
  border-radius: 5px;
  border: 1px solid #334155;
}

/* Ribbon Toolbars Bar */
.paraview-ribbon-bar {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 8px 16px;
  background: #202734;
  border-bottom: 1px solid #2d3748;
  font-size: 12px;
  overflow-x: auto;
}

.ribbon-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-right: 18px;
  border-right: 1px solid #2d3748;
}

.ribbon-group:last-child {
  border-right: none;
}

.group-label {
  font-size: 10px;
  text-transform: uppercase;
  color: #94a3b8;
  font-weight: 700;
  letter-spacing: 0.6px;
}

.group-buttons {
  display: flex;
  align-items: center;
  gap: 5px;
}

.ribbon-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 11px;
  background: #2b3646;
  color: #e2e8f0;
  border: 1px solid #3e4d63;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.ribbon-btn:hover {
  background: #3c4a5f;
  color: #ffffff;
  border-color: #64748b;
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
  gap: 8px;
  font-size: 11px;
  color: #94a3b8;
  margin-top: 2px;
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
  min-width: 220px;
  max-width: 720px;
  flex-shrink: 0;
  background: #181e28;
  border-right: 1px solid #2d3748;
  display: flex;
  flex-direction: column;
  z-index: 10;
}

.dock-size-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 0 4px;
  flex-shrink: 0;
}

.dock-size-btn {
  background: transparent;
  border: 1px solid transparent;
  color: #94a3b8;
  width: 22px;
  height: 22px;
  border-radius: 4px;
  font-size: 11px;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}

.dock-size-btn:hover {
  color: #f1f5f9;
  background: rgba(148, 163, 184, 0.16);
}

.sidebar-resizer {
  width: 4px;
  flex-shrink: 0;
  cursor: col-resize;
  background: transparent;
  z-index: 12;
  transition: background 0.15s ease;
}

.sidebar-resizer:hover {
  background: var(--color-brand, #A89080);
}

.pv-sidebar-restore-btn {
  position: absolute;
  top: 12px;
  left: 12px;
  z-index: 20;
  padding: 5px 10px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
  background: rgba(35, 33, 33, 0.92);
  color: var(--color-earth-cream, #E2DAD2);
  border: 1px solid var(--color-earth-charcoal, #3A3838);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
}

.pv-sidebar-restore-btn:hover {
  border-color: var(--color-brand, #A89080);
}

.theme-paper .dock-size-btn {
  color: var(--color-earth-charcoal);
}

.theme-paper .dock-size-btn:hover {
  background: var(--surface);
  border-color: var(--color-earth-cream);
}

.theme-paper .pv-sidebar-restore-btn {
  background: #FAF7F4;
  color: var(--color-earth-charcoal);
  border: 1px solid var(--color-earth-cream);
  box-shadow: 0 2px 8px rgba(58, 56, 56, 0.1);
}

.theme-earth-dark .dock-size-btn {
  color: var(--color-earth-gray);
}

.theme-earth-dark .dock-size-btn:hover {
  color: var(--color-earth-cream);
  background: var(--surface);
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

/* OpenFOAM WASM Console Box */
.openfoam-console-box {
  background: #0a0d14;
  border: 1px solid #1e293b;
  border-radius: 4px;
  padding: 8px 10px;
  font-family: monospace;
  font-size: 10px;
  color: #94a3b8;
  max-height: 480px;
  overflow-y: auto;
  line-height: 1.5;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.console-header {
  color: #38bdf8;
  font-weight: bold;
  border-bottom: 1px solid #1e293b;
  padding-bottom: 4px;
  margin-bottom: 4px;
}

.console-line.time-line {
  color: #22c55e;
  font-weight: bold;
  margin-top: 4px;
}

.console-line.solve-line {
  color: #e2e8f0;
}

.console-line.cont-line {
  color: #f59e0b;
}

.console-empty {
  color: #64748b;
  font-style: italic;
  padding: 12px 0;
  text-align: center;
}

/* Viewport Area */
.paraview-viewport {
  flex: 1;
  position: relative;
  background: radial-gradient(circle at center, #3c4659 0%, #1e2533 100%);
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

/* Mobile & Tablet Responsive Layout (Wi-Fi Phone Support) */
@media (max-width: 768px) {
  .paraview-menu-bar {
    flex-wrap: wrap;
    padding: 6px 10px;
    gap: 8px;
  }

  .pv-top-actions {
    flex-wrap: wrap;
    gap: 6px;
  }

  .pv-status-right {
    display: none;
  }

  .paraview-workspace {
    flex-direction: column-reverse;
  }

  .paraview-dock-sidebar {
    width: 100%;
    min-width: 100%;
    max-width: 100%;
    height: 40vh;
    border-right: none;
    border-top: 1px solid #2d3748;
  }

  .paraview-viewport {
    min-height: 45vh;
  }

  .pv-scalar-bar-widget {
    width: 160px;
    padding: 6px 8px;
    top: 8px;
    right: 8px;
  }
}

/* ============================================================================
   Core Earth Color Palette — Dimmed Light & Dark Modes
   Cream #E2DAD2 | Warm Gray #B8AFA8 | Taupe #A89080 | Hover #978070
   Charcoal #3A3838 | Near Black #1E1C1C
   ============================================================================ */
.paraview-studio-container.theme-paper {
  background: #DFD7CE;
  color: var(--color-earth-charcoal);
  font-family: "Barlow", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.theme-paper .paraview-menu-bar,
.theme-paper .paraview-ribbon-bar {
  background: #D6CEC5;
  border-bottom: 1px solid #C2B7AC;
  color: var(--color-earth-charcoal);
}

.theme-paper .pv-app-title,
.theme-paper .panel-section-title {
  color: var(--color-earth-charcoal);
  border-color: #C2B7AC;
}

.theme-paper .pv-logo-badge {
  background: var(--color-brand);
  color: #FFFFFF;
}

.theme-paper .pv-badge-pill,
.theme-paper .stats-chip,
.theme-paper .status-chip {
  background: rgba(58, 56, 56, 0.06);
  border: 1px solid #C2B7AC;
  color: var(--color-earth-charcoal);
}

.theme-paper .pv-btn,
.theme-paper .ribbon-btn,
.theme-paper .pv-select-compact,
.theme-paper .pv-ai-input {
  background: #EAE3DC;
  color: var(--color-earth-charcoal);
  border: 1px solid #C2B7AC;
}

.theme-paper .pv-btn:hover:not(:disabled),
.theme-paper .ribbon-btn:hover {
  background: #E2DAD2;
  border-color: var(--color-brand);
  color: var(--color-earth-charcoal);
}

.theme-paper .pv-btn-primary,
.theme-paper .pv-ai-btn {
  background: var(--color-brand) !important;
  border-color: var(--color-brand) !important;
  color: #FFFFFF !important;
}

.theme-paper .pv-btn-primary:hover:not(:disabled),
.theme-paper .pv-ai-btn:hover:not(:disabled) {
  background: var(--color-brand-hover) !important;
  border-color: var(--color-brand-hover) !important;
}

.theme-paper .paraview-dock-sidebar {
  background: #D8D0C7;
  border-right: 1px solid #C2B7AC;
  color: var(--color-earth-charcoal);
}

.theme-paper .dock-tab-header {
  background: #CEC5BB;
  border-bottom: 1px solid #C2B7AC;
}

.theme-paper .dock-tab-btn {
  color: #6B6460;
}

.theme-paper .dock-tab-btn.active {
  background: #D8D0C7;
  color: var(--color-earth-charcoal);
  border-bottom-color: var(--color-brand);
}

.theme-paper .group-label,
.theme-paper .time-readout {
  color: #5C5653;
}

.theme-paper .paraview-viewport {
  background-color: #DFD7CE;
  background-image:
    linear-gradient(to right, rgba(58, 56, 56, 0.08) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(58, 56, 56, 0.08) 1px, transparent 1px);
  background-size: 32px 32px;
}

.theme-paper .pv-scalar-bar-widget,
.theme-paper .pv-probe-hud {
  background: rgba(231, 224, 216, 0.94);
  border: 1px solid #C2B7AC;
  color: var(--color-earth-charcoal);
  box-shadow: 0 2px 8px rgba(58, 56, 56, 0.1);
}

.theme-paper .scalar-bar-title,
.theme-paper .probe-tag,
.theme-paper .probe-val {
  color: var(--color-earth-charcoal);
}

.theme-paper .prop-group,
.theme-paper .pipeline-tree,
.theme-paper .openfoam-console-box,
.theme-paper .info-table {
  background: #E7E0D8;
  border: 1px solid #C2B7AC;
  color: var(--color-earth-charcoal);
}

.theme-paper .prop-group-header {
  background: #DCD3C9;
  color: var(--color-earth-charcoal);
  border-bottom: 1px solid #C2B7AC;
}

.theme-paper .prop-row {
  border-bottom: 1px solid #D3C9BF;
}

.theme-paper .prop-row label,
.theme-paper .info-table th,
.theme-paper .info-table td,
.theme-paper .console-empty {
  color: var(--color-earth-charcoal);
  border-color: #C2B7AC;
}

.theme-paper .val-label {
  color: #7D685A;
}

.theme-paper .prop-row select,
.theme-paper .prop-row input[type="text"],
.theme-paper .btn-micro,
.theme-paper .tree-node {
  background: #DFD7CE;
  color: var(--color-earth-charcoal);
  border: 1px solid #C2B7AC;
}

.theme-paper .btn-micro:hover,
.theme-paper .tree-node:hover {
  border-color: var(--color-brand);
  background: #E7E0D8;
}

.theme-paper .tree-node.selected {
  background: var(--color-brand);
  border-color: var(--color-brand);
  color: #FFFFFF;
}

/* Earth Dark Mode (.theme-earth-dark) */
.paraview-studio-container.theme-earth-dark {
  background: #1A1818;
  color: var(--color-earth-cream);
  font-family: "Barlow", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.theme-earth-dark .paraview-menu-bar,
.theme-earth-dark .paraview-ribbon-bar {
  background: #222020;
  border-bottom: 1px solid var(--color-earth-charcoal);
  color: var(--color-earth-cream);
}

.theme-earth-dark .pv-logo-badge {
  background: var(--color-brand);
  color: var(--color-earth-black);
}

.theme-earth-dark .pv-btn,
.theme-earth-dark .ribbon-btn,
.theme-earth-dark .pv-select-compact,
.theme-earth-dark .pv-ai-input {
  background: var(--surface);
  color: var(--color-earth-cream);
  border: 1px solid var(--border);
}

.theme-earth-dark .pv-btn:hover:not(:disabled),
.theme-earth-dark .ribbon-btn:hover {
  background: var(--color-earth-charcoal);
  border-color: var(--color-brand);
}

.theme-earth-dark .pv-btn-primary,
.theme-earth-dark .pv-ai-btn {
  background: var(--color-brand) !important;
  border-color: var(--color-brand) !important;
  color: var(--color-earth-black) !important;
}

.theme-earth-dark .pv-btn-primary:hover:not(:disabled),
.theme-earth-dark .pv-ai-btn:hover:not(:disabled) {
  background: var(--color-brand-hover) !important;
}

.theme-earth-dark .paraview-dock-sidebar {
  background: #211F1F;
  border-right: 1px solid var(--color-earth-charcoal);
}

.theme-earth-dark .dock-tab-header {
  background: #1A1818;
  border-bottom: 1px solid var(--color-earth-charcoal);
}

.theme-earth-dark .dock-tab-btn {
  color: var(--color-earth-gray);
}

.theme-earth-dark .dock-tab-btn.active {
  background: #211F1F;
  color: var(--color-earth-cream);
  border-bottom-color: var(--color-brand);
}

.theme-earth-dark .prop-group,
.theme-earth-dark .pipeline-tree,
.theme-earth-dark .openfoam-console-box {
  background: #262323;
  border-color: var(--color-earth-charcoal);
}

.theme-earth-dark .prop-group-header {
  background: #2D2A2A;
  color: var(--color-earth-cream);
  border-color: var(--color-earth-charcoal);
}

.theme-earth-dark .prop-row select,
.theme-earth-dark .prop-row input[type="text"],
.theme-earth-dark .btn-micro {
  background: #1E1C1C;
  color: var(--color-earth-cream);
  border-color: var(--color-earth-charcoal);
}

.theme-earth-dark .group-label,
.theme-earth-dark .time-readout {
  color: var(--color-earth-gray);
}

.theme-earth-dark .paraview-viewport {
  background-color: #1A1818;
  background-image:
    linear-gradient(to right, rgba(226, 218, 210, 0.05) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(226, 218, 210, 0.05) 1px, transparent 1px);
  background-size: 32px 32px;
}

.theme-earth-dark .pv-edu-strip {
  background: #222020;
  border-top: 1px solid var(--color-earth-charcoal);
  color: var(--color-earth-cream);
}

.theme-earth-dark .edu-pre {
  background: #1A1818;
  border-color: var(--color-earth-charcoal);
  color: var(--color-earth-cream);
}

/* Stage Mount, Flow Beads Canvas & SVG Elbow Leaders (#board style) */
.pv-vtk-mount {
  position: absolute;
  inset: 0;
  z-index: 1;
}

.pv-flow-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 4;
}

.pv-leaders-svg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 15;
}

.leader-path {
  fill: none;
  stroke: #5A5450;
  stroke-width: 1.4;
  stroke-dasharray: 4 3;
  transition: stroke 0.15s ease, stroke-width 0.15s ease;
}

.theme-earth-dark .leader-path {
  stroke: var(--color-earth-gray);
}

.leader-group.is-hot .leader-path {
  stroke: var(--color-brand);
  stroke-width: 2.2;
  stroke-dasharray: none;
}

.hotspot-halo {
  fill: rgba(168, 144, 128, 0.22);
  stroke: rgba(168, 144, 128, 0.55);
  stroke-width: 1;
  transition: transform 0.2s ease, fill 0.2s ease;
}

.hotspot-anchor {
  fill: var(--color-brand);
  stroke: #FFFFFF;
  stroke-width: 1.6;
}

.leader-end-dot {
  fill: var(--color-earth-charcoal);
}

.theme-earth-dark .leader-end-dot {
  fill: var(--color-earth-cream);
}

.leader-group.is-hot .hotspot-halo {
  fill: rgba(168, 144, 128, 0.38);
}

/* Interactive 3D Callout Pins */
.pv-callout-layer {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 18;
}

.pv-callout-pin {
  position: absolute;
  pointer-events: auto;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 9px 4px 6px;
  border-radius: 6px;
  background: rgba(231, 224, 216, 0.94);
  color: var(--color-earth-charcoal);
  border: 1.5px solid var(--color-earth-charcoal);
  font-family: "JetBrains Mono", monospace;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.35px;
  cursor: pointer;
  white-space: nowrap;
  box-shadow: 2px 2px 0 rgba(58, 56, 56, 0.85);
  transition: background 0.14s ease, border-color 0.14s ease, color 0.14s ease;
}

.theme-earth-dark .pv-callout-pin {
  background: rgba(38, 35, 35, 0.94);
  color: var(--color-earth-cream);
  border-color: var(--color-earth-gray);
  box-shadow: 2px 2px 0 rgba(0, 0, 0, 0.65);
}

.pv-callout-pin:hover,
.pv-callout-pin.hot,
.pv-callout-pin.active {
  background: var(--color-brand);
  border-color: var(--color-brand-hover);
  color: #FFFFFF;
}

.pin-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-brand);
  border: 1.5px solid #ffffff;
  flex-shrink: 0;
}

.pin-sub {
  opacity: 0.72;
  font-weight: 500;
  font-size: 9.5px;
  border-left: 1px solid currentColor;
  padding-left: 5px;
}

.pv-callout-card {
  position: absolute;
  left: 50%;
  bottom: 58px;
  transform: translateX(-50%);
  pointer-events: auto;
  width: 328px;
  background: rgba(231, 224, 216, 0.97);
  color: var(--color-earth-charcoal);
  border: 1.5px solid var(--color-earth-charcoal);
  border-radius: 8px;
  padding: 10px 14px;
  box-shadow: 3px 3px 0 rgba(58, 56, 56, 0.28);
}

.theme-earth-dark .pv-callout-card {
  background: rgba(34, 32, 32, 0.97);
  color: var(--color-earth-cream);
  border-color: var(--color-earth-gray);
}

.callout-card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  margin-bottom: 4px;
}

.callout-close {
  background: transparent;
  border: none;
  font-size: 15px;
  cursor: pointer;
  color: var(--color-earth-gray);
}

.callout-card-body {
  font-size: 11.5px;
  line-height: 1.45;
  color: #5C5754;
  margin: 0 0 6px 0;
}

.theme-earth-dark .callout-card-body {
  color: var(--color-earth-gray);
}

.callout-card-metric {
  font-family: "JetBrains Mono", monospace;
  font-size: 11px;
  font-weight: 600;
  color: var(--color-brand-hover);
  border-top: 1px solid #C2B7AC;
  padding-top: 5px;
}

.callout-inspector-controls {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #C2B7AC;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.insp-slider-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  font-size: 11px;
}

.insp-slider-label input[type="range"] {
  flex: 1;
  accent-color: var(--color-brand);
}

.insp-actions {
  display: flex;
  gap: 6px;
}

.insp-chip-btn {
  flex: 1;
  padding: 4px 6px;
  border-radius: 4px;
  border: 1px solid #C2B7AC;
  background: #DFD7CE;
  color: var(--color-earth-charcoal);
  font-size: 10.5px;
  font-weight: 600;
  cursor: pointer;
}

.insp-chip-btn:hover {
  background: var(--color-brand);
  border-color: var(--color-brand);
  color: #FFFFFF;
}

.theme-earth-dark .insp-chip-btn {
  background: #2C2929;
  color: var(--color-earth-cream);
  border-color: var(--color-earth-charcoal);
}

/* Hover Probe Tooltip */
.pv-hover-tip {
  position: absolute;
  pointer-events: none;
  z-index: 22;
  padding: 5px 9px;
  border-radius: 6px;
  background: rgba(58, 56, 56, 0.92);
  color: #FAF7F4;
  font-family: "JetBrains Mono", monospace;
  font-size: 10px;
  display: flex;
  flex-direction: column;
  gap: 1px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.22);
}

.pv-hover-tip span {
  opacity: 0.85;
  font-size: 9.5px;
}

/* Floating Bottom Viewbar (#board style) */
.pv-viewbar {
  position: absolute;
  left: 50%;
  bottom: 12px;
  transform: translateX(-50%);
  z-index: 20;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 999px;
  background: rgba(231, 224, 216, 0.94);
  border: 1px solid #C2B7AC;
  box-shadow: 0 3px 12px rgba(58, 56, 56, 0.14);
}

.theme-earth-dark .pv-viewbar {
  background: rgba(34, 32, 32, 0.94);
  border-color: var(--color-earth-charcoal);
}

.vb-btn {
  border: 1px solid transparent;
  background: transparent;
  color: var(--color-earth-charcoal);
  padding: 3px 8px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.theme-earth-dark .vb-btn {
  color: var(--color-earth-cream);
}

.vb-btn:hover {
  background: rgba(168, 144, 128, 0.22);
}

.vb-btn.vb-toggle.active {
  background: var(--color-brand);
  color: #FFFFFF;
}

.vb-sep {
  width: 1px;
  height: 14px;
  background: #C2B7AC;
}

.theme-earth-dark .vb-sep {
  background: var(--color-earth-charcoal);
}

/* Bottom Split Educational Panel */
.pv-edu-strip {
  display: grid;
  grid-template-columns: 1.15fr 1fr;
  gap: 12px;
  padding: 8px 16px;
  background: #D6CEC5;
  border-top: 1px solid #C2B7AC;
  color: var(--color-earth-charcoal);
}

.edu-heading {
  font-family: "JetBrains Mono", monospace;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.6px;
  color: #7D685A;
  margin-bottom: 4px;
}

.edu-desc {
  font-size: 12px;
  line-height: 1.45;
  margin: 0;
}

.edu-pre {
  margin: 0;
  padding: 6px 10px;
  background: #E7E0D8;
  border: 1px solid #C2B7AC;
  border-radius: 4px;
  font-family: "JetBrains Mono", monospace;
  font-size: 11px;
  line-height: 1.4;
  color: var(--color-earth-charcoal);
  overflow-x: auto;
}
</style>
