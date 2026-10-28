/**
 * Alignement de pistes enregistrées à partir de repères communs (voir ADR-0010).
 * Modèle : la position `f` dans le fichier d'une piste pour l'instant `T` de la ligne de temps commune est
 *   f = (T − offsetSec) × (1 + driftPpm × 10⁻⁶)
 * `offsetSec` est l'instant de la ligne de temps où le fichier commence (positif : le fichier commence plus
 * tard que la référence), `driftPpm` l'écart de vitesse de l'horloge du fichier par rapport à la référence.
 */

export interface LineFit {
  slope: number;
  intercept: number;
  maxResidual: number;
  rmsResidual: number;
}

/** Droite des moindres carrés `y = slope × x + intercept`. */
export function fitLine(xs: readonly number[], ys: readonly number[]): LineFit {
  const n = xs.length;
  if (n < 2 || ys.length !== n) throw new Error('Au moins deux points sont nécessaires');
  const meanX = xs.reduce((a, b) => a + b, 0) / n;
  const meanY = ys.reduce((a, b) => a + b, 0) / n;
  let sxx = 0;
  let sxy = 0;
  for (let i = 0; i < n; i += 1) {
    const dx = (xs[i] ?? 0) - meanX;
    sxx += dx * dx;
    sxy += dx * ((ys[i] ?? 0) - meanY);
  }
  if (sxx === 0) throw new Error('Les abscisses sont toutes identiques');
  const slope = sxy / sxx;
  const intercept = meanY - slope * meanX;
  let maxResidual = 0;
  let sumSquares = 0;
  for (let i = 0; i < n; i += 1) {
    const residual = (ys[i] ?? 0) - (slope * (xs[i] ?? 0) + intercept);
    maxResidual = Math.max(maxResidual, Math.abs(residual));
    sumSquares += residual * residual;
  }
  return { slope, intercept, maxResidual, rmsResidual: Math.sqrt(sumSquares / n) };
}

export interface MarkerPair {
  index: number;
  a: number;
  b: number;
}

/**
 * Apparie les repères de deux séries : pour chaque repère de `a`, le plus proche de `b` à moins de
 * `maxGapSec` (en cas d'égalité, le plus tardif). Un repère manquant n'en décale pas d'autres.
 */
export function pairMarkers(
  a: readonly number[],
  b: readonly number[],
  maxGapSec: number,
): MarkerPair[] {
  const pairs: MarkerPair[] = [];
  let cursor = 0;
  a.forEach((timeA, index) => {
    while (
      cursor + 1 < b.length &&
      Math.abs((b[cursor + 1] ?? 0) - timeA) <= Math.abs((b[cursor] ?? 0) - timeA)
    )
      cursor += 1;
    const candidate = b[cursor];
    if (candidate !== undefined && Math.abs(candidate - timeA) <= maxGapSec)
      pairs.push({ index, a: timeA, b: candidate });
  });
  return pairs;
}

export interface TrackAlignment {
  trackId: string;
  offsetSec: number;
  driftPpm: number;
  /** Nombre de repères utilisés et écart résiduel après ajustement (ms) : la confiance dans l'alignement. */
  markers: number;
  residualRmsMs: number;
}

export const IDENTITY: Pick<TrackAlignment, 'offsetSec' | 'driftPpm'> = {
  offsetSec: 0,
  driftPpm: 0,
};

/**
 * Alignement d'une piste sur la référence : on ajuste `fichier = (1 + d) × T − (1 + d) × offset` sur les
 * repères appariés (T = repère de la référence). Au moins `minMarkers` repères sont exigés.
 */
export function alignToReference(
  trackId: string,
  referenceOnsets: readonly number[],
  trackOnsets: readonly number[],
  options: { maxGapSec: number; minMarkers: number },
): TrackAlignment {
  const pairs = pairMarkers(referenceOnsets, trackOnsets, options.maxGapSec);
  if (pairs.length < options.minMarkers)
    throw new Error(
      `${trackId} : ${String(pairs.length)} repère(s) appariés, ${String(options.minMarkers)} exigés`,
    );
  const fit = fitLine(
    pairs.map((p) => p.a),
    pairs.map((p) => p.b),
  );
  return {
    trackId,
    offsetSec: -fit.intercept / fit.slope,
    driftPpm: (fit.slope - 1) * 1e6,
    markers: pairs.length,
    residualRmsMs: fit.rmsResidual * 1000,
  };
}

/** Position dans le fichier de l'instant `timelineSec` de la ligne de temps commune. */
export const filePosition = (
  alignment: Pick<TrackAlignment, 'offsetSec' | 'driftPpm'>,
  timelineSec: number,
): number => (timelineSec - alignment.offsetSec) * (1 + alignment.driftPpm * 1e-6);

/** Instant de la ligne de temps commune pour une position dans le fichier (inverse de `filePosition`). */
export const timelinePosition = (
  alignment: Pick<TrackAlignment, 'offsetSec' | 'driftPpm'>,
  fileSec: number,
): number => fileSec / (1 + alignment.driftPpm * 1e-6) + alignment.offsetSec;
