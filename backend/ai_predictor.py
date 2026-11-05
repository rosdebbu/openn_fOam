"""
OpenZess instant flow preview ("ai" solver mode).

Despite the module name, nothing here is a neural network. This file used
to describe a hand-written formula as a "trained PINN"; that claim was false
and has been removed. What the "ai" mode actually computes:

* Open channel / external-flow archetypes -> a **potential-flow** solution
  (inviscid, irrotational, exactly divergence-free) around the real obstacle
  mask, from one sparse Laplace solve. Pressure follows from Bernoulli.
  It captures blockage, acceleration over/under bodies and venturi throat
  speed-up. It has no boundary layers, separation or wake, and therefore
  (d'Alembert's paradox) ~zero drag and no lift without circulation.
* Lid-driven cavity -> the Stokes (Re -> 0) solution from one sparse
  biharmonic solve (RMSE ~0.03 vs Ghia et al. 1982 at Re = 100; misses the
  inertial asymmetry at higher Re). The previous closed-form "PINN" vortex
  spun the wrong way (RMSE ~0.65, worse than an all-zero field).

Buoyancy-driven archetypes have no meaningful instant approximation; the
server runs the real CFD solver for those instead.
"""

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

from .mesh import Mesh2D


def predict_cavity_stokes(mesh: Mesh2D, lid_velocity: float = 1.0, nu: float = 0.01):
    """Stokes-flow (Re -> 0) solution of the lid-driven cavity.

    Solves the biharmonic equation for the streamfunction, del^4 psi = 0, on
    the cell vertices with the 13-point stencil: psi = 0 on every wall,
    d(psi)/dn = 0 on the fixed walls and d(psi)/dy = U on the lid (ghost-node
    elimination). One sparse LU solve, second-order accurate, exactly
    divergence-free. Pressure follows from Stokes momentum, grad p =
    nu * lap(u), integrated along grid lines (mean removed).

    This is the creeping-flow limit: it misses the inertial asymmetry that
    grows with Re (fine at Re ~ 100, increasingly wrong above ~ 400).
    Requires a square cavity with square cells (nx == ny, dx == dy).
    """
    n = mesh.nx
    if mesh.ny != n or not np.isclose(mesh.dx, mesh.dy):
        raise ValueError("Stokes cavity preview needs a square grid")
    h = mesh.dx
    m = n - 1  # interior vertices per side

    def k(i, j):
        return (i - 1) * m + (j - 1)

    stencil = [(0, 0, 20.0)]
    stencil += [(di, dj, -8.0) for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1))]
    stencil += [(di, dj, 2.0) for di, dj in ((1, 1), (1, -1), (-1, 1), (-1, -1))]
    stencil += [(di, dj, 1.0) for di, dj in ((2, 0), (-2, 0), (0, 2), (0, -2))]

    rows, cols, vals = [], [], []
    rhs = np.zeros(m * m)
    for i in range(1, n):
        for j in range(1, n):
            row = k(i, j)
            for di, dj, c in stencil:
                a, b = i + di, j + dj
                if a in (0, n) or b in (0, n):
                    continue                      # wall vertex, psi = 0
                if a == -1:
                    a = 1                         # left wall: dpsi/dx = 0
                elif a == n + 1:
                    a = n - 1                     # right wall: dpsi/dx = 0
                if b == -1:
                    b = 1                         # floor: dpsi/dy = 0
                elif b == n + 1:                  # lid: dpsi/dy = U
                    b = n - 1
                    rhs[row] -= c * 2.0 * h * lid_velocity
                rows.append(row)
                cols.append(k(a, b))
                vals.append(c)
    A = sp.csr_matrix((vals, (rows, cols)), shape=(m * m, m * m))
    psi = np.zeros((n + 1, n + 1))
    psi[1:n, 1:n] = spla.spsolve(A.tocsc(), rhs).reshape(m, m)

    # Cell-centre velocities from vertex streamfunction: u = dpsi/dy, v = -dpsi/dx
    u = 0.5 * ((psi[:-1, 1:] - psi[:-1, :-1]) + (psi[1:, 1:] - psi[1:, :-1])) / h
    v = -0.5 * ((psi[1:, :-1] - psi[:-1, :-1]) + (psi[1:, 1:] - psi[:-1, 1:])) / h

    # Stokes pressure: integrate dp/dx = nu*lap(u) along rows, anchored by
    # dp/dy = nu*lap(v) up the centre column.
    def lap(f):
        return np.gradient(np.gradient(f, h, axis=0), h, axis=0) + \
            np.gradient(np.gradient(f, h, axis=1), h, axis=1)

    gx, gy = nu * lap(u), nu * lap(v)
    ic = n // 2
    p_col = np.concatenate([[0.0], np.cumsum(0.5 * (gy[ic, 1:] + gy[ic, :-1]) * h)])
    p = np.zeros_like(u)
    p[ic, :] = p_col
    p[ic + 1:, :] = p_col + np.cumsum(0.5 * (gx[ic + 1:, :] + gx[ic:-1, :]) * h, axis=0)
    p[:ic, :] = p_col - np.cumsum((0.5 * (gx[1:ic + 1, :] + gx[:ic, :]) * h)[::-1], axis=0)[::-1]
    p -= p.mean()
    return u, v, p


