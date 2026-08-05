import type { ColormapScheme } from '../types/cfd';

export function getColorRgb(
  value: number,
  min: number,
  max: number,
  scheme: ColormapScheme = 'inferno'
): [number, number, number] {
  let norm = (value - min) / (max - min || 1);
  norm = Math.max(0, Math.min(1, norm));

  if (scheme === 'pressure') {
    // Red-Blue pressure mapping
    const r = Math.floor(255 * norm);
    const g = Math.floor(60 * (1 - Math.abs(norm - 0.5) * 2));
    const b = Math.floor(255 * (1 - norm));
    return [r, g, b];
  }

  if (scheme === 'jet') {
    // Standard Jet (Blue -> Cyan -> Green -> Yellow -> Red)
    let r = Math.floor(255 * Math.max(0, Math.min(1, 1.5 - Math.abs(norm * 4 - 3))));
    let g = Math.floor(255 * Math.max(0, Math.min(1, 1.5 - Math.abs(norm * 4 - 2))));
    let b = Math.floor(255 * Math.max(0, Math.min(1, 1.5 - Math.abs(norm * 4 - 1))));
    return [r, g, b];
  }

  if (scheme === 'coolwarm') {
    // Soft Blue to Red
    const r = Math.floor(255 * norm);
    const g = Math.floor(200 * (1 - Math.abs(norm - 0.5)));
    const b = Math.floor(255 * (1 - norm));
    return [r, g, b];
  }

  if (scheme === 'viridis') {
    // Purple -> Teal -> Yellow
    const r = Math.floor(255 * (0.2 + 0.8 * Math.pow(norm, 2)));
    const g = Math.floor(255 * Math.pow(norm, 0.7));
    const b = Math.floor(255 * (0.5 + 0.5 * (1 - norm)));
    return [r, g, b];
  }

  // Default: Inferno (Black -> Purple -> Orange -> Yellow)
  const r = Math.floor(255 * Math.pow(norm, 0.7));
  const g = Math.floor(255 * Math.pow(norm, 1.8));
  const b = Math.floor(255 * (1 - Math.abs(norm - 0.5) * 2));
  return [r, g, b];
}

export function getColorString(
  value: number,
  min: number,
  max: number,
  scheme: ColormapScheme = 'inferno'
): string {
  const [r, g, b] = getColorRgb(value, min, max, scheme);
  return `rgb(${r}, ${g}, ${b})`;
}
