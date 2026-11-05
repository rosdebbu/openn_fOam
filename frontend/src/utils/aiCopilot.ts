import type Anthropic from '@anthropic-ai/sdk';
import type { AiProviderConfig, AiProviderType, AiResponse } from '../types/cfd';

const STORAGE_KEY = 'openzess_ai_copilot_config';

export const DEFAULT_AI_CONFIG: AiProviderConfig = {
  provider: 'gemini',
  apiKey: '',
  model: 'gemini-2.5-flash',
  customBaseUrl: ''
};

export const PROVIDER_MODELS: Record<AiProviderType, { id: string; name: string; badge: string }[]> = {
  gemini: [
    { id: 'gemini-2.5-flash', name: 'Gemini 2.5 Flash', badge: 'Ultra Fast / Recommended' },
    { id: 'gemini-1.5-pro', name: 'Gemini 1.5 Pro', badge: 'Deep Reasoning' },
    { id: 'gemini-2.0-flash', name: 'Gemini 2.0 Flash', badge: 'Fast Multimodal' }
  ],
  openai: [
    { id: 'gpt-4o', name: 'GPT-4o', badge: 'Omni Flagship' },
    { id: 'gpt-4o-mini', name: 'GPT-4o Mini', badge: 'Fast & Affordable' },
    { id: 'o3-mini', name: 'o3-mini', badge: 'STEM Reasoning' }
  ],
  claude: [
    { id: 'claude-opus-5-5', name: 'Claude Opus 5.5', badge: 'Most Capable / Recommended' },
    { id: 'claude-sonnet-5-5', name: 'Claude Sonnet 5.5', badge: 'Fast & Capable' },
    { id: 'claude-haiku-5-5', name: 'Claude Haiku 5.5', badge: 'Fastest' }
  ],
  deepseek: [
    { id: 'deepseek-chat', name: 'DeepSeek-V3', badge: 'Flagship Chat' },
    { id: 'deepseek-reasoner', name: 'DeepSeek-R1', badge: 'Deep Mathematical Reasoning' }
  ],
  groq: [
    { id: 'llama-3.3-70b-versatile', name: 'Llama 3.3 70B (Groq)', badge: '500+ Tokens/sec' },
    { id: 'mixtral-8x7b-32768', name: 'Mixtral 8x7B (Groq)', badge: 'Fast MoE' }
  ],
  ollama: [
    { id: 'qwen2.5-coder:7b', name: 'Qwen 2.5 Coder 7B (Local)', badge: 'Local Active' },
    { id: 'deepseek-r1:8b', name: 'DeepSeek R1 8B (Local)', badge: 'Local Active' },
    { id: 'qwen-16k:latest', name: 'Qwen 16k (Local)', badge: 'Local Active' },
    { id: 'qwen-64k:latest', name: 'Qwen 64k (Local)', badge: 'Local Active' },
    { id: 'deepseek-16k:latest', name: 'DeepSeek 16k (Local)', badge: 'Local Active' },
    { id: 'llama3:latest', name: 'Llama 3 (Local)', badge: 'Offline' },
    { id: 'mistral:latest', name: 'Mistral (Local)', badge: 'Offline' }
  ]
};

export function getStoredAiConfig(): AiProviderConfig {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const config: AiProviderConfig = { ...DEFAULT_AI_CONFIG, ...JSON.parse(raw) };
      // Saved Claude configs may still name retired model IDs (claude-3-5-*)
      if (config.provider === 'claude' && !PROVIDER_MODELS.claude.some(m => m.id === config.model)) {
        config.model = PROVIDER_MODELS.claude[0].id;
      }
      return config;
    }
  } catch (err) {
    console.error('Error loading AI config from localStorage:', err);
  }
  return { ...DEFAULT_AI_CONFIG };
}

export function saveStoredAiConfig(config: AiProviderConfig) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
  } catch (err) {
    console.error('Error saving AI config to localStorage:', err);
  }
}

export function clearStoredAiConfig() {
  localStorage.removeItem(STORAGE_KEY);
}

