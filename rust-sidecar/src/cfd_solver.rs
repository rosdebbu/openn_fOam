//! 2-D incompressible Navier-Stokes kernel for OpenZess Studio.
//!
//! Scheme (Barba, "12 steps to Navier-Stokes", steps 11-12): build the
//! pressure-Poisson source from the current velocity, relax it with Jacobi
//! sweeps (warm-started from the previous step), then advance momentum
//! explicitly with first-order upwind advection and central diffusion.
//!
//! The grid (cell-centred, `dx = lx / nx`), the viscosity and the solid mask
//! are supplied by the Python side, so both engines solve the same problem.
//! Force coefficients are integrated on the Python side from the returned
//! fields; this kernel does not invent them.
//!
//! The Jacobi sweeps and the momentum update are parallelised over grid rows
//! with Rayon once the grid is large enough for threading to pay off
//! (`PARALLEL_MIN_CELLS`). Jacobi updates are order-independent, so the
//! parallel and sequential paths produce bit-identical results.

use rayon::prelude::*;
use serde::{Deserialize, Serialize};
use std::time::Instant;

/// Largest accepted grid side (memory/latency guard for a local service).
pub const MAX_CELLS_PER_SIDE: usize = 512;
/// Largest accepted number of time steps per request.
pub const MAX_STEPS: usize = 20_000;
/// Jacobi sweeps per time step for the pressure Poisson equation.
const JACOBI_SWEEPS: usize = 40;
/// Below this many cells a sweep takes about as long as handing work to the
/// thread pool, so small grids run sequentially.
const PARALLEL_MIN_CELLS: usize = 16_384;
/// Residual (max |du| per step) below which the run counts as converged.
const CONVERGENCE_TOL: f64 = 1e-5;

#[derive(Debug, Clone, Deserialize)]
pub struct CfdConfig {
    #[serde(default = "default_n")]
    pub nx: usize,
    #[serde(default = "default_n")]
    pub ny: usize,
    #[serde(default = "default_len")]
    pub lx: f64,
    #[serde(default = "default_len")]
    pub ly: f64,
    /// Kinematic viscosity. If absent it is derived as `lid_u * ly / re`.
    #[serde(default)]
    pub nu: Option<f64>,
    #[serde(default = "default_re")]
    pub re: f64,
    /// Upper bound on the time step; the solver also enforces CFL and
    /// diffusion limits.
    #[serde(default = "default_dt")]
    pub dt: f64,
    #[serde(default = "default_steps")]
    pub steps: usize,
    #[serde(default = "default_lid_u")]
    pub lid_u: f64,
    /// "cavity" / "water_dam" are sealed boxes; anything else is an
    /// inlet (left) -> outlet (right) channel with freestream top/bottom.
    #[serde(default = "default_archetype")]
    pub archetype: String,
    /// Solid cells indexed `[i][j]`, shape `nx x ny`.
    #[serde(default)]
    pub obstacle_mask: Option<Vec<Vec<bool>>>,
}

fn default_n() -> usize { 41 }
fn default_len() -> f64 { 1.0 }
fn default_re() -> f64 { 100.0 }
fn default_dt() -> f64 { 0.005 }
fn default_steps() -> usize { 150 }
fn default_lid_u() -> f64 { 1.0 }
fn default_archetype() -> String { "cavity".to_string() }

#[derive(Debug, Clone, Serialize)]
pub struct CfdStepResult {
    /// Time steps actually taken (stops early on convergence/divergence).
    pub iteration: usize,
    pub residual: f64,
    pub converged: bool,
    pub diverged: bool,
    pub cfl: f64,
    pub dt_used: f64,
    pub elapsed_ms: f64,
    pub parallel: bool,
    pub threads: usize,
    pub u: Vec<Vec<f64>>,
    pub v: Vec<Vec<f64>>,
    pub p: Vec<Vec<f64>>,
    pub speed: Vec<Vec<f64>>,
    pub vorticity: Vec<Vec<f64>>,
}

