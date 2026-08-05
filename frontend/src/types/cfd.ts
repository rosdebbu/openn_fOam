export type CaseType = 'cavity' | 'channel' | 'obstacle' | 'pipe';

export type SolverMode = 'cfd' | 'ai';

export type TurbulenceModel = 'laminar' | 'k-epsilon' | 'k-omega-sst';

export type VizMode = 'speed' | 'pressure' | 'streamlines' | 'vectors' | 'three3d';

export type ColormapScheme = 'inferno' | 'jet' | 'coolwarm' | 'viridis' | 'pressure';

export interface SimulationParams {
  caseType: CaseType;
  solverMode: SolverMode;
  turbulenceModel: TurbulenceModel;
  reynoldsNumber: number;
  gridResolution: number;
  maxIterations: number;
  dt: number;
  tolerance: number;
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
  content: string;
  language: string;
}

export interface AiResponse {
  query: string;
  analysis: string;
  reynolds: number;
  vortexLocation?: string;
  boundaryLayer?: string;
}
