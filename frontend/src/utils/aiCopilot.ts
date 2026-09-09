import type { AiProviderConfig, SimulationArchetype, FluidSubstanceId } from '../types/cfd';

const STORAGE_KEY = 'openzess_ai_copilot_config';

export interface AiSimulationConfig {
  archetype?: SimulationArchetype;
  substance?: FluidSubstanceId;
  reynoldsNumber?: number;
  angleDegrees?: number;
  autoRun?: boolean;
  summary: string;
  physicsExplanation?: string;
}

export interface AiResponse {
  query: string;
  analysis: string;
  dictCode?: string;
  simConfig?: AiSimulationConfig;
  suggestedSolver?: string;
}

export interface AiModelOption {
  id: string;
  name: string;
  badge: string;
}

export const PROVIDER_MODELS: Record<string, AiModelOption[]> = {
  gemini: [
    { id: 'gemini-2.5-flash', name: 'Gemini 2.5 Flash', badge: 'Fastest' },
    { id: 'gemini-1.5-pro', name: 'Gemini 1.5 Pro', badge: 'Reasoning' },
    { id: 'gemini-1.5-flash', name: 'Gemini 1.5 Flash', badge: 'Light' }
  ],
  openai: [
    { id: 'gpt-4o', name: 'GPT-4o (Omni)', badge: 'Flagship' },
    { id: 'gpt-4o-mini', name: 'GPT-4o Mini', badge: 'Fast' },
    { id: 'o3-mini', name: 'o3-mini (Reasoning)', badge: 'Math' }
  ],
  claude: [
    { id: 'claude-3-7-sonnet-20250219', name: 'Claude 3.7 Sonnet', badge: 'Hybrid' },
    { id: 'claude-3-5-haiku-20241022', name: 'Claude 3.5 Haiku', badge: 'Speed' }
  ],
  deepseek: [
    { id: 'deepseek-chat', name: 'DeepSeek V3', badge: 'Optimal' },
    { id: 'deepseek-reasoner', name: 'DeepSeek R1', badge: 'Chain of Thought' }
  ],
  groq: [
    { id: 'llama-3.3-70b-versatile', name: 'Llama 3.3 70B', badge: 'Ultra-Fast' },
    { id: 'llama3-8b-8192', name: 'Llama 3 8B', badge: 'Instant' },
    { id: 'mixtral-8x7b-32768', name: 'Mixtral 8x7B', badge: 'Mixture of Experts' }
  ],
  ollama: [
    { id: 'llama3:latest', name: 'Llama 3 (Local)', badge: 'Local Private' },
    { id: 'mistral:latest', name: 'Mistral 7B (Local)', badge: 'Local Private' },
    { id: 'deepseek-r1:latest', name: 'DeepSeek R1 (Local)', badge: 'Local Private' }
  ]
};

export function getStoredAiConfig(): AiProviderConfig {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch (_) {}
  return {
    provider: 'gemini',
    apiKey: '',
    model: 'gemini-2.5-flash'
  };
}

export function saveStoredAiConfig(config: AiProviderConfig): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
}

export function clearStoredAiConfig(): void {
  localStorage.removeItem(STORAGE_KEY);
}

const SYSTEM_PROMPT = `You are OpenZess CFD Autonomous Copilot, an expert computational fluid dynamics engineer.
Your goal is to understand the user's physics simulation goals and automatically configure and run OpenFOAM CFD simulations.

When the user asks to simulate, test, or setup a scenario, analyze the physical intent and return an executable JSON action block enclosed in triple backticks:
\`\`\`json
{
  "action": "CONFIG_SIMULATION",
  "archetype": "airfoil" | "cylinder" | "cavity" | "venturi",
  "substance": "air" | "water" | "oil" | "co2" | "ethanol",
  "reynoldsNumber": 100,
  "angleDegrees": 0.0,
  "autoRun": true,
  "summary": "Brief 1-line configuration title",
  "physicsExplanation": "Physical explanation of expected boundary layer, separation point, drag, and vortex behavior."
}
\`\`\`

Available archetypes:
- 'cylinder': Circular bluff body with von Kármán vortex shedding.
- 'airfoil': NACA 0012 aerodynamic wing with lift and stall.
- 'cavity': Lid-driven shear cavity (Ghia 1982 benchmark).
- 'venturi': Compressible nozzle throat with Bernoulli acceleration.

Available substances:
- 'air': rho=1.225, nu=1.5e-5
- 'water': rho=998, nu=1.0e-6
- 'oil': rho=890, nu=4.5e-5
- 'co2': rho=1.98, nu=8.3e-6
- 'ethanol': rho=789, nu=1.5e-6`;

