use wasm_bindgen::prelude::*;
use js_sys::Float32Array;

#[wasm_bindgen]
pub struct WasmCfdSolver {
    nx: usize,
    ny: usize,
    dx: f32,
    dy: f32,
    dt: f32,
    nu: f32,
    rho: f32,
    reynolds: f32,

    // Primary State Arrays
    u: Vec<f32>,
    v: Vec<f32>,
    u_prev: Vec<f32>,
    v_prev: Vec<f32>,
    p: Vec<f32>,
    p_prev: Vec<f32>,
    div: Vec<f32>,
    vorticity: Vec<f32>,
    speed: Vec<f32>,
    mask: Vec<u8>, // 1 for solid obstacle, 0 for fluid

    // Iteration & Physics Metrics
    iteration: u32,
    max_cfl: f32,
    last_residual: f32,
    time_elapsed: f32,
    scenario_type: u8, // 0 = Cavity, 1 = Tunnel/Obstacle
}

#[wasm_bindgen]
impl WasmCfdSolver {
    #[wasm_bindgen(constructor)]
    pub fn new(nx: usize, ny: usize, reynolds: f32) -> WasmCfdSolver {
        let size = nx * ny;
        let dx = 1.0 / (nx as f32 - 1.0);
        let dy = 1.0 / (ny as f32 - 1.0);
        let nu = 1.0 / reynolds.max(1.0);
        let dt = 0.45 * (dx.min(dy)) / 1.0; // CFL safe baseline

        let mut solver = WasmCfdSolver {
            nx,
            ny,
            dx,
            dy,
            dt,
            nu,
            rho: 1.0,
            reynolds,
            u: vec![0.0; size],
            v: vec![0.0; size],
            u_prev: vec![0.0; size],
            v_prev: vec![0.0; size],
            p: vec![0.0; size],
            p_prev: vec![0.0; size],
            div: vec![0.0; size],
            vorticity: vec![0.0; size],
            speed: vec![0.0; size],
            mask: vec![0; size],
            iteration: 0,
            max_cfl: 0.0,
            last_residual: 1.0,
            time_elapsed: 0.0,
            scenario_type: 0, // default cavity
        };

        solver.init_cavity();
        solver
    }

    pub fn set_reynolds(&mut self, reynolds: f32) {
        self.reynolds = reynolds.max(1.0);
        self.nu = 1.0 / self.reynolds;
    }

    pub fn set_scenario(&mut self, scenario: u8) {
        self.scenario_type = scenario;
        self.reset();
    }

    pub fn reset(&mut self) {
        let size = self.nx * self.ny;
        self.u.fill(0.0);
        self.v.fill(0.0);
        self.u_prev.fill(0.0);
        self.v_prev.fill(0.0);
        self.p.fill(0.0);
        self.p_prev.fill(0.0);
        self.div.fill(0.0);
        self.vorticity.fill(0.0);
        self.speed.fill(0.0);
        self.mask.fill(0);
        self.iteration = 0;
        self.time_elapsed = 0.0;

        if self.scenario_type == 0 {
            self.init_cavity();
        } else {
            self.init_tunnel_obstacle();
        }
    }

    fn idx(&self, i: usize, j: usize) -> usize {
        j * self.nx + i
    }

    fn init_cavity(&mut self) {
        // Set top lid velocity to 1.0
        let top_j = self.ny - 1;
        for i in 0..self.nx {
            let id = self.idx(i, top_j);
            self.u[id] = 1.0;
        }
    }

    fn init_tunnel_obstacle(&mut self) {
        // Center obstacle
        let cx = self.nx / 3;
        let cy = self.ny / 2;
        let radius = (self.ny / 6).max(2);

        for j in 0..self.ny {
            for i in 0..self.nx {
                let id = self.idx(i, j);
                let di = i as i32 - cx as i32;
                let dj = j as i32 - cy as i32;
                if di * di + dj * dj <= (radius * radius) as i32 {
                    self.mask[id] = 1;
                } else {
                    self.u[id] = 0.5; // Inlet initial flow
                }
            }
        }
    }

    pub fn step(&mut self, steps: usize) -> f32 {
        for _ in 0..steps {
            self.solve_single_step();
        }
        self.compute_derived_fields();
        self.last_residual
    }