def predict_potential_flow(mesh: Mesh2D, mask: np.ndarray, U: float = 1.0):
    """Inviscid potential flow through a channel around a solid mask.

    Finite-volume Laplace solve for the velocity potential on fluid cells:
      * inlet (west face of column 0):  d(phi)/dx = U
      * outlet (east face of last column): phi = 0
      * floor / lid and every solid face: zero normal flux (slip walls)

    Face velocities are potential gradients, so the discrete divergence of
    the face fluxes is zero to solver precision. Cell-centre velocities are
    face averages; pressure is kinematic Bernoulli, p = (U^2 - |u|^2) / 2,
    relative to the inlet static pressure. Solid cells get u = v = p = 0.
    """
    nx, ny = mesh.nx, mesh.ny
    dx, dy = mesh.dx, mesh.dy
    fluid = ~np.asarray(mask, dtype=bool)
    if not fluid.any():
        zeros = np.zeros((nx, ny))
        return zeros, zeros.copy(), zeros.copy()

    # Number the fluid cells
    index = -np.ones((nx, ny), dtype=np.int64)
    index[fluid] = np.arange(int(fluid.sum()))
    n_unknowns = int(fluid.sum())

    rows, cols, vals = [], [], []
    diag = np.zeros(n_unknowns)
    rhs = np.zeros(n_unknowns)

    def couple(a_mask, b_mask, a_idx, b_idx, w):
        """Add flux coupling w*(phi_b - phi_a) for open fluid-fluid faces."""
        both = a_mask & b_mask
        ia, ib = a_idx[both], b_idx[both]
        rows.extend([ia, ib])
        cols.extend([ib, ia])
        vals.extend([np.full(ia.size, w), np.full(ib.size, w)])
        np.add.at(diag, ia, -w)
        np.add.at(diag, ib, -w)

    couple(fluid[:-1, :], fluid[1:, :], index[:-1, :], index[1:, :], 1.0 / dx**2)
    couple(fluid[:, :-1], fluid[:, 1:], index[:, :-1], index[:, 1:], 1.0 / dy**2)

    # Inlet flux U through the west face of column 0
    inlet = index[0, fluid[0]]
    rhs[inlet] += U / dx
    # Dirichlet phi = 0 on the east face of the last column (half-cell away)
    outlet = index[-1, fluid[-1]]
    diag[outlet] -= 2.0 / dx**2

    A = sp.csr_matrix(
        (np.concatenate(vals + [diag]),
         (np.concatenate(rows + [np.arange(n_unknowns)]),
          np.concatenate(cols + [np.arange(n_unknowns)]))),
        shape=(n_unknowns, n_unknowns),
    )
    phi_fluid = spla.spsolve(A.tocsc(), rhs)
    phi = np.zeros((nx, ny))
    phi[fluid] = phi_fluid

    # Face velocities: x-faces (nx+1, ny), y-faces (nx, ny+1)
    uf = np.zeros((nx + 1, ny))
    open_x = fluid[:-1, :] & fluid[1:, :]
    uf[1:-1, :] = np.where(open_x, (phi[1:, :] - phi[:-1, :]) / dx, 0.0)
    uf[0, :] = np.where(fluid[0], U, 0.0)
    uf[-1, :] = np.where(fluid[-1], (0.0 - phi[-1, :]) / (0.5 * dx), 0.0)

    vf = np.zeros((nx, ny + 1))
    open_y = fluid[:, :-1] & fluid[:, 1:]
    vf[:, 1:-1] = np.where(open_y, (phi[:, 1:] - phi[:, :-1]) / dy, 0.0)

    u = 0.5 * (uf[:-1, :] + uf[1:, :])
    v = 0.5 * (vf[:, :-1] + vf[:, 1:])
    u[~fluid] = 0.0
    v[~fluid] = 0.0

    p = 0.5 * (U**2 - (u**2 + v**2))
    p[~fluid] = 0.0
    return u, v, p