#[derive(Debug, Clone, Serialize)]
pub struct CfdBenchmarkResult {
    pub grid_points: usize,
    pub steps_computed: usize,
    pub total_time_ms: f64,
    pub steps_per_second: f64,
    pub million_cells_per_sec: f64,
    pub final_residual: f64,
    pub max_cfl: f64,
    pub parallel: bool,
    pub threads: usize,
}

pub struct NavierStokesSolver {
    pub nx: usize,
    pub ny: usize,
    pub dx: f64,
    pub dy: f64,
    pub nu: f64,
    pub dt_max: f64,
    pub lid_u: f64,
    pub archetype: String,
    pub closed: bool,
    /// Run row loops on the Rayon pool (set from the grid size).
    pub parallel: bool,
    pub u: Vec<Vec<f64>>,
    pub v: Vec<Vec<f64>>,
    pub p: Vec<Vec<f64>>,
    pub b: Vec<Vec<f64>>,
    pub obstacle_mask: Vec<Vec<bool>>,
    pub last_dt: f64,
    pub diverged: bool,
}

/// Run `f(row_index_within_slice, row)` over `rows`, on the Rayon pool when
/// `parallel` is set. Each closure call only writes its own row.
fn for_each_row<F>(rows: &mut [Vec<f64>], parallel: bool, f: F)
where
    F: Fn(usize, &mut Vec<f64>) + Sync + Send,
{
    if parallel {
        rows.par_iter_mut().enumerate().for_each(|(k, row)| f(k, row));
    } else {
        rows.iter_mut().enumerate().for_each(|(k, row)| f(k, row));
    }
}

fn finite_or(x: f64, fallback: f64) -> f64 {
    if x.is_finite() { x } else { fallback }
}

impl NavierStokesSolver {
    pub fn new(config: &CfdConfig) -> Result<Self, String> {
        let nx = config.nx.clamp(8, MAX_CELLS_PER_SIDE);
        let ny = config.ny.clamp(8, MAX_CELLS_PER_SIDE);
        let lx = if config.lx.is_finite() && config.lx > 0.0 { config.lx } else { 1.0 };
        let ly = if config.ly.is_finite() && config.ly > 0.0 { config.ly } else { 1.0 };
        let lid_u = finite_or(config.lid_u, 1.0);
        let nu = config
            .nu
            .filter(|n| n.is_finite() && *n > 0.0)
            .unwrap_or_else(|| lid_u.abs().max(1e-3) * ly / config.re.max(1e-6))
            .max(1e-9);
        let dt_max = if config.dt.is_finite() && config.dt > 0.0 { config.dt } else { 0.005 };

        let obstacle_mask = match &config.obstacle_mask {
            None => vec![vec![false; ny]; nx],
            Some(m) if m.len() == nx && m.iter().all(|row| row.len() == ny) => m.clone(),
            Some(m) => {
                return Err(format!(
                    "obstacle_mask shape {}x{} does not match grid {}x{}",
                    m.len(),
                    m.first().map_or(0, |r| r.len()),
                    nx,
                    ny
                ))
            }
        };

        let archetype = config.archetype.to_lowercase();
        let closed = archetype == "cavity" || archetype == "water_dam";

        let mut solver = Self {
            nx,
            ny,
            dx: lx / nx as f64,
            dy: ly / ny as f64,
            nu,
            dt_max,
            lid_u,
            archetype,
            closed,
            parallel: nx * ny >= PARALLEL_MIN_CELLS,
            u: vec![vec![0.0; ny]; nx],
            v: vec![vec![0.0; ny]; nx],
            p: vec![vec![0.0; ny]; nx],
            b: vec![vec![0.0; ny]; nx],
            obstacle_mask,
            last_dt: 0.0,
            diverged: false,
        };
        let (mut u, mut v) = (std::mem::take(&mut solver.u), std::mem::take(&mut solver.v));
        solver.apply_velocity_bc(&mut u, &mut v);
        solver.u = u;
        solver.v = v;
        Ok(solver)
    }

