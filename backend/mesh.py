"""
OpenZess Mesh Module — 2D Grid Generation
"""

import numpy as np

class Mesh2D:
    """
    2D Structured Mesh for finite difference / finite volume CFD.
    """
    def __init__(self, nx: int, ny: int, lx: float = 1.0, ly: float = 1.0):
        self.nx = nx
        self.ny = ny
        self.lx = lx
        self.ly = ly
        
        self.dx = lx / nx
        self.dy = ly / ny
        self.n_cells = nx * ny
        
        self.xc = np.linspace(self.dx / 2, lx - self.dx / 2, nx)
        self.yc = np.linspace(self.dy / 2, ly - self.dy / 2, ny)
        self.X, self.Y = np.meshgrid(self.xc, self.yc, indexing='ij')

    def to_dict(self):
        return {
            "nx": self.nx,
            "ny": self.ny,
            "lx": self.lx,
            "ly": self.ly,
            "dx": self.dx,
            "dy": self.dy,
            "n_cells": self.n_cells
        }
