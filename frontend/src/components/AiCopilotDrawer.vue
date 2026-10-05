<template>
  <transition name="slide-drawer">
    <aside v-if="isOpen" class="ai-copilot-drawer">
      <!-- Drawer Header -->
      <div class="drawer-header">
        <div class="header-title-row">
          <div class="title-with-icon">
            <span class="ai-header-icon">🤖</span>
            <div>
              <h3 class="drawer-title">AI Engineering Copilot</h3>
              <span class="drawer-subtitle">{{ providerDisplayName }}</span>
            </div>
          </div>
          <div class="header-actions">
            <button class="clear-btn" @click="clearHistory" title="Clear Chat History">
              🗑️
            </button>
            <button class="close-drawer-btn" @click="$emit('close')" title="Close Drawer (Esc)">
              ✕
            </button>
          </div>
        </div>

        <!-- Strategy Prompt Chips -->
        <div class="strategy-chips-scroll">
          <button
            v-for="(chip, i) in strategyChips"
            :key="i"
            class="strategy-chip-btn"
            @click="sendPrompt(chip.prompt)"
          >
            {{ chip.label }}
          </button>
        </div>
      </div>

      <!-- Scrollable Chat Message History -->
      <div class="chat-message-feed" ref="messageFeedRef">
        <div v-if="messages.length === 0" class="empty-state">
          <div class="empty-icon">🧠</div>
          <h4>Physics & OpenFOAM Assistant</h4>
          <p>
            Ask aerodynamic questions, request boundary condition repairs, or click a strategy chip above to analyze vehicle flows.
          </p>
        </div>

        <div
          v-for="(msg, index) in messages"
          :key="index"
          class="chat-bubble-row"
          :class="msg.role"
        >
          <div class="bubble-avatar">
            {{ msg.role === 'user' ? '👤' : '⚡' }}
          </div>
          <div class="bubble-content">
            <div class="bubble-sender">
              {{ msg.role === 'user' ? 'You' : 'OpenZess Physics AI' }}
              <span class="msg-time">{{ msg.time }}</span>
            </div>

            <!-- Text Content -->
            <div class="bubble-text">{{ msg.text }}</div>

            <!-- Actionable OpenFOAM Dictionary Snippet -->
            <div v-if="msg.dictCode" class="actionable-dict-box">
              <div class="dict-box-header">
                <span class="dict-label">📄 OpenFOAM v2406 Case Snippet</span>
                <button class="copy-code-btn" @click="copyCode(msg.dictCode)">
                  {{ copiedIndex === index ? '✓ Copied!' : '📋 Copy' }}
                </button>
              </div>
              <pre class="dict-code-pre"><code>{{ msg.dictCode }}</code></pre>
              <button class="apply-to-case-btn" @click="$emit('applySnippet', msg.dictCode)">
                ⚡ 1-Click Apply to OpenFOAM Case Hub
              </button>
            </div>
          </div>
        </div>

        <!-- Loading State -->
        <div v-if="isLoading" class="chat-bubble-row ai loading">
          <div class="bubble-avatar">⚡</div>
          <div class="bubble-content">
            <div class="bubble-sender">OpenZess Physics AI</div>
            <div class="typing-indicator">
              <span></span><span></span><span></span>
              <span class="loading-label">Computing Navier-Stokes & boundary equations...</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Drawer Input Bar -->
      <div class="drawer-input-area">
        <div class="input-container">
          <textarea
            v-model="inputPrompt"
            class="drawer-textarea"
            rows="2"
            placeholder="Ask AI: 'Analyze boundary layer stall at 14° AoA' or describe flow conditions... (Enter to send, Shift+Enter for newline)"
            @keydown.enter.exact.prevent="handleSend"
          ></textarea>
          <button
            class="drawer-send-btn"
            :disabled="isLoading || !inputPrompt.trim()"
            @click="handleSend"
            title="Send Message"
          >
            ➤
          </button>
        </div>
        <div class="input-footer">
          <span class="shortcut-tip">Press <strong>Enter</strong> to send · <strong>Shift + Enter</strong> for newline</span>
          <button class="settings-link-btn" @click="$emit('openSettings')">
            ⚙️ Configure AI Key
          </button>
        </div>
      </div>
    </aside>
  </transition>
</template>

<script setup lang="ts">
import { ref, computed, nextTick } from 'vue';
import type { SimulationParams, AiProviderConfig } from '../types/cfd';
import { queryAiCopilot } from '../utils/aiCopilot';

interface ChatMessage {
  role: 'user' | 'ai';
  text: string;
  time: string;
  dictCode?: string;
}

const props = defineProps<{
  isOpen: boolean;
  params: SimulationParams;
  aiConfig: AiProviderConfig;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'openSettings'): void;
  (e: 'applySnippet', code: string): void;
}>();

const messageFeedRef = ref<HTMLDivElement | null>(null);
const inputPrompt = ref('');
const isLoading = ref(false);
const copiedIndex = ref<number | null>(null);

