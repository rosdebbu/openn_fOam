/**
 * OpenFOAM icoFoam Incompressible Finite Volume Solver for WebAssembly (WASM)
 * 
 * Replicates OpenFOAM's icoFoam PISO (Pressure-Implicit with Splitting of Operators)
 * algorithm in pure ANSI C (C99), ready to be compiled to WebAssembly via Emscripten,
 * Clang, or Zig for native execution inside web browsers.
 * 
 * Mathematical Formulation:
 *   Momentum Predictor:
 *     d/dt(U) + div(phi, U) - div(nu * grad(U)) = -grad(p)
 *   Pressure Poisson Equation:
 *     div(1/a_P * grad(p)) = div(HbyA)
 *   Velocity Corrector:
 *     U = HbyA - (1/a_P) * grad(p)
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#ifdef __EMSCRIPTEN__
#include <emscripten.h>
#define WASM_EXPORT EMSCRIPTEN_KEEPALIVE
#else
#define WASM_EXPORT
#endif

// Solver State Structure
typedef struct {
    int nx;
    int ny;
    int num_cells;
    float dx;
    float dy;
    float dt;
    float nu;
    float rho;
    int iteration;
    float current_time;

    // Field arrays (Cell-centred finite volume variables)
    float *U_x;
    float *U_y;
    float *U_x_prev;
    float *U_y_prev;
    float *p;
    float *p_prev;
    float *phi_x; // Face normal volumetric flux
    float *phi_y;
    float *div;   // Velocity divergence
    float *speed;
    float *vorticity;
    unsigned char *mask; // 0 = fluid, 1 = solid obstacle

    // Convergence & Telemetry
    float max_courant;
    float mean_courant;
    float p_initial_residual;
    float p_final_residual;
    float continuity_error_sum;
    int scenario; // 0 = lid cavity, 1 = obstacle tunnel
} OpenFoamWasmContext;

static OpenFoamWasmContext ctx;

static inline int idx(int i, int j) {
    return j * ctx.nx + i;
}

WASM_EXPORT
int wasm_init_solver(int nx, int ny, float reynolds, float dt_user) {
    ctx.nx = nx;
    ctx.ny = ny;
    ctx.num_cells = nx * ny;
    ctx.dx = 1.0f / (float)(nx - 1);
    ctx.dy = 1.0f / (float)(ny - 1);
    ctx.nu = 1.0f / (reynolds > 1.0f ? reynolds : 1.0f);
    ctx.rho = 1.0f;
    ctx.dt = dt_user > 0.0f ? dt_user : 0.45f * (ctx.dx < ctx.dy ? ctx.dx : ctx.dy);
    ctx.iteration = 0;
    ctx.current_time = 0.0f;
    ctx.scenario = 0; // Cavity default

    int size = ctx.num_cells;
    ctx.U_x = (float *)calloc(size, sizeof(float));
    ctx.U_y = (float *)calloc(size, sizeof(float));
    ctx.U_x_prev = (float *)calloc(size, sizeof(float));
    ctx.U_y_prev = (float *)calloc(size, sizeof(float));
    ctx.p = (float *)calloc(size, sizeof(float));
    ctx.p_prev = (float *)calloc(size, sizeof(float));
    ctx.phi_x = (float *)calloc(size, sizeof(float));
    ctx.phi_y = (float *)calloc(size, sizeof(float));
    ctx.div = (float *)calloc(size, sizeof(float));
    ctx.speed = (float *)calloc(size, sizeof(float));
    ctx.vorticity = (float *)calloc(size, sizeof(float));
    ctx.mask = (unsigned char *)calloc(size, sizeof(unsigned char));

    // Initialize OpenFOAM lid-driven cavity movingWall boundary (y = ny-1, U=(1,0,0))
    int top_j = ctx.ny - 1;
    for (int i = 0; i < ctx.nx; i++) {
        ctx.U_x[idx(i, top_j)] = 1.0f;
    }

    return 1;
}

WASM_EXPORT
void wasm_free_solver() {
    free(ctx.U_x);
    free(ctx.U_y);
    free(ctx.U_x_prev);
    free(ctx.U_y_prev);
    free(ctx.p);
    free(ctx.p_prev);
    free(ctx.phi_x);
    free(ctx.phi_y);
    free(ctx.div);
    free(ctx.speed);
    free(ctx.vorticity);
    free(ctx.mask);
}

WASM_EXPORT
void wasm_set_scenario(int scenario_id) {
    ctx.scenario = scenario_id;
    int size = ctx.num_cells;
    memset(ctx.U_x, 0, size * sizeof(float));
    memset(ctx.U_y, 0, size * sizeof(float));
    memset(ctx.p, 0, size * sizeof(float));
    memset(ctx.mask, 0, size * sizeof(unsigned char));

    if (scenario_id == 0) {
        // Cavity
        int top_j = ctx.ny - 1;
        for (int i = 0; i < ctx.nx; i++) {
            ctx.U_x[idx(i, top_j)] = 1.0f;
        }
    } else {
        // Obstacle flow
        int cx = ctx.nx / 3;
        int cy = ctx.ny / 2;
        int radius = ctx.ny / 6;
        for (int j = 0; j < ctx.ny; j++) {
            for (int i = 0; i < ctx.nx; i++) {
                int id = idx(i, j);
                int di = i - cx;
                int dj = j - cy;
                if (di * di + dj * dj <= radius * radius) {
                    ctx.mask[id] = 1;
                } else {
                    ctx.U_x[id] = 1.0f;
                }
            }
        }
    }
}

/**
 * Executes OpenFOAM PISO step:
 * 1. Momentum Predictor: U* = U^n + dt * [ -div(phi, U) + nu * laplacian(U) ]
 * 2. Pressure Poisson Equation: laplacian(p) = div(U*) / dt
 * 3. Momentum Corrector: U^(n+1) = U* - dt * grad(p)
 */
