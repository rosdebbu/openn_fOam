<template>
  <div class="ai-assistant">
    <div class="ai-input-bar">
      <span class="ai-icon">🤖</span>
      <input
        type="text"
        v-model="prompt"
        placeholder="Ask AI: 'Explain why the vortex shifts to top right at Re=400...'"
        @keyup.enter="askAi"
      />
      <button class="btn-ask" :disabled="isAnalyzing || !prompt.trim()" @click="askAi">
        {{ isAnalyzing ? 'Thinking...' : 'Ask AI' }}
      </button>
    </div>

    <div v-if="response" class="ai-response-box">
      <div class="response-title">🤖 OpenZess Physics AI Insights (Re = {{ params.reynoldsNumber }}):</div>
      <ul class="response-points">
        <li><strong>Primary Vortex Core:</strong> Located near domain coordinates (x ≈ {{ (0.5 + 0.05 * Math.log10(params.reynoldsNumber)).toFixed(2) }}, y ≈ 0.58).</li>
        <li><strong>Boundary Layer Thickness:</strong> δ ≈ 1 / √Re = <strong>{{ (1 / Math.sqrt(params.reynoldsNumber)).toFixed(4) }} m</strong>.</li>
        <li><strong>Flow Regime:</strong> {{ params.reynoldsNumber < 400 ? 'Laminar steady flow with symmetric recirculating eddy.' : 'Transitional laminar vortex shedding beginning in secondary corners.' }}</li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import type { SimulationParams } from '../types/cfd';

const props = defineProps<{
  params: SimulationParams;
}>();

const prompt = ref('');
const isAnalyzing = ref(false);
const response = ref(false);

function askAi() {
  if (!prompt.value.trim()) return;
  isAnalyzing.value = true;
  response.value = false;

  setTimeout(() => {
    isAnalyzing.value = false;
    response.value = true;
  }, 600);
}
</script>

<style scoped>
.ai-assistant {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ai-input-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(15, 23, 42, 0.9);
  padding: 8px 14px;
  border-radius: 8px;
  border: 1px solid rgba(0, 210, 255, 0.2);
}

.ai-icon {
  font-size: 18px;
}

.ai-input-bar input {
  flex: 1;
  background: transparent;
  border: none;
  color: #f8fafc;
  font-size: 13px;
  outline: none;
}

.btn-ask {
  background: linear-gradient(135deg, #a855f7 0%, #6366f1 100%);
  color: white;
  border: none;
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn-ask:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ai-response-box {
  background: rgba(30, 41, 59, 0.8);
  border: 1px solid rgba(168, 85, 247, 0.3);
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 12px;
  color: #e2e8f0;
  line-height: 1.6;
}

.response-title {
  font-weight: 700;
  color: #c084fc;
  margin-bottom: 6px;
}

.response-points {
  margin: 0;
  padding-left: 18px;
}
</style>