// Fast Local Intent Parser (Works instantly offline without an API key)
export function parseLocalSimulationIntent(prompt: string): AiSimulationConfig | null {
  const p = prompt.toLowerCase();

  let archetype: SimulationArchetype | undefined = undefined;
  if (p.includes('airfoil') || p.includes('wing') || p.includes('naca') || p.includes('aerodynamic')) {
    archetype = 'airfoil';
  } else if (p.includes('cylinder') || p.includes('bluff') || p.includes('vortex') || p.includes('karman')) {
    archetype = 'cylinder';
  } else if (p.includes('cavity') || p.includes('box') || p.includes('lid') || p.includes('shear')) {
    archetype = 'cavity';
  } else if (p.includes('venturi') || p.includes('nozzle') || p.includes('throat')) {
    archetype = 'venturi';
  }

  let substance: FluidSubstanceId | undefined = undefined;
  if (p.includes('water') || p.includes('liquid') || p.includes('h2o')) substance = 'water';
  else if (p.includes('oil') || p.includes('lubricant') || p.includes('viscous')) substance = 'oil';
  else if (p.includes('co2') || p.includes('carbon dioxide')) substance = 'co2';
  else if (p.includes('ethanol') || p.includes('alcohol')) substance = 'ethanol';
  else if (p.includes('air') || p.includes('gas') || p.includes('atmosphere')) substance = 'air';

  // Reynolds number extraction (e.g. "Re=200", "Re 500", "Reynolds 300")
  let reynoldsNumber: number | undefined = undefined;
  const reMatch = p.match(/(?:re|reynolds)(?:\s*=|\s+)(\d+(?:\.\d+)?)/i);
  if (reMatch) {
    reynoldsNumber = Math.max(10, Math.min(10000, parseFloat(reMatch[1])));
  }

  // Angle of attack extraction (e.g. "12 deg", "15 degrees", "aoa=10", "aoa 8")
  let angleDegrees: number | undefined = undefined;
  const angleMatch = p.match(/(\d+(?:\.\d+)?)\s*(?:deg|degrees|°)/i) || p.match(/aoa(?:\s*=|\s+)(\d+(?:\.\d+)?)/i);
  if (angleMatch) {
    angleDegrees = Math.max(-25, Math.min(25, parseFloat(angleMatch[1])));
  }

  const autoRun = p.includes('run') || p.includes('simulate') || p.includes('start') || p.includes('launch') || p.includes('test') || p.includes('make');

  if (archetype || substance || reynoldsNumber !== undefined || angleDegrees !== undefined) {
    const archName = archetype ? archetype.toUpperCase() : 'Current Domain';
    const subName = substance ? substance.toUpperCase() : 'Selected Substance';
    const reText = reynoldsNumber ? `Re=${reynoldsNumber}` : 'Default Re';
    const aoaText = angleDegrees !== undefined ? `AoA=${angleDegrees}°` : '';

    return {
      archetype,
      substance,
      reynoldsNumber,
      angleDegrees,
      autoRun,
      summary: `Autonomous Setup: ${archName} | ${subName} | ${reText} ${aoaText}`.trim(),
      physicsExplanation: archetype === 'airfoil'
        ? `NACA 0012 wing with ${angleDegrees !== undefined ? angleDegrees : 0}° angle of attack. Flow will produce positive aerodynamic lift with adverse pressure gradient along the suction surface.`
        : archetype === 'cylinder'
        ? `Circular bluff body at ${reText}. Flow experiences boundary layer separation on both shoulders, producing alternating von Kármán vortex shedding.`
        : `Shear-driven recirculating flow with primary core vortex and corner separation eddies.`
    };
  }

  return null;
}

