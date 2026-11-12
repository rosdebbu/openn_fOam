/**
 * OpenZess In-Browser CFD Simulation Worker
 * 
 * Implements a high-performance 2D/3D incompressible Navier-Stokes solver
 * running in a background Web Worker thread using typed Float32Arrays.
 * Enables zero-server, client-side simulation directly in modern browsers.
 */

export interface SimulationParams {
  nx: number;
  ny: number;
  reynolds: number;
  cfl: number;
  maxIter: number;
  scenario: 'cavity' | 'obstacle' | 'channel';
  obstacleType?: 'cylinder' | 'airfoil' | 'square';
}

class InBrowserCfdEngine {
  nx: number;
  ny: number;
  dx: number;
  dy: number;
  dt: number;
  nu: number;
  rho: number;
  reynolds: number;
  scenario: string;

  u: Float32Array;
  v: Float32Array;
  uPrev: Float32Array;
  vPrev: Float32Array;
  p: Float32Array;
  pPrev: Float32Array;
  div: Float32Array;
  vorticity: Float32Array;
  speed: Float32Array;
  mask: Uint8Array; // 1 = solid obstacle, 0 = fluid

  iteration: number = 0;
  lastResidual: number = 1.0;

  constructor(params: SimulationParams) {
    this.nx = params.nx;
    this.ny = params.ny;
    const size = this.nx * this.ny;

    this.dx = 1.0 / (this.nx - 1);
    this.dy = 1.0 / (this.ny - 1);
    this.reynolds = Math.max(1.0, params.reynolds);
    this.nu = 1.0 / this.reynolds;
    this.rho = 1.0;
    this.dt = (params.cfl * Math.min(this.dx, this.dy)) / 1.0;
    this.scenario = params.scenario;

    this.u = new Float32Array(size);
    this.v = new Float32Array(size);
    this.uPrev = new Float32Array(size);
    this.vPrev = new Float32Array(size);
    this.p = new Float32Array(size);
    this.pPrev = new Float32Array(size);
    this.div = new Float32Array(size);
    this.vorticity = new Float32Array(size);
    this.speed = new Float32Array(size);
    this.mask = new Uint8Array(size);

    this.initBoundary();
  }

  idx(i: number, j: number): number {
    return j * this.nx + i;
  }

  initBoundary(): void {
    if (this.scenario === 'cavity') {
      const topJ = this.ny - 1;
      for (let i = 0; i < this.nx; i++) {
        this.u[this.idx(i, topJ)] = 1.0; // Moving Lid
      }
    } else {
      // Tunnel with center obstacle
      const cx = Math.floor(this.nx / 3);
      const cy = Math.floor(this.ny / 2);
      const r = Math.max(2, Math.floor(this.ny / 6));

      for (let j = 0; j < this.ny; j++) {
        for (let i = 0; i < this.nx; i++) {
          const id = this.idx(i, j);
          const di = i - cx;
          const dj = j - cy;
          if (di * di + dj * dj <= r * r) {
            this.mask[id] = 1;
          } else {
            this.u[id] = 0.5;
          }
        }
      }
    }
  }

  step(numSteps: number = 1): number {
    for (let s = 0; s < numSteps; s++) {
      this.solveStep();
    }
    this.computeDerived();
    return this.lastResidual;
  }