const SYSTEM_PROMPT = `You are the OpenZess AI CFD Co-Pilot, an elite aeronautical and fluid dynamics engineer specialized in OpenFOAM, Navier-Stokes numerical methods, and aerothermal physics.
Your goal is to assist the user in configuring fluid simulations, setting up OpenFOAM dictionaries (system/controlDict, system/fvSchemes, system/fvSolution, 0/U, 0/p, 0/T), checking mesh resolution, explaining aerodynamics (Lift/Drag, vorticity, boundary layers), and suggesting optimal solver parameters.
Respond clearly with concise scientific explanations and executable OpenFOAM dictionary snippets where applicable.`;

// --- Anthropic Claude (official SDK) -------------------------------------
// The key is the user's own, entered in this browser, so direct browser
// access is intended here. (Previously the Claude option fell through to the
// OpenAI code path and POSTed the Anthropic key to api.openai.com.)
// Loaded on first use so users of other providers never download the SDK
let sdkPromise: Promise<typeof Anthropic> | null = null;
function loadSdk(): Promise<typeof Anthropic> {
  sdkPromise ??= import('@anthropic-ai/sdk').then(mod => mod.default);
  return sdkPromise;
}

async function claudeClient(config: AiProviderConfig): Promise<Anthropic> {
  const AnthropicSDK = await loadSdk();
  return new AnthropicSDK({
    apiKey: config.apiKey,
    dangerouslyAllowBrowser: true,
    ...(config.customBaseUrl ? { baseURL: config.customBaseUrl } : {})
  });
}

async function describeClaudeError(err: unknown): Promise<string> {
  const AnthropicSDK = await loadSdk();
  if (err instanceof AnthropicSDK.AuthenticationError) return 'Invalid Anthropic API key.';
  if (err instanceof AnthropicSDK.RateLimitError) return 'Rate limited by the Claude API — retry shortly.';
  if (err instanceof AnthropicSDK.APIError) return `Claude API error ${err.status ?? ''}: ${err.message}`;
  return err instanceof Error ? err.message : String(err);
}

async function queryClaude(config: AiProviderConfig, prompt: string, context?: string): Promise<string> {
  const client = await claudeClient(config);
  const response = await client.beta.messages.create({
    model: config.model || 'claude-opus-5-5',
    max_tokens: 16000,
    system: SYSTEM_PROMPT,
    messages: [{
      role: 'user',
      content: `${context ? `Current Simulation Context:\n${context}\n\n` : ''}${prompt}`
    }],
    output_config: { effort: 'medium' },
    // Server-side fallback on a policy decline; a no-op on models without it
    betas: ['server-side-fallback-2026-07-01'],
    fallbacks: 'default'
  });
  if (response.stop_reason === 'refusal') {
    return '⚠️ Claude declined this request. Try rephrasing the question.';
  }
  const text = response.content
    .filter((block): block is Anthropic.Beta.BetaTextBlock => block.type === 'text')
    .map(block => block.text)
    .join('\n')
    .trim();
  return text || 'No response received from Claude.';
}

export async function testAiConnection(config: AiProviderConfig): Promise<{ success: boolean; latencyMs: number; message: string }> {
  const start = performance.now();
  try {
    if (config.provider === 'ollama') {
      const url = (config.customBaseUrl || 'http://localhost:11434').replace(/\/v1\/?$/, '') + '/api/tags';
      const res = await fetch(url);
      if (!res.ok) throw new Error(`Ollama server returned status ${res.status}`);
      const latency = Math.round(performance.now() - start);
      return { success: true, latencyMs: latency, message: `Connected to Local Ollama (${latency}ms)` };
    }

    if (!config.apiKey) {
      return { success: false, latencyMs: 0, message: 'Please enter an API Key first.' };
    }

    if (config.provider === 'claude') {
      try {
        const client = await claudeClient(config);
        await client.messages.create({
          model: config.model || 'claude-opus-5-5',
          max_tokens: 16,
          messages: [{ role: 'user', content: 'Ping: reply with OK.' }]
        });
      } catch (err) {
        throw new Error(await describeClaudeError(err));
      }
      const latency = Math.round(performance.now() - start);
      return { success: true, latencyMs: latency, message: `Claude API verified (${latency}ms)` };
    }

    if (config.provider === 'gemini') {
      // Key in a header, not the URL (URLs end up in logs and history)
      const url = `https://generativelanguage.googleapis.com/v1beta/models/${config.model}:generateContent`;
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'x-goog-api-key': config.apiKey },
        body: JSON.stringify({
          contents: [{ parts: [{ text: 'Ping: reply with "OK".' }] }]
        })
      });
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.error?.message || `HTTP ${res.status}`);
      }
      const latency = Math.round(performance.now() - start);
      return { success: true, latencyMs: latency, message: `Gemini API Verified (${latency}ms)` };
    }

    // OpenAI, DeepSeek, Groq (OpenAI-compatible format)
    let baseUrl = 'https://api.openai.com/v1';
    if (config.provider === 'deepseek') baseUrl = 'https://api.deepseek.com/v1';
    if (config.provider === 'groq') baseUrl = 'https://api.groq.com/openai/v1';
    if (config.customBaseUrl) baseUrl = config.customBaseUrl;

    const res = await fetch(`${baseUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${config.apiKey}`
      },
      body: JSON.stringify({
        model: config.model,
        messages: [{ role: 'user', content: 'Ping: reply with OK.' }],
        max_tokens: 5
      })
    });

    if (!res.ok) {
      const errJson = await res.json().catch(() => ({}));
      throw new Error(errJson.error?.message || `HTTP ${res.status}`);
    }

    const latency = Math.round(performance.now() - start);
    return { success: true, latencyMs: latency, message: `Connected to ${config.provider.toUpperCase()} (${latency}ms)` };
  } catch (err: any) {
    return { success: false, latencyMs: Math.round(performance.now() - start), message: err.message || 'Connection failed' };
  }
}

