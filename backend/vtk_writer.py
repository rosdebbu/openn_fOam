"""
OpenZess VTK Writer — Export CFD Fields to ParaView format (.vtk)
"""

import os
import numpy as np

def export_vtk(mesh, u: np.ndarray, v: np.ndarray, p: np.ndarray, filename: str):
    """
    Export 2D mesh fields (u, v, p) into a VTK Legacy Structured Points format.
    Compatible with ParaView, VisIt, and PyVista.
    """
    nx, ny = mesh.nx, mesh.ny
    dx, dy = mesh.dx, mesh.dy
    
    os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
    
    with open(filename, 'w') as f:
        f.write("# vtk DataFile Version 3.0\n")
        f.write("OpenZess CFD Simulation Data\n")
        f.write("ASCII\n")
        f.write("DATASET STRUCTURED_POINTS\n")
        f.write(f"DIMENSIONS {nx} {ny} 1\n")
        f.write(f"ORIGIN 0.0 0.0 0.0\n")
        f.write(f"SPACING {dx} {dy} 1.0\n\n")
        
        n_points = nx * ny
        f.write(f"POINT_DATA {n_points}\n")
        
        # Velocity Vector Field U = (u, v, 0)
        f.write("VECTORS velocity float\n")
        for j in range(ny):
            for i in range(nx):
                f.write(f"{u[i, j]:.6e} {v[i, j]:.6e} 0.000000e+00\n")
        f.write("\n")
        
        # Pressure Field p
        f.write("SCALARS pressure float 1\n")
        f.write("LOOKUP_TABLE default\n")
        for j in range(ny):
            for i in range(nx):
                f.write(f"{p[i, j]:.6e}\n")
                
    return filename