  private solveStep(): void {
    const { nx, ny, dx, dy, dt, nu, rho } = this;

    this.uPrev.set(this.u);
    this.vPrev.set(this.v);

    // 1. Advection & Diffusion (Tentative Velocities)
    for (let j = 1; j < ny - 1; j++) {
      for (let i = 1; i < nx - 1; i++) {
        const id = j * nx + i;
        if (this.mask[id] === 1) {
          this.u[id] = 0;
          this.v[id] = 0;
          continue;
        }

        const uCurr = this.uPrev[id];
        const vCurr = this.vPrev[id];

        // Upwind Advection
        const uAdvX = uCurr > 0
          ? uCurr * (uCurr - this.uPrev[id - 1]) / dx
          : uCurr * (this.uPrev[id + 1] - uCurr) / dx;

        const uAdvY = vCurr > 0
          ? vCurr * (uCurr - this.uPrev[id - nx]) / dy
          : vCurr * (this.uPrev[id + nx] - uCurr) / dy;

        const vAdvX = uCurr > 0
          ? uCurr * (vCurr - this.vPrev[id - 1]) / dx
          : uCurr * (this.vPrev[id + 1] - vCurr) / dx;

        const vAdvY = vCurr > 0
          ? vCurr * (vCurr - this.vPrev[id - nx]) / dy
          : vCurr * (this.vPrev[id + nx] - vCurr) / dy;

        // Diffusion
        const uDiff = nu * (
          (this.uPrev[id + 1] - 2 * uCurr + this.uPrev[id - 1]) / (dx * dx) +
          (this.uPrev[id + nx] - 2 * uCurr + this.uPrev[id - nx]) / (dy * dy)
        );

        const vDiff = nu * (
          (this.vPrev[id + 1] - 2 * vCurr + this.vPrev[id - 1]) / (dx * dx) +
          (this.vPrev[id + nx] - 2 * vCurr + this.vPrev[id - nx]) / (dy * dy)
        );

        this.u[id] = uCurr + dt * (-uAdvX - uAdvY + uDiff);
        this.v[id] = vCurr + dt * (-vAdvX - vAdvY + vDiff);
      }
    }

    // 2. Divergence
    const rhoDt = rho / dt;
    for (let j = 1; j < ny - 1; j++) {
      for (let i = 1; i < nx - 1; i++) {
        const id = j * nx + i;
        if (this.mask[id] === 1) {
          this.div[id] = 0;
        } else {
          const duDx = (this.u[id + 1] - this.u[id - 1]) / (2 * dx);
          const dvDy = (this.v[id + nx] - this.v[id - nx]) / (2 * dy);
          this.div[id] = rhoDt * (duDx + dvDy);
        }
      }
    }

    // 3. Pressure-Poisson (SOR Solver)
    const idx2 = 1.0 / (dx * dx);
    const idy2 = 1.0 / (dy * dy);
    const denom = 2.0 * (idx2 + idy2);
    const omega = 1.25;

    let maxPDiff = 0.0;
    for (let it = 0; it < 20; it++) {
      maxPDiff = 0.0;
      for (let j = 1; j < ny - 1; j++) {
        for (let i = 1; i < nx - 1; i++) {
          const id = j * nx + i;
          if (this.mask[id] === 1) continue;

          const pOld = this.p[id];
          const rhs = (this.p[id + 1] + this.p[id - 1]) * idx2 +
                      (this.p[id + nx] + this.p[id - nx]) * idy2 -
                      this.div[id];
          const pNew = (1.0 - omega) * pOld + (omega * rhs / denom);
          this.p[id] = pNew;

          const diff = Math.abs(pNew - pOld);
          if (diff > maxPDiff) maxPDiff = diff;
        }
      }

      // Pressure BCs (Neumann)
      for (let i = 0; i < nx; i++) {
        this.p[this.idx(i, 0)] = this.p[this.idx(i, 1)];
        this.p[this.idx(i, ny - 1)] = this.p[this.idx(i, ny - 2)];
      }
      for (let j = 0; j < ny; j++) {
        this.p[this.idx(0, j)] = this.p[this.idx(1, j)];
        this.p[this.idx(nx - 1, j)] = this.p[this.idx(nx - 2, j)];
      }
    }
    this.lastResidual = maxPDiff;

    // 4. Velocity Correction
    const dtRho = dt / rho;
    for (let j = 1; j < ny - 1; j++) {
      for (let i = 1; i < nx - 1; i++) {
        const id = j * nx + i;
        if (this.mask[id] === 1) {
          this.u[id] = 0;
          this.v[id] = 0;
          continue;
        }

        const dpDx = (this.p[id + 1] - this.p[id - 1]) / (2 * dx);
        const dpDy = (this.p[id + nx] - this.p[id - nx]) / (2 * dy);

        this.u[id] -= dtRho * dpDx;
        this.v[id] -= dtRho * dpDy;
      }
    }

    // 5. Boundary Enforcement
    if (this.scenario === 'cavity') {
      const topJ = ny - 1;
      for (let i = 0; i < nx; i++) {
        this.u[this.idx(i, 0)] = 0;
        this.v[this.idx(i, 0)] = 0;
        this.u[this.idx(i, topJ)] = 1.0;
        this.v[this.idx(i, topJ)] = 0;
      }
      for (let j = 0; j < ny; j++) {
        this.u[this.idx(0, j)] = 0;
        this.v[this.idx(0, j)] = 0;
        this.u[this.idx(nx - 1, j)] = 0;
        this.v[this.idx(nx - 1, j)] = 0;
      }
    } else {
      for (let j = 0; j < ny; j++) {
        this.u[this.idx(0, j)] = 1.0;
        this.v[this.idx(0, j)] = 0;
        this.u[this.idx(nx - 1, j)] = this.u[this.idx(nx - 2, j)];
        this.v[this.idx(nx - 1, j)] = this.v[this.idx(nx - 2, j)];
      }
    }

    this.iteration++;
  }

  private computeDerived(): void {
    const { nx, ny, dx, dy } = this;
    for (let j = 1; j < ny - 1; j++) {
      for (let i = 1; i < nx - 1; i++) {
        const id = j * nx + i;
        const uVal = this.u[id];
        const vVal = this.v[id];
        this.speed[id] = Math.sqrt(uVal * uVal + vVal * vVal);

        const dvDx = (this.v[id + 1] - this.v[id - 1]) / (2 * dx);
        const duDy = (this.u[id + nx] - this.u[id - nx]) / (2 * dy);
        this.vorticity[id] = dvDx - duDy;
      }
    }
  }
}

let engine: InBrowserCfdEngine | null = null;

self.onmessage = (e: MessageEvent) => {
  const { type, payload } = e.data;

  if (type === 'INIT') {
    engine = new InBrowserCfdEngine(payload);
    self.postMessage({ type: 'READY', payload: { nx: engine.nx, ny: engine.ny } });
  } else if (type === 'STEP' && engine) {
    const steps = payload?.steps || 2;
    const residual = engine.step(steps);

    self.postMessage({
      type: 'FRAME',
      payload: {
        iteration: engine.iteration,
        residual,
        u: engine.u,
        v: engine.v,
        p: engine.p,
        speed: engine.speed,
        vorticity: engine.vorticity,
        mask: engine.mask
      }
    });
  } else if (type === 'SET_REYNOLDS' && engine) {
    engine.reynolds = payload.reynolds;
    engine.nu = 1.0 / engine.reynolds;
  }
};