    /// Same boundary conditions as the Python `AcceleratedSolver`.
    fn apply_velocity_bc(&self, u: &mut [Vec<f64>], v: &mut [Vec<f64>]) {
        let (nx, ny, lid) = (self.nx, self.ny, self.lid_u);
        if self.closed {
            for i in 0..nx {
                u[i][0] = 0.0;
                v[i][0] = 0.0;
                // Moving lid for the cavity, plain wall for the dam tank
                u[i][ny - 1] = if self.archetype == "cavity" { lid } else { 0.0 };
                v[i][ny - 1] = 0.0;
            }
            for j in 0..ny {
                u[0][j] = 0.0;
                v[0][j] = 0.0;
                u[nx - 1][j] = 0.0;
                v[nx - 1][j] = 0.0;
            }
            if self.archetype == "cavity" {
                // Lid row wins at the top corners (matches the Python solver)
                u[0][ny - 1] = lid;
                u[nx - 1][ny - 1] = lid;
            }
        } else {
            for j in 0..ny {
                u[0][j] = lid; // inlet
                v[0][j] = 0.0;
                u[nx - 1][j] = u[nx - 2][j]; // zero-gradient outlet
                v[nx - 1][j] = v[nx - 2][j];
            }
            for i in 0..nx {
                u[i][0] = lid; // freestream floor / lid
                v[i][0] = 0.0;
                u[i][ny - 1] = lid;
                v[i][ny - 1] = 0.0;
            }
        }
        for i in 0..nx {
            for j in 0..ny {
                if self.obstacle_mask[i][j] {
                    u[i][j] = 0.0;
                    v[i][j] = 0.0;
                }
            }
        }
    }

    /// CFL- and diffusion-limited time step for the explicit march.
    fn stable_dt(&self) -> f64 {
        let u_max = self
            .u
            .iter()
            .chain(self.v.iter())
            .flat_map(|row| row.iter())
            .fold(self.lid_u.abs(), |m, x| m.max(x.abs()))
            .max(1e-6);
        let h = self.dx.min(self.dy);
        let cfl_dt = 0.4 * h / u_max;
        let diff_dt = 0.2 * h * h / self.nu;
        self.dt_max.min(cfl_dt).min(diff_dt).max(1e-7)
    }

    /// Pressure-Poisson source term from the current velocity field.
    fn build_rhs(&mut self, dt: f64) {
        let (nx, ny, dx, dy) = (self.nx, self.ny, self.dx, self.dy);
        let (u, v) = (&self.u, &self.v);
        for_each_row(&mut self.b[1..nx - 1], self.parallel, |k, row| {
            let i = k + 1;
            for j in 1..ny - 1 {
                let du_dx = (u[i + 1][j] - u[i - 1][j]) / (2.0 * dx);
                let dv_dy = (v[i][j + 1] - v[i][j - 1]) / (2.0 * dy);
                let du_dy = (u[i][j + 1] - u[i][j - 1]) / (2.0 * dy);
                let dv_dx = (v[i + 1][j] - v[i - 1][j]) / (2.0 * dx);
                row[j] = (du_dx + dv_dy) / dt
                    - (du_dx * du_dx + 2.0 * du_dy * dv_dx + dv_dy * dv_dy);
            }
        });
        if self.closed {
            // Pure-Neumann box: make the source compatible (mean zero)
            let n = ((nx - 2) * (ny - 2)) as f64;
            let mean = self.b[1..nx - 1]
                .iter()
                .map(|row| row[1..ny - 1].iter().sum::<f64>())
                .sum::<f64>()
                / n;
            for row in &mut self.b[1..nx - 1] {
                for x in &mut row[1..ny - 1] {
                    *x -= mean;
                }
            }
        }
    }

