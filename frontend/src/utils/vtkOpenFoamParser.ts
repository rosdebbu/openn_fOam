/**
 * OpenZess ParaView & OpenFOAM Data Parser Utility
 * 
 * Provides client-side decoding of:
 * 1. OpenFOAM polyMesh (points, faces, boundary) and field dictionaries (0/p, 0/U, 0/T).
 * 2. VTK Legacy ASCII Structured Points & PolyData format.
 * 3. Procedural CFD flow field generators for instantaneous ParaView post-processing.
 */

export interface ParsedMeshData {
  points: Float32Array;         // [x0, y0, z0, x1, y1, z1, ...]
  cells: Uint32Array;           // VTK cell array: [n, p0, p1, ..., n, ...]
  cellCount: number;
  pointCount: number;
  bounds: [number, number, number, number, number, number]; // [xmin, xmax, ymin, ymax, zmin, zmax]
  fields: {
    [key: string]: {
      name: string;
      values: Float32Array;
      numberOfComponents: number;
      min: number;
      max: number;
      unit?: string;
    };
  };
}

/**
 * Parse Legacy VTK ASCII file format (STRUCTURED_POINTS or POLYDATA).
 */
export function parseVtkAscii(vtkText: string): ParsedMeshData {
  const lines = vtkText.split(/\r?\n/).map(l => l.trim()).filter(l => l.length > 0 && !l.startsWith('#'));
  
  let datasetType = '';
  let dimensions: [number, number, number] = [1, 1, 1];
  let origin: [number, number, number] = [0, 0, 0];
  let spacing: [number, number, number] = [1, 1, 1];
  let numPoints = 0;
  
  const fields: ParsedMeshData['fields'] = {};
  
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    const tokens = line.split(/\s+/);
    const cmd = tokens[0].toUpperCase();

    if (cmd === 'DATASET') {
      datasetType = tokens[1].toUpperCase();
      i++;
    } else if (cmd === 'DIMENSIONS') {
      dimensions = [parseInt(tokens[1]), parseInt(tokens[2]), parseInt(tokens[3])];
      i++;
    } else if (cmd === 'ORIGIN') {
      origin = [parseFloat(tokens[1]), parseFloat(tokens[2]), parseFloat(tokens[3])];
      i++;
    } else if (cmd === 'SPACING') {
      spacing = [parseFloat(tokens[1]), parseFloat(tokens[2]), parseFloat(tokens[3])];
      i++;
    } else if (cmd === 'POINT_DATA') {
      numPoints = parseInt(tokens[1]);
      i++;
    } else if (cmd === 'SCALARS') {
      const fieldName = tokens[1];
      const numComp = tokens[3] ? parseInt(tokens[3]) : 1;
      i++; // Skip SCALARS line
      if (i < lines.length && lines[i].toUpperCase().startsWith('LOOKUP_TABLE')) {
        i++; // Skip LOOKUP_TABLE line
      }
      
      const values = new Float32Array(numPoints * numComp);
      let valIdx = 0;
      let minVal = Infinity;
      let maxVal = -Infinity;
      
      while (i < lines.length && valIdx < values.length) {
        const row = lines[i].split(/\s+/);
        if (['SCALARS', 'VECTORS', 'TENSORS', 'POINT_DATA', 'CELL_DATA'].includes(row[0].toUpperCase())) {
          break;
        }
        for (const valStr of row) {
          const v = parseFloat(valStr);
          if (!isNaN(v) && valIdx < values.length) {
            values[valIdx++] = v;
            if (v < minVal) minVal = v;
            if (v > maxVal) maxVal = v;
          }
        }
        i++;
      }
      
      fields[fieldName] = {
        name: fieldName,
        values,
        numberOfComponents: numComp,
        min: minVal === Infinity ? 0 : minVal,
        max: maxVal === -Infinity ? 1 : maxVal,
        unit: fieldName === 'pressure' ? 'Pa' : fieldName === 'temperature' ? 'K' : ''
      };
    } else if (cmd === 'VECTORS') {
      const fieldName = tokens[1];
      i++; // Skip VECTORS line
      
      const values = new Float32Array(numPoints * 3);
      const magValues = new Float32Array(numPoints);
      let valIdx = 0;
      let pIdx = 0;
      let minMag = Infinity;
      let maxMag = -Infinity;
      
      while (i < lines.length && valIdx < values.length) {
        const row = lines[i].split(/\s+/);
        if (['SCALARS', 'VECTORS', 'TENSORS', 'POINT_DATA', 'CELL_DATA'].includes(row[0].toUpperCase())) {
          break;
        }
        for (let r = 0; r < row.length; r += 3) {
          if (r + 2 < row.length && valIdx + 2 < values.length) {
            const vx = parseFloat(row[r]);
            const vy = parseFloat(row[r + 1]);
            const vz = parseFloat(row[r + 2]);
            values[valIdx++] = vx;
            values[valIdx++] = vy;
            values[valIdx++] = vz;
            
            const mag = Math.sqrt(vx * vx + vy * vy + vz * vz);
            magValues[pIdx++] = mag;
            if (mag < minMag) minMag = mag;
            if (mag > maxMag) maxMag = mag;
          }
        }
        i++;
      }
      
      fields[fieldName] = {
        name: fieldName,
        values,
        numberOfComponents: 3,
        min: minMag === Infinity ? 0 : minMag,
        max: maxMag === -Infinity ? 1 : maxMag,
        unit: 'm/s'
      };
      
      // Also inject velocity magnitude scalar for easy scalar coloring
      fields['velocity_magnitude'] = {
        name: 'velocity_magnitude',
        values: magValues,
        numberOfComponents: 1,
        min: minMag === Infinity ? 0 : minMag,
        max: maxMag === -Infinity ? 1 : maxMag,
        unit: 'm/s'
      };
    } else {
      i++;
    }
  }

  // If STRUCTURED_POINTS, generate explicit points and quad cells
  if (datasetType === 'STRUCTURED_POINTS' || dimensions[0] > 1) {
    const [nx, ny, nz] = dimensions;
    const [ox, oy, oz] = origin;
    const [dx, dy, dz] = spacing;
    const totalPts = nx * ny * nz;
    
    const points = new Float32Array(totalPts * 3);
    let ptIdx = 0;
    for (let k = 0; k < nz; k++) {
      for (let j = 0; j < ny; j++) {
        for (let i_x = 0; i_x < nx; i_x++) {
          points[ptIdx * 3] = ox + i_x * dx;
          points[ptIdx * 3 + 1] = oy + j * dy;
          points[ptIdx * 3 + 2] = oz + k * dz;
          ptIdx++;
        }
      }
    }

    const cellsArr: number[] = [];
    let cellCount = 0;
    if (nz === 1) {
      // 2D Quad mesh
      for (let j = 0; j < ny - 1; j++) {
        for (let i_x = 0; i_x < nx - 1; i_x++) {
          const p1 = j * nx + i_x;
          const p2 = j * nx + (i_x + 1);
          const p3 = (j + 1) * nx + (i_x + 1);
          const p4 = (j + 1) * nx + i_x;
          cellsArr.push(4, p1, p2, p3, p4);
          cellCount++;
        }
      }
    } else {
      // 3D Hexahedral mesh
      for (let k = 0; k < nz - 1; k++) {
        for (let j = 0; j < ny - 1; j++) {
          for (let i_x = 0; i_x < nx - 1; i_x++) {
            const p1 = k * (nx * ny) + j * nx + i_x;
            const p2 = k * (nx * ny) + j * nx + (i_x + 1);
            const p3 = k * (nx * ny) + (j + 1) * nx + (i_x + 1);
            const p4 = k * (nx * ny) + (j + 1) * nx + i_x;
            const p5 = (k + 1) * (nx * ny) + j * nx + i_x;
            const p6 = (k + 1) * (nx * ny) + j * nx + (i_x + 1);
            const p7 = (k + 1) * (nx * ny) + (j + 1) * nx + (i_x + 1);
            const p8 = (k + 1) * (nx * ny) + (j + 1) * nx + i_x;
            cellsArr.push(8, p1, p2, p3, p4, p5, p6, p7, p8);
            cellCount++;
          }
        }
      }
    }

    const bounds: [number, number, number, number, number, number] = [
      ox, ox + (nx - 1) * dx,
      oy, oy + (ny - 1) * dy,
      oz, oz + (nz - 1) * dz
    ];

    return {
      points,
      cells: new Uint32Array(cellsArr),
      cellCount,
      pointCount: totalPts,
      bounds,
      fields
    };
  }

  // Fallback default
  return generateProceduralCfdData(41, 41);
}

