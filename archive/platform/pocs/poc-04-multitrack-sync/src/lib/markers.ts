/**
 * Mesure de la synchronisation entre pistes à partir de repères connus.
 * La source de test publie, toutes les `periodSec` secondes, un éclair blanc à l'image et un bip
 * à l'oreille au même instant. On retrouve ces repères dans chaque fichier enregistré ; l'écart
 * entre l'heure de l'éclair et celle du bip donne le décalage audio/vidéo, et la façon dont ces
 * écarts évoluent pendant la session donne la dérive.
 */

export interface Sample {
  /** Temps dans la ligne de temps du fichier, en secondes. */
  t: number;
  value: number;
}

export interface OnsetOptions {
  /** Seuil de déclenchement (dB pour l'audio, luminance 0-255 pour la vidéo). */
  threshold: number;
  /** Deux détections plus proches que cet intervalle (s) sont la même impulsion. */
  minGapSec: number;
}

/** Front montant : premier échantillon au-dessus du seuil, après être passé sous le seuil. */
export function detectOnsets(series: readonly Sample[], options: OnsetOptions): number[] {
  const onsets: number[] = [];
  let armed = true;
  let lastOnset = Number.NEGATIVE_INFINITY;
  for (const sample of series) {
    if (sample.value >= options.threshold) {
      if (armed && sample.t - lastOnset >= options.minGapSec) {
        onsets.push(sample.t);
        lastOnset = sample.t;
      }
      armed = false;
    } else {
      armed = true;
    }
  }
  return onsets;
}

/**
 * Étendue (s) de l'énergie autour de chaque repère : de la première à la dernière valeur au-dessus du seuil
 * dans la fenêtre [repère − avant, repère + après]. Un bip de 100 ms reste à 100 ms ; trois bips décalés
 * donnent une étendue plus large : c'est la mesure de la qualité d'un alignement.
 */
export function markerExtents(
  series: readonly Sample[],
  onsets: readonly number[],
  options: { threshold: number; beforeSec: number; afterSec: number },
): number[] {
  return onsets.map((onset) => {
    let first = Number.POSITIVE_INFINITY;
    let last = Number.NEGATIVE_INFINITY;
    for (const sample of series) {
      if (sample.t < onset - options.beforeSec || sample.t > onset + options.afterSec) continue;
      if (sample.value < options.threshold) continue;
      first = Math.min(first, sample.t);
      last = Math.max(last, sample.t);
    }
    return last >= first ? last - first : 0;
  });
}

export interface LineFit {
  slope: number;
  intercept: number;
  /** Plus grand écart absolu à la droite. */
  maxResidual: number;
  rmsResidual: number;
  /** Erreur-type de la pente (0 pour moins de 3 points) : l'incertitude de la dérive mesurée. */
  slopeStdErr: number;
}

/** Droite des moindres carrés `y = slope * x + intercept`. */
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
  const slopeStdErr = n > 2 ? Math.sqrt(sumSquares / (n - 2) / sxx) : 0;
  return { slope, intercept, maxResidual, rmsResidual: Math.sqrt(sumSquares / n), slopeStdErr };
}

export interface MarkerPair {
  /** Numéro du repère dans la première série (ordre d'apparition). */
  index: number;
  a: number;
  b: number;
}

/**
 * Apparie les repères de deux séries : pour chaque repère de `a`, le plus proche de `b` à moins
 * de `maxGapSec`. Un repère manquant d'un côté n'est pas apparié (et n'en décale pas d'autres).
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

/** Intervalles entre repères qui s'écartent de la période attendue de plus de `toleranceSec`. */
export function irregularIntervals(
  onsets: readonly number[],
  periodSec: number,
  toleranceSec: number,
): { index: number; intervalSec: number }[] {
  const irregular: { index: number; intervalSec: number }[] = [];
  for (let i = 1; i < onsets.length; i += 1) {
    const intervalSec = (onsets[i] ?? 0) - (onsets[i - 1] ?? 0);
    if (Math.abs(intervalSec - periodSec) > toleranceSec) irregular.push({ index: i, intervalSec });
  }
  return irregular;
}

export interface OffsetSummary {
  count: number;
  meanMs: number;
  minMs: number;
  maxMs: number;
  /** Amplitude totale observée (max − min). */
  spanMs: number;
  /** Dérive ajustée sur la session, en parties par million (1 ppm = 3,6 ms par heure). */
  slopePpm: number;
  /** Incertitude (erreur-type) de la pente, en ppm : une dérive de l'ordre de 2 fois cette valeur n'est pas établie. */
  slopeStdErrPpm: number;
  /** Écart entre la droite ajustée à la fin et au début de la session, en ms. */
  fittedDriftMs: number;
  rmsResidualMs: number;
  /** Dérive extrapolée à 2 heures d'après la pente ajustée : une extrapolation, pas une mesure. */
  projectedDriftMs2h: number;
  sessionSec: number;
}

/**
 * Résume une série de décalages (en secondes) relevés à des instants donnés (en secondes) :
 * valeur moyenne, amplitude, dérive ajustée en ppm.
 */
export function summarizeOffsets(
  timesSec: readonly number[],
  offsetsSec: readonly number[],
): OffsetSummary {
  const fit = fitLine(timesSec, offsetsSec);
  const ms = offsetsSec.map((o) => o * 1000);
  const first = timesSec[0] ?? 0;
  const last = timesSec[timesSec.length - 1] ?? 0;
  const sessionSec = last - first;
  const round = (value: number): number => Math.round(value * 100) / 100;
  return {
    count: offsetsSec.length,
    meanMs: round(ms.reduce((a, b) => a + b, 0) / ms.length),
    minMs: round(Math.min(...ms)),
    maxMs: round(Math.max(...ms)),
    spanMs: round(Math.max(...ms) - Math.min(...ms)),
    slopePpm: round(fit.slope * 1e6),
    slopeStdErrPpm: round(fit.slopeStdErr * 1e6),
    fittedDriftMs: round(fit.slope * sessionSec * 1000),
    rmsResidualMs: round(fit.rmsResidual * 1000),
    projectedDriftMs2h: round(fit.slope * 7200 * 1000),
    sessionSec: round(sessionSec),
  };
}