WASM_EXPORT
float wasm_step_piso(int n_correctors) {
    int nx = ctx.nx;
    int ny = ctx.ny;
    float dx = ctx.dx;
    float dy = ctx.dy;
    float dt = ctx.dt;
    float nu = ctx.nu;

    memcpy(ctx.U_x_prev, ctx.U_x, ctx.num_cells * sizeof(float));
    memcpy(ctx.U_y_prev, ctx.U_y, ctx.num_cells * sizeof(float));

    // 1. Momentum Predictor (Gauss upwind advection + central laplacian)
    for (int j = 1; j < ny - 1; j++) {
        for (int i = 1; i < nx - 1; i++) {
            int id = idx(i, j);
            if (ctx.mask[id]) {
                ctx.U_x[id] = 0.0f;
                ctx.U_y[id] = 0.0f;
                continue;
            }

            float u_c = ctx.U_x_prev[id];
            float v_c = ctx.U_y_prev[id];

            // Upwind advection
            float du_dx = u_c > 0 ? (u_c - ctx.U_x_prev[id - 1]) / dx : (ctx.U_x_prev[id + 1] - u_c) / dx;
            float du_dy = v_c > 0 ? (u_c - ctx.U_x_prev[id - nx]) / dy : (ctx.U_x_prev[id + nx] - u_c) / dy;
            float dv_dx = u_c > 0 ? (v_c - ctx.U_y_prev[id - 1]) / dx : (ctx.U_y_prev[id + 1] - v_c) / dx;
            float dv_dy = v_c > 0 ? (v_c - ctx.U_y_prev[id - nx]) / dy : (ctx.U_y_prev[id + nx] - v_c) / dy;

            // Laplacian diffusion
            float lap_u = nu * ((ctx.U_x_prev[id + 1] - 2.0f * u_c + ctx.U_x_prev[id - 1]) / (dx * dx) +
                                (ctx.U_x_prev[id + nx] - 2.0f * u_c + ctx.U_x_prev[id - nx]) / (dy * dy));
            float lap_v = nu * ((ctx.U_y_prev[id + 1] - 2.0f * v_c + ctx.U_y_prev[id - 1]) / (dx * dx) +
                                (ctx.U_y_prev[id + nx] - 2.0f * v_c + ctx.U_y_prev[id - nx]) / (dy * dy));

            ctx.U_x[id] = u_c + dt * (-u_c * du_dx - v_c * du_dy + lap_u);
            ctx.U_y[id] = v_c + dt * (-u_c * dv_dx - v_c * dv_dy + lap_v);
        }
    }

    // 2. PISO Corrector Loop
    float idx2 = 1.0f / (dx * dx);
    float idy2 = 1.0f / (dy * dy);
    float denom = 2.0f * (idx2 + idy2);
    float omega = 1.25f; // SOR relaxation parameter

    for (int corr = 0; corr < n_correctors; corr++) {
        // Compute RHS Divergence = div(U*) / dt
        float cont_err = 0.0f;
        for (int j = 1; j < ny - 1; j++) {
            for (int i = 1; i < nx - 1; i++) {
                int id = idx(i, j);
                if (ctx.mask[id]) {
                    ctx.div[id] = 0.0f;
                } else {
                    float dU_dx = (ctx.U_x[id + 1] - ctx.U_x[id - 1]) / (2.0f * dx);
                    float dV_dy = (ctx.U_y[id + nx] - ctx.U_y[id - nx]) / (2.0f * dy);
                    ctx.div[id] = (dU_dx + dV_dy) / dt;
                    cont_err += fabsf(dU_dx + dV_dy);
                }
            }
        }
        ctx.continuity_error_sum = cont_err;

        // Solve Pressure Poisson Equation via Iterative Relaxation
        float max_diff = 0.0f;
        for (int iter = 0; iter < 20; iter++) {
            max_diff = 0.0f;
            memcpy(ctx.p_prev, ctx.p, ctx.num_cells * sizeof(float));

            for (int j = 1; j < ny - 1; j++) {
                for (int i = 1; i < nx - 1; i++) {
                    int id = idx(i, j);
                    if (ctx.mask[id]) continue;

                    float p_old = ctx.p[id];
                    float rhs = (ctx.p[id + 1] + ctx.p[id - 1]) * idx2 +
                                (ctx.p[id + nx] + ctx.p[id - nx]) * idy2 -
                                ctx.div[id];
                    float p_new = (1.0f - omega) * p_old + (omega * rhs / denom);
                    ctx.p[id] = p_new;

                    float d = fabsf(p_new - p_old);
                    if (d > max_diff) max_diff = d;
                }
            }

            // Pressure zeroGradient boundary condition
            for (int i = 0; i < nx; i++) {
                ctx.p[idx(i, 0)] = ctx.p[idx(i, 1)];
                ctx.p[idx(i, ny - 1)] = ctx.p[idx(i, ny - 2)];
            }
            for (int j = 0; j < ny; j++) {
                ctx.p[idx(0, j)] = ctx.p[idx(1, j)];
                ctx.p[idx(nx - 1, j)] = ctx.p[idx(nx - 2, j)];
            }
        }

        if (corr == 0) ctx.p_initial_residual = max_diff;
        ctx.p_final_residual = max_diff;

        // 3. Velocity Correction: U = U* - dt * grad(p)
        for (int j = 1; j < ny - 1; j++) {
            for (int i = 1; i < nx - 1; i++) {
                int id = idx(i, j);
                if (ctx.mask[id]) continue;

                float dp_dx = (ctx.p[id + 1] - ctx.p[id - 1]) / (2.0f * dx);
                float dp_dy = (ctx.p[id + nx] - ctx.p[id - nx]) / (2.0f * dy);
                ctx.U_x[id] -= dt * dp_dx;
                ctx.U_y[id] -= dt * dp_dy;
            }
        }
    }

    // Apply Physical Boundary Conditions
    if (ctx.scenario == 0) {
        // Cavity
        int top_j = ny - 1;
        for (int i = 0; i < nx; i++) {
            ctx.U_x[idx(i, 0)] = 0.0f;
            ctx.U_y[idx(i, 0)] = 0.0f;
            ctx.U_x[idx(i, top_j)] = 1.0f; // Moving Lid
            ctx.U_y[idx(i, top_j)] = 0.0f;
        }
        for (int j = 0; j < ny; j++) {
            ctx.U_x[idx(0, j)] = 0.0f;
            ctx.U_y[idx(0, j)] = 0.0f;
            ctx.U_x[idx(nx - 1, j)] = 0.0f;
            ctx.U_y[idx(nx - 1, j)] = 0.0f;
        }
    } else {
        // Tunnel
        for (int j = 0; j < ny; j++) {
            ctx.U_x[idx(0, j)] = 1.0f;
            ctx.U_y[idx(0, j)] = 0.0f;
            ctx.U_x[idx(nx - 1, j)] = ctx.U_x[idx(nx - 2, j)];
            ctx.U_y[idx(nx - 1, j)] = ctx.U_y[idx(nx - 2, j)];
        }
        for (int i = 0; i < nx; i++) {
            ctx.U_x[idx(i, 0)] = 0.0f;
            ctx.U_y[idx(i, 0)] = 0.0f;
            ctx.U_x[idx(i, ny - 1)] = 0.0f;
            ctx.U_y[idx(i, ny - 1)] = 0.0f;
        }
    }

    // Compute Derived Telemetry (Speed, Vorticity, Courant)
    float max_spd = 0.0f;
    float sum_spd = 0.0f;
    for (int j = 1; j < ny - 1; j++) {
        for (int i = 1; i < nx - 1; i++) {
            int id = idx(i, j);
            float u = ctx.U_x[id];
            float v = ctx.U_y[id];
            float spd = sqrtf(u * u + v * v);
            ctx.speed[id] = spd;
            if (spd > max_spd) max_spd = spd;
            sum_spd += spd;

            float dv_dx = (ctx.U_y[id + 1] - ctx.U_y[id - 1]) / (2.0f * dx);
            float du_dy = (ctx.U_x[id + nx] - ctx.U_x[id - nx]) / (2.0f * dy);
            ctx.vorticity[id] = dv_dx - du_dy;
        }
    }

    float min_d = dx < dy ? dx : dy;
    ctx.max_courant = (max_spd * dt) / min_d;
    ctx.mean_courant = (sum_spd / (float)ctx.num_cells * dt) / min_d;

    ctx.iteration++;
    ctx.current_time += dt;

    return ctx.p_final_residual;
}

// Memory Accessors for WebAssembly JS Binding
WASM_EXPORT float* wasm_get_u_ptr() { return ctx.U_x; }
WASM_EXPORT float* wasm_get_v_ptr() { return ctx.U_y; }
WASM_EXPORT float* wasm_get_p_ptr() { return ctx.p; }
WASM_EXPORT float* wasm_get_speed_ptr() { return ctx.speed; }
WASM_EXPORT float* wasm_get_vorticity_ptr() { return ctx.vorticity; }
WASM_EXPORT unsigned char* wasm_get_mask_ptr() { return ctx.mask; }
WASM_EXPORT int wasm_get_iteration() { return ctx.iteration; }
WASM_EXPORT float wasm_get_time() { return ctx.current_time; }
WASM_EXPORT float wasm_get_max_courant() { return ctx.max_courant; }
WASM_EXPORT float wasm_get_mean_courant() { return ctx.mean_courant; }
WASM_EXPORT float wasm_get_p_residual() { return ctx.p_final_residual; }
WASM_EXPORT float wasm_get_continuity_error() { return ctx.continuity_error_sum; }