    fn solve_single_step(&mut self) {
        let nx = self.nx;
        let ny = self.ny;
        let dx = self.dx;
        let dy = self.dy;
        let dt = self.dt;
        let nu = self.nu;

        // Backup current velocities for advection
        self.u_prev.copy_from_slice(&self.u);
        self.v_prev.copy_from_slice(&self.v);

        // 1. Advection & Diffusion (Tentative Velocities u*, v*)
        for j in 1..(ny - 1) {
            for i in 1..(nx - 1) {
                let id = j * nx + i;
                if self.mask[id] == 1 {
                    self.u[id] = 0.0;
                    self.v[id] = 0.0;
                    continue;
                }

                let u_curr = self.u_prev[id];
                let v_curr = self.v_prev[id];

                // Upwind Differencing for Advection
                let u_adv_x = if u_curr > 0.0 {
                    u_curr * (u_curr - self.u_prev[id - 1]) / dx
                } else {
                    u_curr * (self.u_prev[id + 1] - u_curr) / dx
                };

                let u_adv_y = if v_curr > 0.0 {
                    v_curr * (u_curr - self.u_prev[id - nx]) / dy
                } else {
                    v_curr * (self.u_prev[id + nx] - u_curr) / dy
                };

                let v_adv_x = if u_curr > 0.0 {
                    u_curr * (v_curr - self.v_prev[id - 1]) / dx
                } else {
                    u_curr * (self.v_prev[id + 1] - v_curr) / dx
                };

                let v_adv_y = if v_curr > 0.0 {
                    v_curr * (v_curr - self.v_prev[id - nx]) / dy
                } else {
                    v_curr * (self.v_prev[id + nx] - v_curr) / dy
                };

                // Central Differencing for Viscous Diffusion
                let u_diff = nu * (
                    (self.u_prev[id + 1] - 2.0 * u_curr + self.u_prev[id - 1]) / (dx * dx) +
                    (self.u_prev[id + nx] - 2.0 * u_curr + self.u_prev[id - nx]) / (dy * dy)
                );

                let v_diff = nu * (
                    (self.v_prev[id + 1] - 2.0 * v_curr + self.v_prev[id - 1]) / (dx * dx) +
                    (self.v_prev[id + nx] - 2.0 * v_curr + self.v_prev[id - nx]) / (dy * dy)
                );

                self.u[id] = u_curr + dt * (-u_adv_x - u_adv_y + u_diff);
                self.v[id] = v_curr + dt * (-v_adv_x - v_adv_y + v_diff);
            }
        }

        // 2. Velocity Divergence Calculation
        let rho_dt = self.rho / dt;
        for j in 1..(ny - 1) {
            for i in 1..(nx - 1) {
                let id = j * nx + i;
                if self.mask[id] == 1 {
                    self.div[id] = 0.0;
                } else {
                    let du_dx = (self.u[id + 1] - self.u[id - 1]) / (2.0 * dx);
                    let dv_dy = (self.v[id + nx] - self.v[id - nx]) / (2.0 * dy);
                    self.div[id] = rho_dt * (du_dx + dv_dy);
                }
            }
        }

        // 3. Pressure-Poisson Iteration (Successive Over-Relaxation)
        let idx2 = 1.0 / (dx * dx);
        let idy2 = 1.0 / (dy * dy);
        let denom = 2.0 * (idx2 + idy2);
        let omega = 1.25; // SOR acceleration parameter

        let mut max_p_diff: f32 = 0.0;
        for _ in 0..25 {
            max_p_diff = 0.0;
            self.p_prev.copy_from_slice(&self.p);

            for j in 1..(ny - 1) {
                for i in 1..(nx - 1) {
                    let id = j * nx + i;
                    if self.mask[id] == 1 {
                        continue;
                    }

                    let p_old = self.p[id];
                    let rhs = (self.p[id + 1] + self.p[id - 1]) * idx2 +
                              (self.p[id + nx] + self.p[id - nx]) * idy2 -
                              self.div[id];
                    let p_new = (1.0 - omega) * p_old + (omega * rhs / denom);
                    self.p[id] = p_new;

                    let diff = (p_new - p_old).abs();
                    if diff > max_p_diff {
                        max_p_diff = diff;
                    }
                }
            }

            // Pressure Neumann Boundary Conditions
            for i in 0..nx {
                self.p[self.idx(i, 0)] = self.p[self.idx(i, 1)];
                self.p[self.idx(i, ny - 1)] = self.p[self.idx(i, ny - 2)];
            }
            for j in 0..ny {
                self.p[self.idx(0, j)] = self.p[self.idx(1, j)];
                self.p[self.idx(nx - 1, j)] = self.p[self.idx(nx - 2, j)];
            }
        }
        self.last_residual = max_p_diff;

        // 4. Divergence-Free Velocity Correction
        let dt_rho = dt / self.rho;
        for j in 1..(ny - 1) {
            for i in 1..(nx - 1) {
                let id = j * nx + i;
                if self.mask[id] == 1 {
                    self.u[id] = 0.0;
                    self.v[id] = 0.0;
                    continue;
                }

                let dp_dx = (self.p[id + 1] - self.p[id - 1]) / (2.0 * dx);
                let dp_dy = (self.p[id + nx] - self.p[id - nx]) / (2.0 * dy);

                self.u[id] -= dt_rho * dp_dx;
                self.v[id] -= dt_rho * dp_dy;
            }
        }

        // 5. Re-enforce Physical Boundary Conditions
        if self.scenario_type == 0 {
            // Lid-Driven Cavity
            let top_j = ny - 1;
            for i in 0..nx {
                self.u[self.idx(i, 0)] = 0.0;
                self.v[self.idx(i, 0)] = 0.0;
                self.u[self.idx(i, top_j)] = 1.0; // Moving Lid
                self.v[self.idx(i, top_j)] = 0.0;
            }
            for j in 0..ny {
                self.u[self.idx(0, j)] = 0.0;
                self.v[self.idx(0, j)] = 0.0;
                self.u[self.idx(nx - 1, j)] = 0.0;
                self.v[self.idx(nx - 1, j)] = 0.0;
            }
        } else {
            // Wind Tunnel Obstacle Flow
            for j in 0..ny {
                self.u[self.idx(0, j)] = 1.0; // Inlet
                self.v[self.idx(0, j)] = 0.0;
                self.u[self.idx(nx - 1, j)] = self.u[self.idx(nx - 2, j)]; // Outlet Neumann
                self.v[self.idx(nx - 1, j)] = self.v[self.idx(nx - 2, j)];
            }
            for i in 0..nx {
                self.u[self.idx(i, 0)] = 0.0; // Slip / No-slip walls
                self.v[self.idx(i, 0)] = 0.0;
                self.u[self.idx(i, ny - 1)] = 0.0;
                self.v[self.idx(i, ny - 1)] = 0.0;
            }
        }

        self.iteration += 1;
        self.time_elapsed += dt;
    }

