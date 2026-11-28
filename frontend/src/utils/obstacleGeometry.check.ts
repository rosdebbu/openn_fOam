/**
 * Self-check for the obstacleSpec -> WASM primitive adapter.
 * Run from frontend/:
 *   npx tsc --ignoreConfig --outDir <tmp> --target es2022 --module commonjs --skipLibCheck \
 *     --strict src/utils/obstacleGeometry.check.ts && node <tmp>/obstacleGeometry.check.js
 */

import { primitivesFromObstacleSpec, GEOMETRY_SHAPES } from './obstacleGeometry';

let failures = 0;
function check(name: string, ok: boolean) {
  if (!ok) { failures++; console.error(`FAIL ${name}`); } else { console.log(`ok   ${name}`); }
}

const centre = primitivesFromObstacleSpec({ shape: 'circle', cx: 0.5, cy: 0.5, size: 0.15, aoa: 0 })[0];
check('centre of domain maps to (0,0)', centre.x === 0 && centre.y === 0);
check('circle becomes a cylinder', centre.kind === 'cylinder');
check('size 0.15 -> 0.30 full width', Math.abs(centre.w - 0.3) < 1e-9);

const inlet = primitivesFromObstacleSpec({ shape: 'square', cx: 0.15, cy: 0.85, size: 0.1, aoa: 0 })[0];
check('cx 0.15 -> x -0.7', Math.abs(inlet.x + 0.7) < 1e-9);
check('cy 0.85 -> y +0.7', Math.abs(inlet.y - 0.7) < 1e-9);

// Every primitive must land inside the engine's paintable domain (-1..1), edges included.
for (const s of GEOMETRY_SHAPES) {
  for (const cx of [0.15, 0.5, 0.85]) {
    for (const cy of [0.15, 0.5, 0.85]) {
      const prims = primitivesFromObstacleSpec({ shape: s.id, cx, cy, size: 0.35, aoa: 20 });
      check(
        `${s.id} @ ${cx}/${cy} stays in -1..1`,
        prims.length > 0 && prims.every(
          (p) => Math.abs(p.x) <= 1 && Math.abs(p.y) <= 1 && p.w > 0 && p.h > 0
        )
      );
    }
  }
}

const flat = primitivesFromObstacleSpec({ shape: 'airfoil', cx: 0.4, cy: 0.5, size: 0.15, aoa: 0 })[0];
const steep = primitivesFromObstacleSpec({ shape: 'airfoil', cx: 0.4, cy: 0.5, size: 0.15, aoa: 20 })[0];
check('airfoil thickens with angle of attack', steep.h > flat.h);

check('house is body + roof', primitivesFromObstacleSpec({ shape: 'house', cx: 0.4, cy: 0.4, size: 0.15, aoa: 0 }).length === 2);
check('unknown shape falls back to a cylinder', primitivesFromObstacleSpec({ shape: 'banana', cx: 0.4, cy: 0.5, size: 0.15, aoa: 0 })[0].kind === 'cylinder');

console.log(failures === 0 ? '\nALL CHECKS PASSED' : `\n${failures} CHECK(S) FAILED`);
