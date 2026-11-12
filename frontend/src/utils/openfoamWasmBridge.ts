/**
 * OpenZess In-Browser OpenFOAM & WebAssembly Bridge
 * 
 * Manages the client-side CFD Web Worker lifecycle, dictionary generation,
 * and data interchange for browser-native simulations.
 */

export interface OpenFoamCaseFiles {
  'system/controlDict': string;
  'system/fvSchemes': string;
  'system/fvSolution': string;
  'constant/transportProperties': string;
  '0/U': string;
  '0/p': string;
}

export function generateOpenFoamCase(reynolds: number, maxIter: number = 200): OpenFoamCaseFiles {
  const nu = (1.0 / Math.max(1.0, reynolds)).toExponential(4);

  return {
    'system/controlDict': `/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\\\    /   O peration     | Version:  v2312                                 |
|   \\\\  /    A nd           | Website:  www.openfoam.com                      |
|    \\\\/     M anipulation  | Case:     OpenZess WebAssembly Simulation       |
\\*---------------------------------------------------------------------------*/
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "system";
    object      controlDict;
}

application     icoFoam;
startFrom       startTime;
startTime       0;
stopAt          endTime;
endTime         ${(maxIter * 0.005).toFixed(3)};
deltaT          0.002;
writeControl    timeStep;
writeInterval   20;
purgeWrite      0;
writeFormat     ascii;
writePrecision  6;
runTimeModifiable true;
`,

    'system/fvSchemes': `FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "system";
    object      fvSchemes;
}

ddtSchemes
{
    default         Euler;
}

gradSchemes
{
    default         Gauss linear;
}

divSchemes
{
    default         none;
    div(phi,U)      Gauss linear;
}

laplacianSchemes
{
    default         Gauss linear orthogonal;
}

interpolationSchemes
{
    default         linear;
}

snGradSchemes
{
    default         orthogonal;
}
`,

    'system/fvSolution': `FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "system";
    object      fvSolution;
}

solvers
{
    p
    {
        solver          PCG;
        preconditioner  DIC;
        tolerance       1e-06;
        relTol          0;
    }

    U
    {
        solver          smoothSolver;
        smoother        GaussSeidel;
        tolerance       1e-05;
        relTol          0;
    }
}

PISO
{
    nCorrectors     2;
    nNonOrthogonalCorrectors 0;
    pRefCell        0;
    pRefValue       0;
}
`,

    'constant/transportProperties': `FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "constant";
    object      transportProperties;
}

transportModel  Newtonian;
nu              [0 2 -1 0 0 0 0] ${nu};
`,

    '0/U': `FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "0";
    object      U;
}

dimensions      [0 1 -1 0 0 0 0];
internalField   uniform (0 0 0);

boundaryField
{
    movingWall
    {
        type            fixedValue;
        value           uniform (1 0 0);
    }

    fixedWalls
    {
        type            noSlip;
    }
}
`,

    '0/p': `FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    location    "0";
    object      p;
}

dimensions      [0 2 -2 0 0 0 0];
internalField   uniform 0;

boundaryField
{
    movingWall
    {
        type            zeroGradient;
    }

    fixedWalls
    {
        type            zeroGradient;
    }
}
`
  };
}

