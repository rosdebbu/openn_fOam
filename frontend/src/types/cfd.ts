export type CaseType = 'cavity' | 'channel' | 'obstacle' | 'pipe';

export type SimulationArchetype = 'plume' | 'airfoil' | 'cylinder' | 'venturi' | 'cavity' | 'cad';

export type SolverMode = 'cfd' | 'ai';

export type TurbulenceModel = 'laminar' | 'k-epsilon' | 'k-omega-sst';

export type VizMode = 'speed' | 'pressure' | 'streamlines' | 'vectors' | 'three3d';

export type ColormapScheme = 'inferno' | 'jet' | 'coolwarm' | 'viridis' | 'pressure';

export type AiProviderType = 'gemini' | 'openai' | 'claude' | 'deepseek' | 'groq' | 'ollama';

export interface AiProviderConfig {
  provider: AiProviderType;
  apiKey: string;
  model: string;
  customBaseUrl?: string;
}

export interface StudioParameters {
  irisPurple: number;        // Inlet velocity / iris magnitude (default: 0.182)
  vorticityAngle: number;    // Swirl angle / vorticity angle / AoA (default: 0.152)
  vorticityCore: number;     // Core vortex intensity / Re scale (default: 30)
  butterscotchCore: number;  // Thermal core temperature / intensity (default: 84.899)
}

export interface SimulationParams {
  archetype: SimulationArchetype;
  caseType: CaseType;
  solverMode: SolverMode;
  turbulenceModel: TurbulenceModel;
  reynoldsNumber: number;
  gridResolution: number;
  maxIterations: number;
  dt: number;
  tolerance: number;
  studioParams: StudioParameters;
}

export interface ProbeData {
  x: number;
  y: number;
  z: number;
  value: number;
  u: number;
  v: number;
  w: number;
  p: number;
  t: number;
}

export interface SimulationStepData {
  iteration: number;
  residual: number;
  converged: boolean;
  u: number[][];
  v: number[][];
  p: number[][];
  speed: number[][];
  mode: SolverMode;
  error?: string;
}

export interface OpenFoamDictFile {
  name: string;
  path: string;
  category?: 'system' | 'constant' | '0' | string;
  content: string;
  language?: string;
  description?: string;
}

export interface AiResponse {
  query: string;
  analysis: string;
  reynolds?: number;
  suggestedSolver?: string;
  openfoamDictSnippet?: string;
  vortexLocation?: string;
  boundaryLayer?: string;
}


