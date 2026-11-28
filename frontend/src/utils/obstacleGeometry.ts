/**
 * Obstacle spec -> WASM primitive adapter.
 *
 * The Custom Geometry Builder speaks the backend's `obstacleSpec` language
 * (shape name, cx/cy/size as 0..1 fractions of the domain, aoa in degrees).
 * fvm_solver.wasm speaks CustomPrimitive (kind, x/y in -1..1, w/h as full
 * extents in domain units). This translates the former into the latter so the
 * builder can run entirely in the browser, with no backend.
 */

import type { CustomPrimitive } from './openfoamWasmBridge';

export interface ObstacleSpec {
  shape: string;
  cx: number; // 0..1 across the domain (inlet -> outlet)
  cy: number; // 0..1 across the domain (bottom -> top)
  size: number; // 0..1 characteristic length
  aoa: number; // degrees, airfoil only
}

export const GEOMETRY_SHAPES = [
  { id: 'circle', name: 'Cylinder', icon: '⚪' },
  { id: 'square', name: 'Square', icon: '⬛' },
  { id: 'rectangle', name: 'Plate', icon: '▬' },
  { id: 'airfoil', name: 'Airfoil', icon: '✈️' },
  { id: 'house', name: 'House', icon: '🏠' },
  { id: 'tower', name: 'Tower', icon: '🏢' }
] as const;

const BODY = '#5c89a6';
const ROOF = '#c85a44';

export function primitivesFromObstacleSpec(spec: ObstacleSpec): CustomPrimitive[] {
  // The engine clips anything outside -1..1, so keep stacked parts (a roof at the
  // top of the domain) on the domain edge instead of letting them vanish.
  return build(spec).map((p) => ({ ...p, x: clamp(p.x), y: clamp(p.y) }));
}

const clamp = (v: number) => Math.max(-1, Math.min(1, v));

function build(spec: ObstacleSpec): CustomPrimitive[] {
  // 0..1 fraction -> -1..1 domain; `size` is a fraction of the 2-unit-wide domain.
  const x = spec.cx * 2 - 1;
  const y = spec.cy * 2 - 1;
  const s = Math.max(0.02, Math.min(0.7, spec.size)) * 2;

  switch (spec.shape) {
    case 'circle':
      return [{ kind: 'cylinder', x, y, w: s, h: s, d: s, color: BODY }];
    case 'square':
      return [{ kind: 'box', x, y, w: s, h: s, d: s, color: BODY }];
    case 'rectangle':
      return [{ kind: 'box', x, y, w: s * 1.8, h: s * 0.3, d: s * 0.3, color: BODY }];
    case 'airfoil': {
      // shortcut: primitives carry no rotation, so angle of attack becomes
      // projected thickness. Replace with a rotated mask if lift/drag vs aoa matters.
      const chord = s * 2;
      const t = Math.max(0.12, Math.abs(Math.sin((spec.aoa * Math.PI) / 180)));
      return [{ kind: 'capsule', x, y, w: chord, h: chord * t, d: s * 0.4, color: BODY }];
    }
    case 'house':
      return [
        { kind: 'box', x, y, w: s * 1.6, h: s, d: s, color: BODY },
        { kind: 'box', x, y: y + s * 0.75, w: s * 1.0, h: s * 0.5, d: s * 0.5, color: ROOF }
      ];
    case 'tower':
      return [{ kind: 'box', x, y, w: s * 0.7, h: s * 2.4, d: s * 2.4, color: BODY }];
    default:
      return [{ kind: 'cylinder', x, y, w: s, h: s, d: s, color: BODY }];
  }
}