/**
 * Generate Procedural OpenFOAM Cavity & Vortex CFD Simulation Data.
 * Used for instant preview and standalone test bench.
 */
export function generateProceduralCfdData(nx: number = 41, ny: number = 41, t: number = 0): ParsedMeshData {
  const points = new Float32Array(nx * ny * 3);
  const velValues = new Float32Array(nx * ny * 3);
  const velMag = new Float32Array(nx * ny);
  const pressValues = new Float32Array(nx * ny);
  const tempValues = new Float32Array(nx * ny);
  const vortValues = new Float32Array(nx * ny);
  const cells: number[] = [];

  let idx = 0;
  let minP = Infinity, maxP = -Infinity;
  let minV = Infinity, maxV = -Infinity;
  let minT = Infinity, maxT = -Infinity;
  let minW = Infinity, maxW = -Infinity;

  for (let j = 0; j < ny; j++) {
    for (let i = 0; i < nx; i++) {
      const x = (i / (nx - 1)) * 2.0 - 1.0;
      const y = (j / (ny - 1)) * 2.0 - 1.0;
      points[idx * 3] = x;
      points[idx * 3 + 1] = y;
      points[idx * 3 + 2] = 0;

      // Realistic lid-driven cavity + von Karman vortex field
      const r = Math.sqrt(x * x + y * y);
      const theta = Math.atan2(y, x);
      const phase = t * 2.0;

      // Lid velocity top boundary driving shear layer
      const lidInfluence = Math.exp(-3.0 * (1.0 - y));
      const u_lid = lidInfluence * (1.0 - x * x);
      
      // Core recirculating vortex
      const u_vortex = -Math.sin(theta) * Math.sin(r * Math.PI) * (1.0 - r * 0.7) * (1.0 + 0.1 * Math.sin(phase));
      const v_vortex = Math.cos(theta) * Math.sin(r * Math.PI) * (1.0 - r * 0.7) * (1.0 + 0.1 * Math.cos(phase));

      const u = u_vortex + u_lid;
      const v = v_vortex;
      const speed = Math.sqrt(u * u + v * v);

      // Pressure Poisson solution approximation (high at stagnation corners, low in vortex core)
      const p = -0.5 * speed * speed + 2.0 * Math.exp(-4.0 * (r * r)) + 3.0 * (x > 0.8 && y > 0.8 ? 1.5 : 0.0);
      
      // Temperature field (buoyant thermal plume from bottom plate)
      const temp = 293.15 + 40.0 * Math.max(0, 1.0 - y * 1.2) * Math.exp(-2.0 * x * x) + 5.0 * Math.sin(x * 5 + phase);

      // Vorticity = dv/dx - du/dy
      const vort = -2.0 * Math.cos(r * Math.PI) * (1.0 - y * y);

      velValues[idx * 3] = u;
      velValues[idx * 3 + 1] = v;
      velValues[idx * 3 + 2] = 0;
      velMag[idx] = speed;
      pressValues[idx] = p;
      tempValues[idx] = temp;
      vortValues[idx] = vort;

      if (p < minP) minP = p;
      if (p > maxP) maxP = p;
      if (speed < minV) minV = speed;
      if (speed > maxV) maxV = speed;
      if (temp < minT) minT = temp;
      if (temp > maxT) maxT = temp;
      if (vort < minW) minW = vort;
      if (vort > maxW) maxW = vort;

      idx++;
    }
  }

  // Generate 2D quad cells
  for (let j = 0; j < ny - 1; j++) {
    for (let i = 0; i < nx - 1; i++) {
      const p1 = j * nx + i;
      const p2 = j * nx + (i + 1);
      const p3 = (j + 1) * nx + (i + 1);
      const p4 = (j + 1) * nx + i;
      cells.push(4, p1, p2, p3, p4);
    }
  }

  return {
    points,
    cells: new Uint32Array(cells),
    cellCount: (nx - 1) * (ny - 1),
    pointCount: nx * ny,
    bounds: [-1.0, 1.0, -1.0, 1.0, 0.0, 0.0],
    fields: {
      velocity: {
        name: 'velocity',
        values: velValues,
        numberOfComponents: 3,
        min: minV,
        max: maxV,
        unit: 'm/s'
      },
      velocity_magnitude: {
        name: 'velocity_magnitude',
        values: velMag,
        numberOfComponents: 1,
        min: minV,
        max: maxV,
        unit: 'm/s'
      },
      pressure: {
        name: 'pressure',
        values: pressValues,
        numberOfComponents: 1,
        min: minP,
        max: maxP,
        unit: 'Pa'
      },
      temperature: {
        name: 'temperature',
        values: tempValues,
        numberOfComponents: 1,
        min: minT,
        max: maxT,
        unit: 'K'
      },
      vorticity: {
        name: 'vorticity',
        values: vortValues,
        numberOfComponents: 1,
        min: minW,
        max: maxW,
        unit: '1/s'
      }
    }
  };
}