const messages = ref<ChatMessage[]>([
  {
    role: 'ai',
    text: 'Welcome to OpenZess 3D Engineering Studio. I am your Physics & OpenFOAM Copilot. Select any vehicle archetype (F1, Drone, Submarine, Airfoil) or ask any aerothermal fluid question.',
    time: 'Now'
  }
]);

const strategyChips = [
  { label: '🏎️ F1 Downforce', prompt: 'Configure Formula 1 front wing in ground effect at 80 m/s with inverted multi-element downforce' },
  { label: '✈️ Wing Stall', prompt: 'Analyze NACA 0012 swept wing at 14 degrees angle of attack with boundary layer separation' },
  { label: '🚁 Drone Downwash', prompt: 'Simulate quadcopter multi-rotor propeller downwash and slipstream contraction in air' },
  { label: '🌊 Submarine Hull', prompt: 'Simulate submarine hydrodynamic teardrop hull in seawater at 20 knots with boundary layer wake' },
  { label: '🔥 Thermal Plume', prompt: 'Thermal plume rising with Boussinesq buoyancy at 350K' },
  { label: '🛠️ Mesh Refinement', prompt: 'Inspect mesh boundary layer y+ wall spacing and recommend cell grading for OpenFOAM v2406' }
];

const providerDisplayName = computed(() => {
  const p = props.aiConfig?.provider || 'gemini';
  const m = props.aiConfig?.model || 'gemini-1.5-flash';
  return `${p.toUpperCase()} · ${m}`;
});