export async function testAiConnection(config: AiProviderConfig): Promise<{ success: boolean; latencyMs: number; message: string }> {
  const start = performance.now();
  try {
    if (!config.apiKey && config.provider !== 'ollama') {
      return { success: false, latencyMs: 0, message: 'Please enter an API Key first.' };
    }

    if (config.provider === 'gemini') {
      const url = `https://generativelanguage.googleapis.com/v1beta/models/${config.model}:generateContent?key=${config.apiKey}`;
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ contents: [{ parts: [{ text: 'Ping: reply with "OK".' }] }] })
      });
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.error?.message || `HTTP ${res.status}`);
      }
      const latency = Math.round(performance.now() - start);
      return { success: true, latencyMs: latency, message: `Gemini API Verified (${latency}ms)` };
    }

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

  // 1. Check local physics intent first (works instantly offline)
  const localConfig = parseLocalSimulationIntent(prompt);

  // If no API key is provided, use the built-in Autonomous Physics Agent
  if (!config.apiKey && config.provider !== 'ollama') {
    if (localConfig) {
      return {
        query: prompt,
        analysis: `⚡ **Autonomous CFD Agent Action**: Detected physics request for **${localConfig.summary}**.

${localConfig.physicsExplanation || ''}`,
        simConfig: localConfig
      };
    }
    return {
      query: prompt,
      analysis: '🤖 **OpenZess CFD Agent**: Describe what simulation you want to make (e.g. *"Simulate water past a NACA airfoil at 12 deg AoA"* or *"Test cylinder vortex shedding with CO2"*). You can also configure an LLM key via **[ 🔑 Set AI Key ]** for advanced reasoning.',
      suggestedSolver: 'icoFoam'
    };
  }

  // 2. Query LLM with full context
  const fullPrompt = `${SYSTEM_PROMPT}\n\n${context ? `Current Simulation Context:\n${context}\n\n` : ''}User Request: ${prompt}`;

  try {
    let rawText = '';

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
      rawText = data.candidates?.[0]?.content?.parts?.[0]?.text || '';
    } else {
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
      rawText = data.choices?.[0]?.message?.content || '';
    }

    // Try to extract JSON simulation action block from LLM response
    let extractedConfig = localConfig;
    const jsonMatch = rawText.match(/```(?:json)?\s*([\s\S]*?)\s*```/);
    if (jsonMatch) {
      try {
        const parsed = JSON.parse(jsonMatch[1]);
        if (parsed.action === 'CONFIG_SIMULATION' || parsed.archetype || parsed.substance) {
          extractedConfig = {
            archetype: parsed.archetype,
            substance: parsed.substance,
            reynoldsNumber: parsed.reynoldsNumber ? Number(parsed.reynoldsNumber) : undefined,
            angleDegrees: parsed.angleDegrees ? Number(parsed.angleDegrees) : undefined,
            autoRun: parsed.autoRun !== false,
            summary: parsed.summary || `${parsed.archetype || 'Custom'} Simulation`,
            physicsExplanation: parsed.physicsExplanation
          };
        }
      } catch (_) {}
    }

    const cleanAnalysis = rawText.replace(/```(?:json)?[\s\S]*?```/g, '').trim() || rawText;

    return {
      query: prompt,
      analysis: cleanAnalysis || `Autonomous CFD Agent configured: ${extractedConfig?.summary || 'Custom case'}`,
      simConfig: extractedConfig || undefined
    };
  } catch (err: any) {
    // Fallback to local intent parser on network error
    if (localConfig) {
      return {
        query: prompt,
        analysis: `⚡ **Autonomous CFD Agent Action (Offline)**: Configured **${localConfig.summary}**.

${localConfig.physicsExplanation || ''}`,
        simConfig: localConfig
      };
    }
    return {
      query: prompt,
      analysis: `⚠️ AI Copilot error (${config.provider}): ${err.message || 'Request failed'}. Verify your connection.`
    };
  }
}