export async function queryAiCopilot(prompt: string, context?: string): Promise<AiResponse> {
  const config = getStoredAiConfig();
  if (!config.apiKey && config.provider !== 'ollama') {
    return {
      query: prompt,
      analysis: '⚠️ No LLM API Key is configured yet. Click **[ 🔑 Set AI Key ]** in the top navbar to configure Google Gemini, OpenAI, Claude, DeepSeek, Groq, or Local Ollama.',
      suggestedSolver: 'buoyantBoussinesqSimpleFoam'
    };
  }

  const fullPrompt = `${SYSTEM_PROMPT}\n\n${context ? `Current Simulation Context:\n${context}\n\n` : ''}User Query: ${prompt}`;

  if (config.provider === 'claude') {
    try {
      return { query: prompt, analysis: await queryClaude(config, prompt, context) };
    } catch (err) {
      return { query: prompt, analysis: `⚠️ AI Copilot error (claude): ${await describeClaudeError(err)}` };
    }
  }

  try {
    if (config.provider === 'gemini') {
      const url = `https://generativelanguage.googleapis.com/v1beta/models/${config.model}:generateContent`;
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'x-goog-api-key': config.apiKey },
        body: JSON.stringify({
          contents: [{ parts: [{ text: fullPrompt }] }],
          generationConfig: { maxOutputTokens: 800, temperature: 0.2 }
        })
      });
      const data = await res.json();
      const text = data.candidates?.[0]?.content?.parts?.[0]?.text || 'No response received from Gemini.';
      return { query: prompt, analysis: text };
    }

    // OpenAI-compatible providers: OpenAI, DeepSeek, Groq, Ollama
    let baseUrl = 'https://api.openai.com/v1';
    if (config.provider === 'deepseek') baseUrl = 'https://api.deepseek.com/v1';
    if (config.provider === 'groq') baseUrl = 'https://api.groq.com/openai/v1';
    if (config.provider === 'ollama') baseUrl = (config.customBaseUrl || 'http://localhost:11434').replace(/\/v1\/?$/, '') + '/v1';
    if (config.customBaseUrl && config.provider !== 'ollama') baseUrl = config.customBaseUrl;

    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (config.apiKey) headers['Authorization'] = `Bearer ${config.apiKey}`;

    const res = await fetch(`${baseUrl}/chat/completions`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        model: config.model,
        messages: [
          { role: 'system', content: SYSTEM_PROMPT },
          { role: 'user', content: `${context ? `Context: ${context}\n\n` : ''}${prompt}` }
        ],
        max_tokens: 800,
        temperature: 0.2
      })
    });

    const data = await res.json();
    const text = data.choices?.[0]?.message?.content || 'No response received.';
    return { query: prompt, analysis: text };
  } catch (err: any) {
    return {
      query: prompt,
      analysis: `⚠️ AI Copilot error (${config.provider}): ${err.message || 'Request failed'}. Verify your API key and connection.`
    };
  }
}