    fn compute_derived_fields(&mut self) {
        let nx = self.nx;
        let ny = self.ny;
        let dx = self.dx;
        let dy = self.dy;
        let mut max_speed: f32 = 0.0;

        for j in 1..(ny - 1) {
            for i in 1..(nx - 1) {
                let id = j * nx + i;
                let u = self.u[id];
                let v = self.v[id];
                let spd = (u * u + v * v).sqrt();
                self.speed[id] = spd;
                if spd > max_speed {
                    max_speed = spd;
                }

                // Vorticity = dv/dx - du/dy
                let dv_dx = (self.v[id + 1] - self.v[id - 1]) / (2.0 * dx);
                let du_dy = (self.u[id + nx] - self.u[id - nx]) / (2.0 * dy);
                self.vorticity[id] = dv_dx - du_dy;
            }
        }

        self.max_cfl = (max_speed * self.dt) / self.dx.min(self.dy);
    }

    // Direct Zero-Copy WebAssembly Memory Pointers for WebGL / Canvas2D
    pub fn get_u_ptr(&self) -> *const f32 {
        self.u.as_ptr()
    }

    pub fn get_v_ptr(&self) -> *const f32 {
        self.v.as_ptr()
    }

    pub fn get_p_ptr(&self) -> *const f32 {
        self.p.as_ptr()
    }

    pub fn get_speed_ptr(&self) -> *const f32 {
        self.speed.as_ptr()
    }

    pub fn get_vorticity_ptr(&self) -> *const f32 {
        self.vorticity.as_ptr()
    }

    pub fn get_mask_ptr(&self) -> *const u8 {
        self.mask.as_ptr()
    }

    pub fn get_size(&self) -> usize {
        self.nx * self.ny
    }

    pub fn get_iteration(&self) -> u32 {
        self.iteration
    }

    pub fn get_cfl(&self) -> f32 {
        self.max_cfl
    }

    pub fn get_residual(&self) -> f32 {
        self.last_residual
    }
}

