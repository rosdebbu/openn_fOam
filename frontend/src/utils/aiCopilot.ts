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
    { id: 'claude-3-5-sonnet-20241022', name: 'Claude 3.5 Sonnet', badge: 'SOTA Coding' },
    { id: 'claude-3-5-haiku-20241022', name: 'Claude 3.5 Haiku', badge: 'Ultra Fast' }
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
    { id: 'deepseek-r1:latest', name: 'DeepSeek R1 (Local)', badge: '100% Free / Offline' },
    { id: 'llama3:latest', name: 'Llama 3 (Local)', badge: 'Offline' },
    { id: 'mistral:latest', name: 'Mistral (Local)', badge: 'Offline' }
  ]
};

export function getStoredAiConfig(): AiProviderConfig {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      return { ...DEFAULT_AI_CONFIG, ...JSON.parse(raw) };
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

    if (config.provider === 'gemini') {
      const url = `https://generativelanguage.googleapis.com/v1beta/models/${config.model}:generateContent?key=${config.apiKey}`;
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
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

  try {
    if (config.provider === 'gemini') {
      const url = `https://generativelanguage.googleapis.com/v1beta/models/${config.model}:generateContent?key=${config.apiKey}`;
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents: [{ parts: [{ text: fullPrompt }] }],
          generationConfig: { maxOutputTokens: 800, temperature: 0.2 }
        })
      });
      const data = await res.json();
      const text = data.candidates?.[0]?.content?.parts?.[0]?.text || 'No response received from Gemini.';
      return { query: prompt, analysis: text };
    }

    // OpenAI, DeepSeek, Groq, Ollama
    let baseUrl = 'https://api.openai.com/v1';
    if (config.provider === 'deepseek') baseUrl = 'https://api.deepseek.com/v1';
    if (config.provider === 'groq') baseUrl = 'https://api.groq.com/openai/v1';
    if (config.provider === 'ollama') baseUrl = (config.customBaseUrl || 'http://localhost:11434') + '/v1';
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
