"""
OpenZess VTK Writer — Export CFD Fields to ParaView format (.vtk)
"""

import io
import os
import numpy as np

def generate_vtk_bytes(mesh, u: np.ndarray, v: np.ndarray, p: np.ndarray) -> bytes:
    """
    Generate VTK Legacy Structured Points format directly in-memory as bytes.
    Compatible with ParaView, VisIt, and PyVista.
    """
    nx, ny = mesh.nx, mesh.ny
    dx, dy = mesh.dx, mesh.dy
    n_points = nx * ny
    
    out = io.StringIO()
    out.write("# vtk DataFile Version 3.0\n")
    out.write("OpenZess CFD Simulation Data\n")
    out.write("ASCII\n")
    out.write("DATASET STRUCTURED_POINTS\n")
    out.write(f"DIMENSIONS {nx} {ny} 1\n")
    out.write("ORIGIN 0.0 0.0 0.0\n")
    out.write(f"SPACING {dx} {dy} 1.0\n\n")
    
    out.write(f"POINT_DATA {n_points}\n")
    
    # Velocity Vector Field U = (u, v, 0)
    out.write("VECTORS velocity float\n")
    for j in range(ny):
        for i in range(nx):
            out.write(f"{u[i, j]:.6e} {v[i, j]:.6e} 0.000000e+00\n")
    out.write("\n")
    
    # Pressure Field p
    out.write("SCALARS pressure float 1\n")
    out.write("LOOKUP_TABLE default\n")
    for j in range(ny):
        for i in range(nx):
            out.write(f"{p[i, j]:.6e}\n")
            
    return out.getvalue().encode('utf-8')


def export_vtk(mesh, u: np.ndarray, v: np.ndarray, p: np.ndarray, filename: str = None) -> bytes:
    """
    Export 2D mesh fields (u, v, p) into a VTK Legacy Structured Points format.
    Optionally writes to disk if filename provided.
    """
    content = generate_vtk_bytes(mesh, u, v, p)
    if filename:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
            with open(filename, 'wb') as f:
                f.write(content)
        except Exception as e:
            print(f"[VTK Writer] Warning: File write bypassed: {e}")
    return content
