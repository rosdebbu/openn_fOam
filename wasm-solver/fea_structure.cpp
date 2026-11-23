/**
 * OpenZess Structural FEA Kernel for Fluid-Structure Interaction (FSI)
 *
 * Computes Euler-Bernoulli cantilever bending moment, shear, lateral deflection,
 * and Von Mises stress across a building domain from live FVM wind pressure.
 */

#include <cmath>
#include <vector>
#include <algorithm>

#ifdef __EMSCRIPTEN__
#include <emscripten/emscripten.h>
#define FEA_EXPORT EMSCRIPTEN_KEEPALIVE
#else
#define FEA_EXPORT
#endif

struct FeaContext {
    int nx = 41;
    int ny = 41;
    float youngs_modulus = 70.0e9f; // Glass/Aluminum facade composite ~70 GPa
    float max_stress_mpa = 0.0f;
    float max_disp_mm = 0.0f;

    std::vector<float> p_in;
    std::vector<unsigned char> mask_in;
    std::vector<float> stress_mpa;
    std::vector<float> disp_mm;
};

static FeaContext g_fea;

extern "C" {

FEA_EXPORT
void fea_create(int nx, int ny, float youngs_modulus_gpa) {
    g_fea.nx = nx;
    g_fea.ny = ny;
    g_fea.youngs_modulus = std::max(1.0f, youngs_modulus_gpa) * 1.0e9f;
    int n = nx * ny;
    g_fea.p_in.assign(n, 0.0f);
    g_fea.mask_in.assign(n, 0);
    g_fea.stress_mpa.assign(n, 0.0f);
    g_fea.disp_mm.assign(n, 0.0f);
    g_fea.max_stress_mpa = 0.0f;
    g_fea.max_disp_mm = 0.0f;
}

FEA_EXPORT float* fea_get_pressure_in_ptr() { return g_fea.p_in.data(); }
FEA_EXPORT unsigned char* fea_get_mask_in_ptr() { return g_fea.mask_in.data(); }
FEA_EXPORT const float* fea_get_stress_ptr() { return g_fea.stress_mpa.data(); }
FEA_EXPORT const float* fea_get_disp_ptr() { return g_fea.disp_mm.data(); }
FEA_EXPORT float fea_get_max_stress() { return g_fea.max_stress_mpa; }
FEA_EXPORT float fea_get_max_disp() { return g_fea.max_disp_mm; }

/**
 * Couples fluid pressure p (Pa-normalized) into building structural stress & drift.
 * wind_speed_ms scales dynamic pressure q = 0.5 * rho * U^2.
 */
FEA_EXPORT
void fea_solve_from_pressure(float wind_speed_ms, float building_height_m) {
    int nx = g_fea.nx;
    int ny = g_fea.ny;
    int n = nx * ny;
    std::fill(g_fea.stress_mpa.begin(), g_fea.stress_mpa.end(), 0.0f);
    std::fill(g_fea.disp_mm.begin(), g_fea.disp_mm.end(), 0.0f);

    float dy = building_height_m / static_cast<float>(std::max(1, ny - 1));
    float rho_air = 1.225f;
    float q_dyn = 0.5f * rho_air * wind_speed_ms * wind_speed_ms;

    // 1. Extract net horizontal wind load f_x(j) per vertical slice of the building
    std::vector<float> fx(ny, 0.0f);
    std::vector<int> i_min(ny, nx), i_max(ny, -1);

    for (int j = 0; j < ny; ++j) {
        for (int i = 0; i < nx; ++i) {
            if (g_fea.mask_in[j * nx + i] == 1) {
                i_min[j] = std::min(i_min[j], i);
                i_max[j] = std::max(i_max[j], i);
            }
        }
        if (i_max[j] >= i_min[j]) {
            int left_i = std::max(0, i_min[j] - 1);
            int right_i = std::min(nx - 1, i_max[j] + 1);
            float p_windward = g_fea.p_in[j * nx + left_i];
            float p_leeward = g_fea.p_in[j * nx + right_i];
            // Net pressure force per unit depth [N/m]
            fx[j] = (p_windward - p_leeward) * q_dyn * dy;
        }
    }

    // 2. Integrate top-down for shear V(j) and bending moment M(j)
    std::vector<float> shear(ny, 0.0f);
    std::vector<float> moment(ny, 0.0f);
    for (int j = ny - 2; j >= 0; --j) {
        shear[j] = shear[j + 1] + fx[j + 1];
        moment[j] = moment[j + 1] + shear[j + 1] * dy;
    }

    // 3. Compute curvature -> lateral deflection & Von Mises stress across building cells
    float b_width = 6.0f; // Reference structural depth 6 m
    float I_sec = (1.0f / 12.0f) * 1.0f * (b_width * b_width * b_width); // Second moment of area
    float theta = 0.0f;
    float disp = 0.0f;
    float max_stress = 0.0f;
    float max_disp = 0.0f;

    for (int j = 0; j < ny; ++j) {
        if (i_max[j] < i_min[j]) continue;

        float curvature = moment[j] / (g_fea.youngs_modulus * I_sec);
        theta += curvature * dy;
        disp += theta * dy;
        float disp_mm_val = disp * 1000.0f;
        max_disp = std::max(max_disp, std::fabs(disp_mm_val));

        float mid_i = 0.5f * static_cast<float>(i_min[j] + i_max[j]);
        float half_span = std::max(0.5f, 0.5f * static_cast<float>(i_max[j] - i_min[j]));

        for (int i = i_min[j]; i <= i_max[j]; ++i) {
            int id = j * nx + i;
            if (g_fea.mask_in[id] == 1) {
                float c_dist = ((static_cast<float>(i) - mid_i) / half_span) * (0.5f * b_width);
                float sigma_xx = (moment[j] * c_dist) / I_sec;
                float tau_xy = 1.5f * shear[j] / b_width;
                float von_mises_pa = std::sqrt(sigma_xx * sigma_xx + 3.0f * tau_xy * tau_xy);
                float vm_mpa = von_mises_pa / 1.0e6f;
                g_fea.stress_mpa[id] = vm_mpa;
                g_fea.disp_mm[id] = disp_mm_val;
                max_stress = std::max(max_stress, vm_mpa);
            }
        }
    }

    g_fea.max_stress_mpa = max_stress;
    g_fea.max_disp_mm = max_disp;
}

} // extern "C"