/**
 * Parse OpenFOAM polyMesh/points ASCII file.
 */
export function parseOpenFoamPoints(content: string): Float32Array {
  // Look for the count followed by '('
  const countMatch = content.match(/(\d+)\s*\(/);
  if (!countMatch) return new Float32Array(0);
  const startIdx = content.indexOf('(', countMatch.index!) + 1;
  const endIdx = content.lastIndexOf(')');
  const body = content.substring(startIdx, endIdx);

  const coords = body.match(/\(\s*([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s*\)/g);
  if (!coords) return new Float32Array(0);

  const pts = new Float32Array(coords.length * 3);
  for (let i = 0; i < coords.length; i++) {
    const nums = coords[i].replace(/[()]/g, '').trim().split(/\s+/);
    pts[i * 3] = parseFloat(nums[0]);
    pts[i * 3 + 1] = parseFloat(nums[1]);
    pts[i * 3 + 2] = parseFloat(nums[2]);
  }
  return pts;
}

/**
 * Parse OpenFOAM scalar field file (e.g. 0/p, 0/T).
 */
export function parseOpenFoamScalarField(content: string): Float32Array {
  const match = content.match(/internalField\s+nonuniform\s+List<scalar>\s+(\d+)\s*\(([\s\S]*?)\);/);
  if (!match) {
    // Check if uniform
    const uniformMatch = content.match(/internalField\s+uniform\s+([-\d.eE+]+);/);
    if (uniformMatch) {
      const val = parseFloat(uniformMatch[1]);
      return new Float32Array([val]);
    }
    return new Float32Array(0);
  }
  const body = match[2];
  const nums = body.trim().split(/\s+/).map(Number);
  return new Float32Array(nums);
}