    /// Jacobi relaxation of the pressure Poisson equation.
    fn solve_pressure(&mut self) {
        let (nx, ny) = (self.nx, self.ny);
        let dx2 = self.dx * self.dx;
        let dy2 = self.dy * self.dy;
        let factor = 2.0 * (dx2 + dy2);

        // Two buffers swapped every sweep: each sweep overwrites every entry
        // of `pn` (interior by the stencil, edges by the BCs), so no per-sweep
        // allocation or copy is needed.
        let mut pn = self.p.clone();
        for _ in 0..JACOBI_SWEEPS {
            {
                let (p, b) = (&self.p, &self.b);
                for_each_row(&mut pn[1..nx - 1], self.parallel, |k, row| {
                    let i = k + 1;
                    for j in 1..ny - 1 {
                        row[j] = ((p[i + 1][j] + p[i - 1][j]) * dy2
                            + (p[i][j + 1] + p[i][j - 1]) * dx2
                            - b[i][j] * dx2 * dy2)
                            / factor;
                    }
                });
            }

            // dp/dx = 0 on the inlet / left wall
            for j in 0..ny {
                pn[0][j] = pn[1][j];
            }
            // Right: wall (dp/dx = 0) for sealed boxes, p = 0 outlet otherwise
            for j in 0..ny {
                pn[nx - 1][j] = if self.closed { pn[nx - 2][j] } else { 0.0 };
            }
            // dp/dy = 0 on floor and lid
            for i in 0..nx {
                pn[i][0] = pn[i][1];
                pn[i][ny - 1] = pn[i][ny - 2];
            }
            if self.closed {
                // Gauge: pressure is only defined up to a constant
                let mean = pn.iter().flatten().sum::<f64>() / (nx * ny) as f64;
                pn.iter_mut().flatten().for_each(|x| *x -= mean);
            }
            std::mem::swap(&mut self.p, &mut pn);
        }
    }

    /// Advance one time step; returns the residual max(|du|, |dv|).
    pub fn step(&mut self) -> f64 {
        let dt = self.stable_dt();
        self.last_dt = dt;
        self.build_rhs(dt);
        self.solve_pressure();

        let (nx, ny, dx, dy, nu) = (self.nx, self.ny, self.dx, self.dy, self.nu);
        let mut un = self.u.clone();
        let mut vn = self.v.clone();
        {
            let (u, v, p) = (&self.u, &self.v, &self.p);
            let update = |i: usize, u_row: &mut Vec<f64>, v_row: &mut Vec<f64>| {
                for j in 1..ny - 1 {
                    let (uij, vij) = (u[i][j], v[i][j]);
                    // First-order upwind advection (direction-aware)
                    let (du_dx, dv_dx) = if uij > 0.0 {
                        ((uij - u[i - 1][j]) / dx, (vij - v[i - 1][j]) / dx)
                    } else {
                        ((u[i + 1][j] - uij) / dx, (v[i + 1][j] - vij) / dx)
                    };
                    let (du_dy, dv_dy) = if vij > 0.0 {
                        ((uij - u[i][j - 1]) / dy, (vij - v[i][j - 1]) / dy)
                    } else {
                        ((u[i][j + 1] - uij) / dy, (v[i][j + 1] - vij) / dy)
                    };
                    let dp_dx = (p[i + 1][j] - p[i - 1][j]) / (2.0 * dx);
                    let dp_dy = (p[i][j + 1] - p[i][j - 1]) / (2.0 * dy);
                    let lap_u = (u[i + 1][j] - 2.0 * uij + u[i - 1][j]) / (dx * dx)
                        + (u[i][j + 1] - 2.0 * uij + u[i][j - 1]) / (dy * dy);
                    let lap_v = (v[i + 1][j] - 2.0 * vij + v[i - 1][j]) / (dx * dx)
                        + (v[i][j + 1] - 2.0 * vij + v[i][j - 1]) / (dy * dy);
                    u_row[j] = uij + dt * (-uij * du_dx - vij * du_dy - dp_dx + nu * lap_u);
                    v_row[j] = vij + dt * (-uij * dv_dx - vij * dv_dy - dp_dy + nu * lap_v);
                }
            };
            let (u_rows, v_rows) = (&mut un[1..nx - 1], &mut vn[1..nx - 1]);
            if self.parallel {
                u_rows
                    .par_iter_mut()
                    .zip(v_rows.par_iter_mut())
                    .enumerate()
                    .for_each(|(k, (ur, vr))| update(k + 1, ur, vr));
            } else {
                u_rows
                    .iter_mut()
                    .zip(v_rows.iter_mut())
                    .enumerate()
                    .for_each(|(k, (ur, vr))| update(k + 1, ur, vr));
            }
        }
        self.apply_velocity_bc(&mut un, &mut vn);

        // Divergence guard: a healthy run stays far below 10x the lid speed
        let cap = 10.0 * self.lid_u.abs().max(1.0);
        let mut max_res = 0.0f64;
        for i in 0..nx {
            for j in 0..ny {
                let (a, b) = (un[i][j], vn[i][j]);
                if !a.is_finite() || !b.is_finite() || a.abs() > cap || b.abs() > cap {
                    self.diverged = true;
                }
                max_res = max_res
                    .max((a - self.u[i][j]).abs())
                    .max((b - self.v[i][j]).abs());
            }
        }
        self.u = un;
        self.v = vn;
        max_res
    }

