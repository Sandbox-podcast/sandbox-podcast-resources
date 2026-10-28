/**
 * Mise en page du Program (rendu du studio virtuel), en fonctions pures : positions des participants détourés,
 * bandeau des noms et des niveaux audio, titre, signal « ON AIR ». Les coordonnées sont celles d'un canevas de
 * `width × height` pixels (1920 × 1080 en production).
 */
export interface Rect {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface ProgramLayout {
  /** Zone de chaque participant, de gauche à droite. Les voisins se chevauchent légèrement. */
  slots: Rect[];
  /** Bandeau du bas, dessiné par-dessus le bas des silhouettes. */
  panel: Rect;
  /** Pour chaque participant : zone de son nom et zone de ses barres de niveau, dans le bandeau. */
  captions: { name: Rect; levels: Rect }[];
  title: Rect;
  onAir: Rect;
}

export const MAX_PARTICIPANTS = 5;

/** Rapport largeur/hauteur d'une caméra : une silhouette ne dépasse jamais sa largeur naturelle. */
const CAMERA_ASPECT = 16 / 9;

export function programLayout(count: number, width: number, height: number): ProgramLayout {
  const n = Math.min(MAX_PARTICIPANTS, Math.max(1, Math.floor(count)));
  const margin = 0.0125 * width;
  const spacing = (width - 2 * margin) / n;
  const slotHeight = 0.5 * height;
  const slotWidth = Math.min(spacing * 1.1, slotHeight * CAMERA_ASPECT);
  const slotY = 0.13 * height;

  const panel: Rect = {
    x: margin,
    y: 0.58 * height,
    width: width - 2 * margin,
    height: 0.33 * height,
  };
  const slots: Rect[] = [];
  const captions: ProgramLayout['captions'] = [];
  for (let i = 0; i < n; i += 1) {
    const center = margin + spacing * (i + 0.5);
    // Les silhouettes d'extrémité débordent un peu de leur colonne : on les ramène dans le canevas.
    const x = Math.min(width - slotWidth, Math.max(0, center - slotWidth / 2));
    slots.push({ x, y: slotY, width: slotWidth, height: slotHeight });
    const zoneWidth = spacing * 0.8;
    captions.push({
      name: {
        x: center - zoneWidth / 2,
        y: panel.y + 0.12 * panel.height,
        width: zoneWidth,
        height: 0.2 * panel.height,
      },
      levels: {
        x: center - zoneWidth / 2,
        y: panel.y + 0.42 * panel.height,
        width: zoneWidth,
        height: 0.3 * panel.height,
      },
    });
  }
  return {
    slots,
    panel,
    captions,
    title: { x: 0.03 * width, y: 0.05 * height, width: 0.35 * width, height: 0.14 * height },
    onAir: { x: 0.64 * width, y: 0.05 * height, width: 0.14 * width, height: 0.08 * height },
  };
}

/**
 * Partie de l'image source à copier dans une zone : même proportions que la zone, centrée sur `focusX` (0 à 1),
 * agrandie de `zoom` (≥ 1). Ne sort jamais de l'image.
 */
export function cropForSlot(
  source: { width: number; height: number },
  slot: Rect,
  zoom = 1,
  focusX = 0.5,
): Rect {
  const aspect = slot.width / slot.height;
  const z = Math.max(1, zoom);
  let cropHeight = source.height / z;
  let cropWidth = cropHeight * aspect;
  if (cropWidth > source.width / z) {
    cropWidth = source.width / z;
    cropHeight = cropWidth / aspect;
  }
  const clamp = (v: number, min: number, max: number): number => Math.min(max, Math.max(min, v));
  return {
    x: clamp(focusX * source.width - cropWidth / 2, 0, source.width - cropWidth),
    y: (source.height - cropHeight) / 2,
    width: cropWidth,
    height: cropHeight,
  };
}

/** Rectangle de destination pour couvrir un canevas avec une image sans la déformer (rogne ce qui dépasse). */
export function coverRect(
  image: { width: number; height: number },
  canvas: { width: number; height: number },
): Rect {
  const scale = Math.max(canvas.width / image.width, canvas.height / image.height);
  const width = image.width * scale;
  const height = image.height * scale;
  return { x: (canvas.width - width) / 2, y: (canvas.height - height) / 2, width, height };
}

/** Initiales d'un nom, pour l'emplacement d'un participant dont la caméra n'est pas (encore) reçue. */
export function initials(name: string): string {
  const parts = name
    .trim()
    .split(/\s+/)
    .filter((p) => p.length > 0);
  if (parts.length === 0) return '?';
  const first = Array.from(parts[0] ?? '')[0] ?? '?';
  const last = parts.length > 1 ? (Array.from(parts[parts.length - 1] ?? '')[0] ?? '') : '';
  return (first + last).toUpperCase();
}

/** Garde une courte mémoire des derniers niveaux audio (0 à 1) pour dessiner des barres qui défilent. */
export class LevelHistory {
  private readonly values: number[];
  private readonly size: number;

  constructor(size: number) {
    this.size = size;
    this.values = Array.from({ length: size }, () => 0);
  }

  push(level: number): void {
    this.values.push(Math.min(1, Math.max(0, Number.isFinite(level) ? level : 0)));
    if (this.values.length > this.size) this.values.shift();
  }

  get bars(): readonly number[] {
    return this.values;
  }
}
