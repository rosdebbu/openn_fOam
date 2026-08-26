<template>
  <div v-if="isOpen" class="modal-backdrop" @click="close">
    <div class="modal-card" @click.stop>
      <!-- Header -->
      <div class="modal-header">
        <div class="modal-title-wrap">
          <span class="modal-icon">⚙️</span>
          <div>
            <h3 class="modal-title">AI Copilot & LLM Settings</h3>
            <p class="modal-subtitle">Configure your own API Key to power real-time OpenFOAM reasoning</p>
          </div>
        </div>
        <button class="modal-close-btn" @click="close">✕</button>
      </div>

      <!-- Body -->
      <div class="modal-body">
        <!-- Provider Selector -->
        <div class="form-group">
          <label class="form-label">Select LLM Provider</label>
          <div class="provider-grid">
            <button
              v-for="prov in providers"
              :key="prov.id"
              class="provider-btn"
              :class="{ active: localConfig.provider === prov.id }"
              @click="selectProvider(prov.id)"
            >
              <span class="provider-icon">{{ prov.icon }}</span>
              <span class="provider-name">{{ prov.name }}</span>
            </button>
          </div>
        </div>

        <!-- Model Selector -->
        <div class="form-group">
          <label class="form-label" for="model-select">Model</label>
          <select id="model-select" v-model="localConfig.model" class="form-select">
            <option v-for="m in currentModels" :key="m.id" :value="m.id">
              {{ m.name }} ({{ m.badge }})
            </option>
          </select>
        </div>

        <!-- API Key Input (Masked) -->
        <div v-if="localConfig.provider !== 'ollama'" class="form-group">
          <div class="label-with-link">
            <label class="form-label" for="api-key-input">API Key</label>
            <a :href="providerApiKeyUrl" target="_blank" rel="noopener" class="key-help-link">
              Get {{ localConfig.provider.toUpperCase() }} API Key ↗
            </a>
          </div>

          <div class="input-with-eye">
            <input
              id="api-key-input"
              :type="showKey ? 'text' : 'password'"
              v-model="localConfig.apiKey"
              class="form-input"
              :placeholder="`Paste your ${localConfig.provider} API key here...`"
            />
            <button class="eye-toggle" type="button" @click="showKey = !showKey">
              {{ showKey ? '🙈' : '👁️' }}
            </button>
          </div>
          <span class="privacy-note">🔒 Stored securely in your browser localStorage only. Never sent to any server.</span>
        </div>

        <!-- Custom Base URL (for Ollama / Self-hosted proxy) -->
        <div v-if="localConfig.provider === 'ollama'" class="form-group">
          <label class="form-label" for="ollama-url">Ollama Base URL</label>
          <input
            id="ollama-url"
            type="text"
            v-model="localConfig.customBaseUrl"
            class="form-input"
            placeholder="http://localhost:11434"
          />
          <span class="privacy-note">Make sure Ollama is running locally (`ollama run deepseek-r1`).</span>
        </div>

        <!-- Test Connection Section -->
        <div class="test-connection-section">
          <button
            class="test-btn"
            :disabled="isTesting"
            @click="runTestConnection"
          >
            <span v-if="!isTesting">⚡ Test Connection & Latency</span>
            <span v-else>⏳ Testing Connection...</span>
          </button>

          <div v-if="testResult" class="test-feedback" :class="{ success: testResult.success, error: !testResult.success }">
            <span>{{ testResult.success ? '✓' : '⚠️' }} {{ testResult.message }}</span>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="modal-footer">
        <button class="btn btn-secondary" @click="handleClearKey">
          🗑️ Clear Key
        </button>

        <div class="footer-actions">
          <button class="btn btn-secondary" @click="close">
            Cancel
          </button>
          <button class="btn btn-primary" @click="handleSave">
            💾 Save Configuration
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue';
import type { AiProviderConfig, AiProviderType } from '../types/cfd';
import { getStoredAiConfig, saveStoredAiConfig, clearStoredAiConfig, testAiConnection, PROVIDER_MODELS } from '../utils/aiCopilot';

const props = defineProps<{
  isOpen: boolean;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'saved', config: AiProviderConfig): void;
}>();

const providers: { id: AiProviderType; name: string; icon: string; url: string }[] = [
  { id: 'gemini', name: 'Google Gemini', icon: '♊', url: 'https://aistudio.google.com/app/apikey' },
  { id: 'openai', name: 'OpenAI', icon: '🟢', url: 'https://platform.openai.com/api-keys' },
  { id: 'claude', name: 'Anthropic Claude', icon: '🟣', url: 'https://console.anthropic.com/settings/keys' },
  { id: 'deepseek', name: 'DeepSeek', icon: '🐋', url: 'https://platform.deepseek.com/api_keys' },
  { id: 'groq', name: 'Groq (Ultra-Fast)', icon: '⚡', url: 'https://console.groq.com/keys' },
  { id: 'ollama', name: 'Local Ollama', icon: '🦙', url: 'https://ollama.com/' }
];