    /// Maximum cell Courant number |u| dt/dx + |v| dt/dy for the last step.
    pub fn compute_cfl(&self) -> f64 {
        let mut max_cfl = 0.0f64;
        for i in 0..self.nx {
            for j in 0..self.ny {
                let c = self.u[i][j].abs() * self.last_dt / self.dx
                    + self.v[i][j].abs() * self.last_dt / self.dy;
                max_cfl = max_cfl.max(c);
            }
        }
        max_cfl
    }

    /// Vorticity omega = dv/dx - du/dy (central differences, zero on edges).
    pub fn compute_vorticity(&self) -> Vec<Vec<f64>> {
        let mut omega = vec![vec![0.0; self.ny]; self.nx];
        for i in 1..self.nx - 1 {
            for j in 1..self.ny - 1 {
                let dv_dx = (self.v[i + 1][j] - self.v[i - 1][j]) / (2.0 * self.dx);
                let du_dy = (self.u[i][j + 1] - self.u[i][j - 1]) / (2.0 * self.dy);
                omega[i][j] = dv_dx - du_dy;
            }
        }
        omega
    }

    /// Speed |U| = sqrt(u^2 + v^2).
    pub fn compute_speed(&self) -> Vec<Vec<f64>> {
        self.u
            .iter()
            .zip(self.v.iter())
            .map(|(ur, vr)| ur.iter().zip(vr).map(|(a, b)| (a * a + b * b).sqrt()).collect())
            .collect()
    }
}

/// JSON cannot carry NaN/inf; a diverged run reports `diverged: true` and
/// zeros in place of non-finite values.
fn sanitize(field: Vec<Vec<f64>>) -> Vec<Vec<f64>> {
    field
        .into_iter()
        .map(|row| row.into_iter().map(|x| finite_or(x, 0.0)).collect())
        .collect()
}

/// Run up to `config.steps` time steps, stopping early on convergence or
/// divergence.
pub fn run_simulation(config: CfdConfig) -> Result<CfdStepResult, String> {
    let start = Instant::now();
    let mut solver = NavierStokesSolver::new(&config)?;
    let steps = config.steps.clamp(1, MAX_STEPS);
    let mut last_res = f64::INFINITY;
    let mut taken = 0;

    for _ in 0..steps {
        last_res = solver.step();
        taken += 1;
        if solver.diverged || last_res < CONVERGENCE_TOL {
            break;
        }
    }

    let elapsed_ms = start.elapsed().as_secs_f64() * 1000.0;
    let cfl = solver.compute_cfl();
    let speed = solver.compute_speed();
    let vorticity = solver.compute_vorticity();

    Ok(CfdStepResult {
        iteration: taken,
        residual: finite_or(last_res, 0.0),
        converged: !solver.diverged && last_res < CONVERGENCE_TOL,
        diverged: solver.diverged,
        cfl: finite_or(cfl, 0.0),
        dt_used: solver.last_dt,
        elapsed_ms,
        parallel: solver.parallel,
        threads: rayon::current_num_threads(),
        u: sanitize(solver.u),
        v: sanitize(solver.v),
        p: sanitize(solver.p),
        speed: sanitize(speed),
        vorticity: sanitize(vorticity),
    })
}

