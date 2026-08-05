"""
OpenZess Solver Engine — Accelerated Navier-Stokes Solver
Uses SciPy sparse matrix routines (spsolve / CG) for ultra-fast Pressure Poisson solution.
"""

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import time

from .mesh import Mesh2D


class AcceleratedSolver:
    def __init__(self, mesh: Mesh2D, Re: float = 100.0, lid_velocity: float = 1.0):
        self.mesh = mesh
        self.Re = Re
        self.lid_velocity = lid_velocity
        self.nu = lid_velocity * mesh.lx / Re
        
        self.u = np.zeros((mesh.nx, mesh.ny))
        self.v = np.zeros((mesh.nx, mesh.ny))
        self.p = np.zeros((mesh.nx, mesh.ny))
        
        self._build_poisson_matrix()

    def _build_poisson_matrix(self):
        """Build 5-point discrete Laplacian sparse matrix for Pressure Poisson equation."""
        nx, ny = self.mesh.nx, self.mesh.ny
        dx, dy = self.mesh.dx, self.mesh.dy
        
        N = nx * ny
        diag_c = -2.0 / dx**2 - 2.0 / dy**2
        diag_x = 1.0 / dx**2
        diag_y = 1.0 / dy**2
        
        A = sp.dok_matrix((N, N), dtype=np.float64)
        
        for i in range(nx):
            for j in range(ny):
                k = i * ny + j
                
                # Boundary nodes (Neumann dp/dn = 0 or reference cell)
                if i == 0 and j == 0:
                    A[k, k] = 1.0 # Reference pressure cell
                    continue
                    
                A[k, k] = diag_c
                
                # Left / Right
                if i > 0:
                    A[k, (i - 1) * ny + j] += diag_x
                else:
                    A[k, k] += diag_x # Neumann boundary reflection
                    
                if i < nx - 1:
                    A[k, (i + 1) * ny + j] += diag_x
                else:
                    A[k, k] += diag_x
                    
                # Bottom / Top
                if j > 0:
                    A[k, i * ny + (j - 1)] += diag_y
                else:
                    A[k, k] += diag_y
                    
                if j < ny - 1:
                    A[k, i * ny + (j + 1)] += diag_y
                else:
                    A[k, k] += diag_y

        self.A_poisson = A.tocsr()

    def apply_bc(self):
        # Velocity BCs
        self.u[:, 0] = 0.0;  self.v[:, 0] = 0.0   # Bottom
        self.u[0, :] = 0.0;  self.v[0, :] = 0.0   # Left
        self.u[-1, :] = 0.0; self.v[-1, :] = 0.0  # Right
        self.u[:, -1] = self.lid_velocity; self.v[:, -1] = 0.0 # Top (Moving Lid)

    def step(self, dt: float):
        nx, ny = self.mesh.nx, self.mesh.ny
        dx, dy = self.mesh.dx, self.mesh.dy
        
        u_old = self.u.copy()
        v_old = self.v.copy()
        
        # 1. Predictor (convection + diffusion)
        # Vectorized Laplacian
        lap_u = np.zeros_like(self.u)
        lap_v = np.zeros_like(self.v)
        lap_u[1:-1, 1:-1] = (
            (self.u[2:, 1:-1] - 2*self.u[1:-1, 1:-1] + self.u[:-2, 1:-1])/dx**2 +
            (self.u[1:-1, 2:] - 2*self.u[1:-1, 1:-1] + self.u[1:-1, :-2])/dy**2
        )
        lap_v[1:-1, 1:-1] = (
            (self.v[2:, 1:-1] - 2*self.v[1:-1, 1:-1] + self.v[:-2, 1:-1])/dx**2 +
            (self.v[1:-1, 2:] - 2*self.v[1:-1, 1:-1] + self.v[1:-1, :-2])/dy**2
        )
        
        # Vectorized Upwind Convection
        conv_u = np.zeros_like(self.u)
        conv_v = np.zeros_like(self.v)
        
        i, j = slice(1, -1), slice(1, -1)
        du_dx = np.where(self.u[i,j] > 0, (self.u[i,j] - self.u[:-2,j])/dx, (self.u[2:,j] - self.u[i,j])/dx)
        du_dy = np.where(self.v[i,j] > 0, (self.u[i,j] - self.u[i,:-2])/dy, (self.u[i,2:] - self.u[i,j])/dy)
        conv_u[i,j] = self.u[i,j] * du_dx + self.v[i,j] * du_dy
        
        dv_dx = np.where(self.u[i,j] > 0, (self.v[i,j] - self.v[:-2,j])/dx, (self.v[2:,j] - self.v[i,j])/dx)
        dv_dy = np.where(self.v[i,j] > 0, (self.v[i,j] - self.v[i,:-2])/dy, (self.v[i,2:] - self.v[i,j])/dy)
        conv_v[i,j] = self.u[i,j] * dv_dx + self.v[i,j] * dv_dy
        
        u_star = self.u.copy()
        v_star = self.v.copy()
        
        u_star[1:-1, 1:-1] += dt * (self.nu * lap_u[1:-1, 1:-1] - conv_u[1:-1, 1:-1])
        v_star[1:-1, 1:-1] += dt * (self.nu * lap_v[1:-1, 1:-1] - conv_v[1:-1, 1:-1])
        
        # Apply BC to star velocity
        u_star[:, 0] = 0.0; v_star[:, 0] = 0.0
        u_star[0, :] = 0.0; v_star[0, :] = 0.0
        u_star[-1, :] = 0.0; v_star[-1, :] = 0.0
        u_star[:, -1] = self.lid_velocity; v_star[:, -1] = 0.0

        # 2. Pressure Poisson RHS: (1/dt) * div(u_star)
        div_ustar = np.zeros_like(self.u)
        div_ustar[1:-1, 1:-1] = (
            (u_star[2:, 1:-1] - u_star[:-2, 1:-1]) / (2 * dx) +
            (v_star[1:-1, 2:] - v_star[1:-1, :-2]) / (2 * dy)
        )
        rhs = (div_ustar / dt).flatten()
        rhs[0] = 0.0 # Reference pressure cell
        
        # Fast Sparse Matrix Solve!
        p_flat = spla.spsolve(self.A_poisson, rhs)
        self.p = p_flat.reshape((nx, ny))
        
        # 3. Correct velocity
        dp_dx = np.zeros_like(self.p)
        dp_dy = np.zeros_like(self.p)
        dp_dx[1:-1, :] = (self.p[2:, :] - self.p[:-2, :]) / (2 * dx)
        dp_dy[:, 1:-1] = (self.p[:, 2:] - self.p[:, :-2]) / (2 * dy)
        
        self.u[1:-1, 1:-1] = u_star[1:-1, 1:-1] - dt * dp_dx[1:-1, 1:-1]
        self.v[1:-1, 1:-1] = v_star[1:-1, 1:-1] - dt * dp_dy[1:-1, 1:-1]
        
        self.apply_bc()
        
        # Residual
        res_u = np.max(np.abs(self.u - u_old))
        res_v = np.max(np.abs(self.v - v_old))
        return max(res_u, res_v)