const localConfig = reactive<AiProviderConfig>(getStoredAiConfig());
const showKey = ref(false);
const isTesting = ref(false);
const testResult = ref<{ success: boolean; message: string } | null>(null);

const currentModels = computed(() => {
  return PROVIDER_MODELS[localConfig.provider] || [];
});

const providerApiKeyUrl = computed(() => {
  const p = providers.find(item => item.id === localConfig.provider);
  return p ? p.url : 'https://aistudio.google.com/';
});

function selectProvider(prov: AiProviderType) {
  localConfig.provider = prov;
  const models = PROVIDER_MODELS[prov];
  if (models && models.length > 0) {
    localConfig.model = models[0].id;
  }
  testResult.value = null;
}

async function runTestConnection() {
  isTesting.value = true;
  testResult.value = null;
  const res = await testAiConnection(localConfig);
  isTesting.value = false;
  testResult.value = res;
}

function handleSave() {
  saveStoredAiConfig({ ...localConfig });
  emit('saved', { ...localConfig });
  emit('close');
}

function handleClearKey() {
  localConfig.apiKey = '';
  clearStoredAiConfig();
  testResult.value = { success: true, message: 'API Key removed from browser.' };
}

function close() {
  emit('close');
}

watch(() => props.isOpen, (open) => {
  if (open) {
    Object.assign(localConfig, getStoredAiConfig());
    testResult.value = null;
  }
});
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(8px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.modal-card {
  width: 540px;
  max-width: 95vw;
  background: #141b24;
  border: 1px solid var(--border-active);
  border-radius: 12px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.8);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #19222f;
  border-bottom: 1px solid var(--border-subtle);
}

.modal-title-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
}

.modal-icon {
  font-size: 24px;
}

.modal-title {
  font-size: 15px;
  font-weight: 700;
  color: #ffffff;
  margin: 0;
}

.modal-subtitle {
  font-size: 11px;
  color: var(--text-secondary);
  margin: 2px 0 0 0;
}

.modal-close-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 16px;
  cursor: pointer;
  padding: 4px;
}

.modal-close-btn:hover {
  color: #ffffff;
}

.modal-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: #0f151e;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 12px;
  font-weight: 600;
  color: #cbd5e1;
}

.label-with-link {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.key-help-link {
  font-size: 11px;
  color: #38bdf8;
  text-decoration: none;
}

.key-help-link:hover {
  text-decoration: underline;
}

.provider-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.provider-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 12px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: #cbd5e1;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.provider-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
}

.provider-btn.active {
  background: rgba(168, 85, 247, 0.2);
  border-color: rgba(168, 85, 247, 0.6);
  color: #e9d5ff;
  box-shadow: 0 0 10px rgba(168, 85, 247, 0.25);
}

.form-select,
.form-input {
  background: #19222f;
  color: #f1f5f9;
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 12.5px;
  outline: none;
  transition: border-color 0.15s ease;
}

.form-select:focus,
.form-input:focus {
  border-color: #a855f7;
}

.input-with-eye {
  display: flex;
  position: relative;
}

.input-with-eye .form-input {
  flex: 1;
  padding-right: 38px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
}

.eye-toggle {
  position: absolute;
  right: 6px;
  top: 50%;
  transform: translateY(-50%);
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 14px;
  padding: 4px;
}

.privacy-note {
  font-size: 10px;
  color: #94a3b8;
}

/* Test Connection Section */
.test-connection-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 12px;
  background: rgba(0, 0, 0, 0.25);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.test-btn {
  background: rgba(56, 189, 248, 0.12);
  border: 1px solid rgba(56, 189, 248, 0.35);
  color: #38bdf8;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.test-btn:hover:not(:disabled) {
  background: rgba(56, 189, 248, 0.22);
}

.test-feedback {
  font-size: 11.5px;
  padding: 4px 8px;
  border-radius: 4px;
}

.test-feedback.success {
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
}

.test-feedback.error {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
}

/* Modal Footer */
.modal-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  background: #19222f;
  border-top: 1px solid var(--border-subtle);
}

.footer-actions {
  display: flex;
  gap: 10px;
}

.btn {
  padding: 8px 14px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.15s ease;
}

.btn-primary {
  background: linear-gradient(135deg, #a855f7 0%, #6366f1 100%);
  color: #ffffff;
  box-shadow: 0 2px 10px rgba(168, 85, 247, 0.4);
}

.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 15px rgba(168, 85, 247, 0.6);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.08);
  color: #cbd5e1;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.15);
  color: #ffffff;
}
</style>