/// Fixed-step throughput benchmark (no early stopping).
pub fn run_benchmark(config: CfdConfig) -> Result<CfdBenchmarkResult, String> {
    let mut solver = NavierStokesSolver::new(&config)?;
    let steps = config.steps.clamp(1, MAX_STEPS);
    let start = Instant::now();
    let mut last_res = 0.0;
    for _ in 0..steps {
        last_res = solver.step();
    }
    let total_time_s = start.elapsed().as_secs_f64().max(1e-9);
    let grid_points = solver.nx * solver.ny;

    Ok(CfdBenchmarkResult {
        grid_points,
        steps_computed: steps,
        total_time_ms: total_time_s * 1000.0,
        steps_per_second: steps as f64 / total_time_s,
        million_cells_per_sec: (grid_points * steps) as f64 / (total_time_s * 1e6),
        final_residual: finite_or(last_res, 0.0),
        max_cfl: finite_or(solver.compute_cfl(), 0.0),
        parallel: solver.parallel,
        threads: rayon::current_num_threads(),
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn cavity(n: usize, steps: usize) -> CfdConfig {
        CfdConfig {
            nx: n,
            ny: n,
            lx: 1.0,
            ly: 1.0,
            nu: Some(0.01),
            re: 100.0,
            dt: 0.005,
            steps,
            lid_u: 1.0,
            archetype: "cavity".to_string(),
            obstacle_mask: None,
        }
    }

    #[test]
    fn single_step_moves_the_fluid() {
        let mut solver = NavierStokesSolver::new(&cavity(21, 1)).unwrap();
        let res = solver.step();
        assert!(res > 0.0);
        assert!(solver.compute_cfl() >= 0.0);
        assert!(!solver.diverged);
    }

    #[test]
    fn parallel_matches_sequential_bit_for_bit() {
        let config = cavity(130, 3); // above PARALLEL_MIN_CELLS
        let mut par = NavierStokesSolver::new(&config).unwrap();
        let mut seq = NavierStokesSolver::new(&config).unwrap();
        assert!(par.parallel);
        seq.parallel = false;
        for _ in 0..3 {
            par.step();
            seq.step();
        }
        assert_eq!(par.u, seq.u);
        assert_eq!(par.v, seq.v);
        assert_eq!(par.p, seq.p);
    }

    #[test]
    fn cavity_reaches_ghia_primary_vortex_strength() {
        // Re = 100: Ghia et al. (1982) give min u = -0.2109 on x = 0.5.
        let result = run_simulation(cavity(41, 20_000)).unwrap();
        assert!(result.converged, "residual {}", result.residual);
        let u_mid = &result.u[20];
        let u_min = u_mid.iter().cloned().fold(f64::INFINITY, f64::min);
        assert!((-0.25..-0.15).contains(&u_min), "u_min = {u_min}");
    }

    #[test]
    fn open_channel_pins_outlet_pressure() {
        let mut config = cavity(40, 50);
        config.archetype = "cylinder".to_string();
        let result = run_simulation(config).unwrap();
        assert!(!result.diverged);
        assert!(result.p[39].iter().all(|&p| p == 0.0));
        assert_eq!(result.u[0][20], 1.0); // inlet
    }

    #[test]
    fn reports_steps_actually_taken() {
        let result = run_simulation(cavity(21, 5)).unwrap();
        assert_eq!(result.iteration, 5);
    }

    #[test]
    fn viscous_limit_keeps_high_viscosity_stable() {
        // nu * dt / dx^2 = 1 * 0.005 * 1600 = 8 would blow up without the limit
        let mut config = cavity(41, 200);
        config.nu = Some(1.0);
        let result = run_simulation(config).unwrap();
        assert!(!result.diverged);
        assert!(result.dt_used < 0.005);
    }

    #[test]
    fn rejects_mask_with_wrong_shape() {
        let mut config = cavity(20, 1);
        config.obstacle_mask = Some(vec![vec![false; 5]; 5]);
        assert!(NavierStokesSolver::new(&config).is_err());
    }

    #[test]
    fn solid_cells_have_no_velocity() {
        let mut config = cavity(30, 20);
        config.archetype = "obstacle".to_string();
        let mut mask = vec![vec![false; 30]; 30];
        for row in mask.iter_mut().take(15).skip(10) {
            for cell in row.iter_mut().take(18).skip(12) {
                *cell = true;
            }
        }
        config.obstacle_mask = Some(mask);
        let result = run_simulation(config).unwrap();
        assert_eq!(result.u[12][15], 0.0);
        assert_eq!(result.v[12][15], 0.0);
    }
}
