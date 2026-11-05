<template>
  <div class="dict-editor">
    <div class="dict-file-tabs">
      <button
        v-for="file in dictFiles"
        :key="file.name"
        class="dict-file-tab"
        :class="{ active: selectedFileName === file.name }"
        @click="selectedFileName = file.name"
      >
        {{ file.name }}
      </button>
    </div>

    <div class="dict-content-wrapper" v-if="currentFile">
      <div class="dict-header">
        <span class="dict-path">{{ currentFile.path }}</span>
        <button class="btn-copy" @click="copyContent">
          {{ copied ? '✓ Copied' : '📋 Copy' }}
        </button>
      </div>

      <textarea
        class="dict-code-area"
        v-model="currentFile.content"
        spellcheck="false"
      ></textarea>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import type { SimulationParams, OpenFoamDictFile } from '../types/cfd';
import { getOpenFoamDicts } from '../utils/openfoamDicts';

const props = defineProps<{
  params: SimulationParams;
}>();

const dictFiles = ref<OpenFoamDictFile[]>(getOpenFoamDicts(props.params));
const selectedFileName = ref<string>('controlDict');
const copied = ref<boolean>(false);

watch(() => props.params, (newParams) => {
  dictFiles.value = getOpenFoamDicts(newParams);
}, { deep: true });

const currentFile = computed(() => {
  return dictFiles.value.find(f => f.name === selectedFileName.value);
});

function copyContent() {
  if (currentFile.value) {
    navigator.clipboard.writeText(currentFile.value.content);
    copied.value = true;
    setTimeout(() => { copied.value = false; }, 2000);
  }
}
</script>

<style scoped>
.dict-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 10px;
}

.dict-file-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  background: #0f172a;
  padding: 6px;
  border-radius: 6px;
}

.dict-file-tab {
  padding: 4px 10px;
  font-size: 11px;
  font-family: monospace;
  background: transparent;
  color: #94a3b8;
  border: 1px solid transparent;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s;
}

.dict-file-tab.active {
  background: #1e293b;
  color: #00d2ff;
  border-color: rgba(0, 210, 255, 0.3);
}

.dict-content-wrapper {
  display: flex;
  flex-direction: column;
  flex: 1;
  background: #090d16;
  border-radius: 8px;
  border: 1px solid #1e293b;
  overflow: hidden;
}

.dict-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 12px;
  background: #1e293b;
  border-bottom: 1px solid #334155;
}

.dict-path {
  font-size: 11px;
  font-family: monospace;
  color: #38bdf8;
}

.btn-copy {
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: #cbd5e1;
  font-size: 10px;
  padding: 3px 8px;
  border-radius: 4px;
  cursor: pointer;
}

.btn-copy:hover {
  background: rgba(255, 255, 255, 0.2);
}

.dict-code-area {
  flex: 1;
  width: 100%;
  min-height: 380px;
  background: #070a12;
  color: #e2e8f0;
  font-family: 'Fira Code', 'Consolas', monospace;
  font-size: 11px;
  line-height: 1.5;
  padding: 12px;
  border: none;
  resize: none;
  outline: none;
}
</style>
