export type CaseType = 'cavity' | 'channel' | 'obstacle' | 'pipe';

export type SimulationArchetype = 'plume' | 'airfoil' | 'cylinder' | 'venturi' | 'cavity' | 'cad' | 'water_dam' | 'weather_plume';

export type SolverMode = 'cfd' | 'rust' | 'ai';

export type FieldVariable = 'U' | 'p' | 'T' | 'omega' | 'q_crit';

export type TurbulenceModel = 'laminar' | 'k-epsilon' | 'k-omega-sst' | 'spalart-allmaras';

export type VizMode = 'speed' | 'pressure' | 'streamlines' | 'vectors' | 'three3d';

export type ColormapScheme = 'inferno' | 'jet' | 'coolwarm' | 'viridis' | 'turbo' | 'pressure';

export type AiProviderType = 'gemini' | 'openai' | 'claude' | 'deepseek' | 'groq' | 'ollama';

export type FluidSubstanceId = 'air' | 'water' | 'co2' | 'oil' | 'ethanol';

export interface FluidProperties {
  id: FluidSubstanceId;
  name: string;
  density: number;             // rho [kg/m^3]
  kinematicViscosity: number;  // nu [m^2/s]
  specificHeat: number;        // Cp [J/(kg*K)]
  thermalExpansion: number;    // beta [1/K]
  surfaceTension?: number;     // sigma [N/m] (for multiphase/water)
}

export interface NaturalForces {
  gravity: [number, number, number]; // g vector [m/s^2], e.g. [0, -9.81, 0]
  ambientTemp: number;               // T0 [K], e.g. 293.15
  referencePressure: number;         // p0 [Pa], e.g. 101325
}

export interface AiProviderConfig {
  provider: AiProviderType;
  apiKey: string;
  model: string;
  customBaseUrl?: string;
}

export interface AerodynamicTelemetry {
  cd: number;           // Drag Coefficient
  cl: number;           // Lift Coefficient
  l_d: number;          // Lift-to-Drag Ratio
  courantMax: number;   // Maximum Courant number Co = |U| dt / dx
  courantMean: number;  // Mean Courant number
  continuityError: number;
}

export interface StudioParameters {
  irisPurple: number;        // Inlet velocity / iris magnitude (default: 0.182)
  vorticityAngle: number;    // Swirl angle / vorticity angle / AoA (default: 0.152)
  vorticityCore: number;     // Core vortex intensity / Re scale (default: 30)
  butterscotchCore: number;  // Thermal core temperature / intensity (default: 84.899)
}

export interface SimulationParams {
  archetype: SimulationArchetype;
  activeField: FieldVariable;
  substance: FluidSubstanceId;
  naturalForces: NaturalForces;
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
  uMax?: number;
  uAvg?: number;
  pMin?: number;
  pMax?: number;
  cd?: number;
  cl?: number;
  courantMax?: number;
  continuityError?: number;
  obstacleMask?: boolean[][];
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