function formatCurrentTime(): string {
  const d = new Date();
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

async function handleSend() {
  if (!inputPrompt.value.trim() || isLoading.value) return;
  const prompt = inputPrompt.value.trim();
  inputPrompt.value = '';
  await sendPrompt(prompt);
}

async function sendPrompt(prompt: string) {
  messages.value.push({
    role: 'user',
    text: prompt,
    time: formatCurrentTime()
  });

  isLoading.value = true;
  await scrollToBottom();

  const context = `Archetype: ${props.params.archetype}, Substance: ${props.params.substance}, Re: ${props.params.reynoldsNumber}, Solver: ${props.params.solverMode}`;

  try {
    const res = await queryAiCopilot(prompt, context);
    messages.value.push({
      role: 'ai',
      text: res.analysis,
      dictCode: res.openfoamDictSnippet,
      time: formatCurrentTime()
    });
  } catch (err: any) {
    messages.value.push({
      role: 'ai',
      text: `⚠️ Copilot response error: ${err.message || 'Check API key in settings'}`,
      time: formatCurrentTime()
    });
  } finally {
    isLoading.value = false;
    await scrollToBottom();
  }
}

async function scrollToBottom() {
  await nextTick();
  if (messageFeedRef.value) {
    messageFeedRef.value.scrollTop = messageFeedRef.value.scrollHeight;
  }
}

function clearHistory() {
  messages.value = [];
}

function copyCode(code: string) {
  navigator.clipboard.writeText(code);
  copiedIndex.value = 999;
  setTimeout(() => { copiedIndex.value = null; }, 1800);
}
</script>

<style scoped>
.ai-copilot-drawer {
  position: absolute;
  top: 56px;
  right: 0;
  bottom: 0;
  width: 480px;
  max-width: 90vw;
  background: rgba(14, 10, 20, 0.96);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-left: 1px solid rgba(168, 85, 247, 0.35);
  box-shadow: -8px 0 32px rgba(0, 0, 0, 0.7);
  display: flex;
  flex-direction: column;
  z-index: 40;
  overflow: hidden;
}

/* Slide Transition */
.slide-drawer-enter-active,
.slide-drawer-leave-active {
  transition: transform 0.28s cubic-bezier(0.16, 1, 0.3, 1);
}
.slide-drawer-enter-from,
.slide-drawer-leave-to {
  transform: translateX(100%);
}

/* Header */
.drawer-header {
  padding: 14px 16px 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: rgba(20, 14, 30, 0.7);
}

.header-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-with-icon {
  display: flex;
  align-items: center;
  gap: 10px;
}

.ai-header-icon {
  font-size: 24px;
}

.drawer-title {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: #f1f5f9;
}

.drawer-subtitle {
  font-size: 10px;
  color: #c084fc;
  font-family: 'JetBrains Mono', monospace;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.clear-btn,
.close-drawer-btn {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #cbd5e1;
  border-radius: 6px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.clear-btn:hover,
.close-drawer-btn:hover {
  background: rgba(239, 68, 68, 0.2);
  color: #fca5a5;
  border-color: rgba(239, 68, 68, 0.4);
}

/* Strategy Chips */
.strategy-chips-scroll {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.strategy-chips-scroll::-webkit-scrollbar {
  height: 4px;
}
.strategy-chips-scroll::-webkit-scrollbar-thumb {
  background: rgba(168, 85, 247, 0.3);
  border-radius: 4px;
}

.strategy-chip-btn {
  background: rgba(168, 85, 247, 0.12);
  border: 1px solid rgba(168, 85, 247, 0.28);
  color: #e9d5ff;
  border-radius: 20px;
  padding: 4px 10px;
  font-size: 11px;
  font-weight: 500;
  white-space: nowrap;
  cursor: pointer;
  transition: all 0.2s;
}

.strategy-chip-btn:hover {
  background: rgba(168, 85, 247, 0.25);
  border-color: #c084fc;
  color: #ffffff;
}

/* Chat Feed */
.chat-message-feed {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.empty-state {
  margin: auto;
  text-align: center;
  max-width: 320px;
  color: #94a3b8;
}

.empty-icon {
  font-size: 42px;
  margin-bottom: 8px;
}

.empty-state h4 {
  margin: 0 0 6px;
  color: #f1f5f9;
  font-size: 14px;
}

.empty-state p {
  margin: 0;
  font-size: 12px;
  line-height: 1.5;
}

/* Message Rows */
.chat-bubble-row {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.chat-bubble-row.user {
  flex-direction: row-reverse;
}

.bubble-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(168, 85, 247, 0.2);
  border: 1px solid rgba(168, 85, 247, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  flex-shrink: 0;
}

.chat-bubble-row.user .bubble-avatar {
  background: rgba(56, 189, 248, 0.2);
  border-color: rgba(56, 189, 248, 0.4);
}

.bubble-content {
  max-width: 82%;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.bubble-sender {
  font-size: 10px;
  font-weight: 600;
  color: #cbd5e1;
  display: flex;
  align-items: center;
  gap: 6px;
}

.chat-bubble-row.user .bubble-sender {
  justify-content: flex-end;
  color: #7dd3fc;
}

.msg-time {
  font-size: 9px;
  color: #64748b;
  font-weight: 400;
}

.bubble-text {
  background: rgba(30, 24, 45, 0.9);
  border: 1px solid rgba(168, 85, 247, 0.25);
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 12.5px;
  color: #f1f5f9;
  line-height: 1.55;
  white-space: pre-wrap;
  word-break: break-word;
}

.chat-bubble-row.user .bubble-text {
  background: rgba(14, 42, 65, 0.9);
  border-color: rgba(56, 189, 248, 0.35);
  color: #f8fafc;
}

/* Actionable Dict Box */
.actionable-dict-box {
  margin-top: 6px;
  background: #09060d;
  border: 1px solid rgba(56, 189, 248, 0.35);
  border-radius: 8px;
  overflow: hidden;
}

.dict-box-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(56, 189, 248, 0.1);
  padding: 6px 10px;
  border-bottom: 1px solid rgba(56, 189, 248, 0.2);
}

.dict-label {
  font-size: 10.5px;
  font-weight: 600;
  color: #38bdf8;
  font-family: 'JetBrains Mono', monospace;
}

.copy-code-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 11px;
  cursor: pointer;
  padding: 2px 6px;
}
.copy-code-btn:hover {
  color: #f1f5f9;
}

.dict-code-pre {
  margin: 0;
  padding: 10px;
  max-height: 200px;
  overflow-y: auto;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10.5px;
  color: #a7f3d0;
  background: #060408;
}

.apply-to-case-btn {
  width: 100%;
  background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
  color: white;
  border: none;
  padding: 7px 12px;
  font-size: 11.5px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}
.apply-to-case-btn:hover {
  opacity: 0.92;
}

/* Typing Indicator */
.typing-indicator {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 8px 12px;
  background: rgba(30, 24, 45, 0.8);
  border-radius: 8px;
  border: 1px solid rgba(168, 85, 247, 0.2);
}
.typing-indicator span:not(.loading-label) {
  width: 6px;
  height: 6px;
  background: #c084fc;
  border-radius: 50%;
  animation: bounce 1.2s infinite ease-in-out;
}
.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

.loading-label {
  font-size: 11px;
  color: #cbd5e1;
  margin-left: 6px;
}

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

/* Input Area */
.drawer-input-area {
  padding: 12px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(18, 12, 26, 0.9);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-container {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(168, 85, 247, 0.35);
  border-radius: 8px;
  padding: 8px 10px;
}

.drawer-textarea {
  flex: 1;
  background: transparent;
  border: none;
  color: #f8fafc;
  font-size: 12.5px;
  outline: none;
  resize: none;
  line-height: 1.45;
  font-family: inherit;
}

.drawer-textarea::placeholder {
  color: #64748b;
}

.drawer-send-btn {
  background: linear-gradient(135deg, #a855f7 0%, #6366f1 100%);
  color: white;
  border: none;
  border-radius: 6px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  cursor: pointer;
  flex-shrink: 0;
  transition: opacity 0.2s;
}

.drawer-send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.input-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.shortcut-tip {
  font-size: 10px;
  color: #64748b;
}

.settings-link-btn {
  background: transparent;
  border: none;
  color: #a855f7;
  font-size: 10.5px;
  cursor: pointer;
  padding: 0;
}
.settings-link-btn:hover {
  text-decoration: underline;
  color: #c084fc;
}
</style>
