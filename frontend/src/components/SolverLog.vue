<template>
  <div class="openfoam-terminal-card" :class="{ collapsed: isCollapsed }">
    <div class="terminal-header" @click="isCollapsed = !isCollapsed">
      <div class="header-left">
        <span class="term-icon">📟</span>
        <span class="term-title">Solver Log — {{ engineLabel }}</span>
        <span v-if="isPlaying" class="pulse-indicator"></span>
      </div>
      <div class="header-actions" @click.stop>
        <button class="term-action-btn" @click="isAutoScroll = !isAutoScroll" :title="isAutoScroll ? 'Auto-scroll ON' : 'Auto-scroll OFF'">
          {{ isAutoScroll ? '⬇ Auto-scroll' : '⏸ Paused' }}
        </button>
        <button class="term-action-btn" @click="emit('clear')" title="Clear log window">
          🗑 Clear
        </button>
        <button class="term-toggle-btn" @click="isCollapsed = !isCollapsed">
          {{ isCollapsed ? '▲' : '▼' }}
        </button>
      </div>
    </div>

    <div v-show="!isCollapsed" class="terminal-body" ref="termBodyRef">
      <div v-if="entries.length === 0" class="term-line info">
        <span class="line-text">No solver output yet — start a run.</span>
      </div>
      <div v-for="(line, idx) in entries" :key="idx" class="term-line" :class="line.type">
        <span class="line-time">[{{ line.time }}]</span>
        <span class="line-text">{{ line.text }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Every line here is produced from a real event of the simulation stream
// (frames, errors, engine fallbacks). The previous component printed
// fabricated OpenFOAM-style residuals from Math.random() every 1.5 s.
import { ref, computed, watch, nextTick } from 'vue';
import type { SolverMode } from '../types/cfd';

export interface SolverLogEntry {
  time: string;
  text: string;
  type: 'header' | 'solver' | 'force' | 'info' | 'error';
}

const props = defineProps<{
  entries: SolverLogEntry[];
  isPlaying: boolean;
  mode: SolverMode | 'rust_bare_metal';
}>();

const emit = defineEmits<{ (e: 'clear'): void }>();

const isCollapsed = ref(false);
const isAutoScroll = ref(true);
const termBodyRef = ref<HTMLDivElement | null>(null);

const engineLabel = computed(() => {
  switch (props.mode) {
    case 'ai': return 'instant preview (potential flow / Stokes)';
    case 'rust':
    case 'rust_bare_metal': return 'Rust kernel';
    default: return 'Python projection solver';
  }
});

watch(() => props.entries.length, () => {
  if (!isAutoScroll.value) return;
  nextTick(() => {
    if (termBodyRef.value) termBodyRef.value.scrollTop = termBodyRef.value.scrollHeight;
  });
});
</script>

<style scoped>
.openfoam-terminal-card {
  background: #0b0f16;
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.7);
  user-select: text;
  width: 100%;
}

.terminal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #141b24;
  border-bottom: 1px solid var(--border-subtle);
  cursor: pointer;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.term-icon {
  font-size: 14px;
}

.term-title {
  font-size: 11.5px;
  font-weight: 700;
  color: #38bdf8;
}

.pulse-indicator {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 6px #10b981;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.term-action-btn {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #94a3b8;
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 10px;
  cursor: pointer;
  font-family: inherit;
}

.term-action-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #ffffff;
}

.term-toggle-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 11px;
  cursor: pointer;
  padding: 2px 4px;
}

.terminal-body {
  padding: 10px 12px;
  height: 140px;
  overflow-y: auto;
  background: #090d14;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.openfoam-ascii-banner {
  font-size: 9px;
  color: #64748b;
  white-space: pre;
  line-height: 1.2;
  margin-bottom: 6px;
}

.term-line {
  display: flex;
  gap: 8px;
  font-size: 10.5px;
  line-height: 1.35;
}

.line-time {
  color: #64748b;
  font-size: 9.5px;
  flex-shrink: 0;
}

.term-line.header .line-text {
  color: #f1f5f9;
  font-weight: 600;
}

.term-line.solver .line-text {
  color: #38bdf8;
}

.term-line.p-solve .line-text {
  color: #c084fc;
}

.term-line.continuity .line-text {
  color: #34d399;
}

.term-line.force .line-text {
  color: #fbbf24;
  font-weight: 600;
}

.term-line.error .line-text {
  color: #f87171;
  font-weight: 600;
}

.term-line.info .line-text {
  color: #94a3b8;
}
</style>
