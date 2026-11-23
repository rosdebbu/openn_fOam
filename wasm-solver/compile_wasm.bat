@echo off
REM ============================================================================
REM OpenFOAM C/C++ WebAssembly Compilation Script
REM Compiles openfoam_icoFoam_wasm.c to WebAssembly (.wasm + .js)
REM ============================================================================

echo [OpenFOAM-WASM] Checking for Emscripten (emcc) or Clang...

where emcc >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OpenFOAM-WASM] Found Emscripten SDK. Compiling with emcc...
    emcc openfoam_icoFoam_wasm.c -O3 ^
        -s WASM=1 ^
        -s ALLOW_MEMORY_GROWTH=1 ^
        -s MODULARIZE=1 ^
        -s EXPORT_NAME="createOpenFoamWasmModule" ^
        -s EXPORTED_FUNCTIONS="['_wasm_init_solver','_wasm_free_solver','_wasm_set_scenario','_wasm_step_piso','_wasm_get_u_ptr','_wasm_get_v_ptr','_wasm_get_p_ptr','_wasm_get_speed_ptr','_wasm_get_vorticity_ptr','_wasm_get_mask_ptr','_wasm_get_iteration','_wasm_get_time','_wasm_get_max_courant','_wasm_get_mean_courant','_wasm_get_p_residual','_wasm_get_continuity_error','_malloc','_free']" ^
        -s EXPORTED_RUNTIME_METHODS="['ccall','cwrap','HEAPF32','HEAPU8']" ^
        -o ../frontend/public/openfoam_solver.js
    echo [OpenFOAM-WASM] Success! Output placed in frontend/public/openfoam_solver.js and .wasm
    exit /b 0
)

where clang >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OpenFOAM-WASM] Compiling standalone WebAssembly with Clang...
    clang --target=wasm32 -O3 -nostdlib -Wl,--no-entry -Wl,--export-all -o ../frontend/public/openfoam_solver.wasm openfoam_icoFoam_wasm.c
    echo [OpenFOAM-WASM] Standalone WASM binary compiled to frontend/public/openfoam_solver.wasm
    exit /b 0
)

echo [OpenFOAM-WASM] Note: Neither emcc nor clang found on PATH.
echo [OpenFOAM-WASM] The in-browser Web Worker fallback in frontend/src/utils/openfoamWasmBridge.ts executes
echo [OpenFOAM-WASM] the exact same C-equivalent finite volume Navier-Stokes algorithm without local toolchain prerequisites.

