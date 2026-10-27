import { describe, expect, it } from 'vitest';
import {
  detectOnsets,
  markerExtents,
  fitLine,
  irregularIntervals,
  pairMarkers,
  summarizeOffsets,
  type Sample,
} from '../src/lib/markers.ts';
import {
  DEFAULT_THRESHOLDS,
  buildSyncReport,
  evaluateReport,
  type TrackOnsets,
} from '../src/lib/sync-report.ts';

const range = (n: number, from = 1): number[] => Array.from({ length: n }, (_, i) => i + from);

/** Série à `stepSec` avec des impulsions de `widthSec` aux instants donnés. */
function pulses(
  onsets: readonly number[],
  widthSec: number,
  stepSec: number,
  endSec: number,
  low = 0,
  high = 1,
): Sample[] {
  const series: Sample[] = [];
  for (let t = 0; t < endSec; t += stepSec) {
    const inside = onsets.some((o) => t >= o - 1e-9 && t < o + widthSec);
    series.push({ t: Math.round(t * 1e6) / 1e6, value: inside ? high : low });
  }
  return series;
}

describe('detectOnsets', () => {
  it('trouve le premier échantillon au-dessus du seuil de chaque impulsion', () => {
    const series = pulses([10, 20, 30.0125], 0.1, 0.0025, 40);
    const found = detectOnsets(series, { threshold: 0.5, minGapSec: 1 });
    expect(found).toEqual([10, 20, 30.0125]);
  });

  it('ne compte qu’une fois une impulsion hachée', () => {
    const series: Sample[] = [
      { t: 10, value: 1 },
      { t: 10.01, value: 0 },
      { t: 10.02, value: 1 },
      { t: 10.03, value: 0 },
      { t: 20, value: 1 },
    ];
    expect(detectOnsets(series, { threshold: 0.5, minGapSec: 1 })).toEqual([10, 20]);
  });

  it('ignore le bruit sous le seuil et ne rend rien sans impulsion', () => {
    const noise = pulses([], 0.1, 0.01, 5, 0.2, 0.2);
    expect(detectOnsets(noise, { threshold: 0.5, minGapSec: 1 })).toEqual([]);
  });

  it('un signal déjà au-dessus du seuil au départ compte comme un repère', () => {
    expect(
      detectOnsets(
        [
          { t: 0, value: 1 },
          { t: 0.1, value: 1 },
        ],
        { threshold: 0.5, minGapSec: 1 },
      ),
    ).toEqual([0]);
  });

  it('un échantillon exactement au seuil déclenche', () => {
    expect(
      detectOnsets(
        [
          { t: 1, value: 0 },
          { t: 2, value: 0.5 },
        ],
        { threshold: 0.5, minGapSec: 1 },
      ),
    ).toEqual([2]);
  });

  it('une impulsion plus longue que l’intervalle minimal ne compte qu’une fois', () => {
    const series = pulses([10], 3, 0.5, 20);
    expect(detectOnsets(series, { threshold: 0.5, minGapSec: 1 })).toEqual([10]);
  });

  it('une impulsion trop proche de la précédente est la même (intervalle minimal)', () => {
    const series: Sample[] = [
      { t: 10, value: 1 },
      { t: 10.1, value: 0 },
      { t: 10.5, value: 1 },
      { t: 10.6, value: 0 },
      { t: 12, value: 1 },
    ];
    expect(detectOnsets(series, { threshold: 0.5, minGapSec: 1 })).toEqual([10, 12]);
  });
});

describe('markerExtents', () => {
  const opts = { threshold: 0.5, beforeSec: 0.2, afterSec: 1 };

  it('mesure l’étendue d’un bip isolé', () => {
    const series = pulses([10, 20], 0.1, 0.0025, 30);
    const [first, second] = markerExtents(series, [10, 20], opts);
    expect(first).toBeCloseTo(0.0975, 3);
    expect(second).toBeCloseTo(0.0975, 3);
  });

  it('trois bips décalés donnent une étendue plus large que trois bips alignés', () => {
    const aligned = pulses([10, 10, 10], 0.1, 0.0025, 20);
    const spread = pulses([10, 10.12, 10.29], 0.1, 0.0025, 20);
    const [narrow] = markerExtents(aligned, [10], opts);
    const [wide] = markerExtents(spread, [10], opts);
    expect(narrow).toBeCloseTo(0.0975, 3);
    expect(wide).toBeCloseTo(0.3875, 3);
  });

  it('ignore l’énergie hors de la fenêtre et rend 0 sans énergie', () => {
    const series = pulses([10, 12], 0.1, 0.0025, 20);
    expect(markerExtents(series, [10], opts)[0]).toBeCloseTo(0.0975, 3);
    expect(markerExtents(series, [15], opts)).toEqual([0]);
    expect(markerExtents(series, [], opts)).toEqual([]);
  });
});

describe('fitLine', () => {
  it('retrouve la pente et l’ordonnée d’une droite exacte', () => {
    const fit = fitLine([0, 10, 20, 30], [5, 7, 9, 11]);
    expect(fit.slope).toBeCloseTo(0.2, 12);
    expect(fit.intercept).toBeCloseTo(5, 12);
    expect(fit.maxResidual).toBeCloseTo(0, 12);
  });

  it('mesure l’écart à la droite', () => {
    const fit = fitLine([0, 1, 2, 3, 4], [0, 1, 2, 3, 10]);
    expect(fit.maxResidual).toBeGreaterThan(1);
    expect(fit.rmsResidual).toBeGreaterThan(0.5);
  });

  it('refuse les cas dégénérés', () => {
    expect(() => fitLine([1], [1])).toThrow(/deux points/);
    expect(() => fitLine([1, 1], [1, 2])).toThrow(/identiques/);
    expect(() => fitLine([1, 2], [1])).toThrow(/deux points/);
  });
});

describe('pairMarkers', () => {
  it('apparie par proximité, sans décaler les suivants quand un repère manque', () => {
    const a = [10, 20, 30, 40];
    const b = [10.03, 30.03, 40.03];
    const pairs = pairMarkers(a, b, 5);
    expect(pairs.map((p) => [p.index, p.a, p.b])).toEqual([
      [0, 10, 10.03],
      [2, 30, 30.03],
      [3, 40, 40.03],
    ]);
  });

  it('n’apparie pas au-delà de l’écart maximal', () => {
    expect(pairMarkers([10, 20], [30, 40], 5)).toEqual([]);
  });

  it('en cas d’égalité de distance, retient le repère le plus tardif', () => {
    expect(pairMarkers([15], [10, 20], 6).map((p) => p.b)).toEqual([20]);
  });

  it('gère un décalage constant de plusieurs secondes sous la limite', () => {
    const pairs = pairMarkers([10, 20, 30], [12.5, 22.5, 32.5], 4);
    expect(pairs).toHaveLength(3);
    expect(pairs.every((p) => Math.abs(p.b - p.a - 2.5) < 1e-9)).toBe(true);
  });
});

describe('irregularIntervals', () => {
  it('signale un repère manquant ou en avance', () => {
    expect(irregularIntervals([10, 20, 40, 50], 10, 0.5)).toEqual([{ index: 2, intervalSec: 20 }]);
    expect(irregularIntervals([10, 20, 24, 30], 10, 0.5)).toHaveLength(2);
  });

  it('un intervalle exactement à la tolérance est accepté', () => {
    expect(irregularIntervals([10, 20.5], 10, 0.5)).toEqual([]);
  });

  it('accepte la tolérance', () => {
    expect(irregularIntervals([10, 20.4, 30.2], 10, 0.5)).toEqual([]);
    expect(irregularIntervals([10, 20.6], 10, 0.5)).toHaveLength(1);
  });
});

describe('summarizeOffsets', () => {
  const times = range(180).map((k) => k * 10);

  it('mesure un décalage constant sans dérive', () => {
    const summary = summarizeOffsets(
      times,
      times.map(() => 0.035),
    );
    expect(summary.meanMs).toBe(35);
    expect(summary.spanMs).toBe(0);
    expect(summary.slopePpm).toBe(0);
    expect(summary.fittedDriftMs).toBe(0);
  });

  it('retrouve une dérive de 50 ppm (180 ms par heure) et l’extrapole', () => {
    const summary = summarizeOffsets(
      times,
      times.map((t) => 0.02 + t * 50e-6),
    );
    expect(summary.slopePpm).toBeCloseTo(50, 1);
    expect(summary.fittedDriftMs).toBeCloseTo(89.55, 1);
    expect(summary.projectedDriftMs2h).toBeCloseTo(360, 0);
    expect(summary.spanMs).toBeCloseTo(89.55, 1);
    expect(summary.sessionSec).toBe(1790);
  });

  it('donne l’incertitude de la pente : nulle sur une droite exacte, positive avec du bruit', () => {
    expect(
      summarizeOffsets(
        times,
        times.map((t) => 0.02 + t * 50e-6),
      ).slopeStdErrPpm,
    ).toBe(0);
    const noisy = summarizeOffsets(
      times,
      times.map((t, i) => 0.02 + t * 50e-6 + (i % 2 === 0 ? 0.005 : -0.005)),
    );
    // Bruit de 5 ms sur 180 points espacés de 10 s : sigma / racine(somme des carrés des écarts de t) ≈ 0,72 ppm.
    expect(noisy.slopeStdErrPpm).toBeGreaterThan(0.6);
    expect(noisy.slopeStdErrPpm).toBeLessThan(0.85);
  });

  it('distingue une dérive d’un décalage qui oscille', () => {
    const summary = summarizeOffsets(
      times,
      times.map((_, i) => (i % 2 === 0 ? 0.01 : -0.01)),
    );
    expect(Math.abs(summary.slopePpm)).toBeLessThan(1);
    expect(summary.spanMs).toBe(20);
    expect(summary.rmsResidualMs).toBeCloseTo(10, 0);
  });
});

describe('buildSyncReport et évaluation', () => {
  const marks = range(20).map((k) => k * 10);
  const track = (
    participant: string,
    shift: number,
    driftPpm: number,
    avMs: number,
  ): TrackOnsets => ({
    participant,
    video: marks.map((t) => t + shift + t * driftPpm * 1e-6),
    audio: marks.map((t) => t + shift + avMs / 1000 + t * driftPpm * 1e-6),
  });

  it('une session synchronisée respecte les seuils', () => {
    const report = buildSyncReport(
      [track('a', 0.1, 0, 30), track('b', 0.35, 0, 30), track('c', 0.2, 0, 30)],
      { periodSec: 10 },
    );
    expect(evaluateReport(report)).toEqual([]);
    expect(report.participants[0]?.audioMinusVideo?.meanMs).toBe(30);
    expect(report.cross).toHaveLength(2);
    expect(report.cross[0]?.video?.meanMs).toBe(250);
  });

  it('détecte une dérive audio/vidéo propre à un participant', () => {
    const drifting: TrackOnsets = {
      participant: 'b',
      video: marks.map((t) => t + 0.1),
      audio: marks.map((t) => t + 0.1 + 0.03 + t * 200e-6),
    };
    const report = buildSyncReport([track('a', 0.1, 0, 30), drifting], { periodSec: 10 });
    const issues = evaluateReport(report);
    expect(issues.some((i) => i.startsWith('b bip−éclair') && i.includes('dérive ajustée'))).toBe(
      true,
    );
    expect(issues.some((i) => i.startsWith('a bip−éclair'))).toBe(false);
  });

  it('détecte aussi une dérive négative (le son avance sur l’image)', () => {
    const early: TrackOnsets = {
      participant: 'b',
      video: marks,
      audio: marks.map((t) => t - t * 200e-6),
    };
    const issues = evaluateReport(buildSyncReport([early], { periodSec: 10 }));
    expect(issues.some((i) => i.includes('dérive ajustée -'))).toBe(true);
  });

  it('détecte une dérive entre deux participants', () => {
    const report = buildSyncReport([track('a', 0, 0, 0), track('b', 0, 150, 0)], { periodSec: 10 });
    const issues = evaluateReport(report);
    expect(issues.some((i) => i.includes('b contre a, vidéo : dérive ajustée'))).toBe(true);
    expect(issues.some((i) => i.includes('b contre a, audio : dérive ajustée'))).toBe(true);
  });

  it('détecte une amplitude excessive même sans pente', () => {
    const jittery = (jitterMs: number): TrackOnsets => ({
      participant: 'a',
      video: marks,
      audio: marks.map((t, i) => t + (i % 2 === 0 ? 0 : jitterMs / 1000)),
    });
    expect(evaluateReport(buildSyncReport([jittery(80)], { periodSec: 10 }))).toEqual([
      expect.stringContaining('amplitude 80 ms > 70 ms'),
    ]);
  });

  it('l’amplitude entre deux séries vidéo tolère deux images, pas entre deux séries audio', () => {
    const wobble = (kind: 'audio' | 'video'): TrackOnsets[] => {
      const base = { participant: 'a', video: marks, audio: marks };
      const other = { participant: 'b', video: marks, audio: marks };
      const shifted = marks.map((t, i) => t + (i % 2 === 0 ? 0 : 0.067));
      return [base, { ...other, [kind]: shifted }];
    };
    const video = evaluateReport(buildSyncReport(wobble('video'), { periodSec: 10 }));
    expect(video.filter((issue) => issue.includes('amplitude'))).toEqual([]);
    const audio = evaluateReport(buildSyncReport(wobble('audio'), { periodSec: 10 }));
    expect(audio).toEqual([expect.stringContaining('b contre a, audio : amplitude 67 ms > 40 ms')]);
  });

  it('signale trop peu de repères et un intervalle irrégulier', () => {
    const few: TrackOnsets = { participant: 'a', video: [10, 20, 30], audio: [10, 20, 30] };
    expect(evaluateReport(buildSyncReport([few], { periodSec: 10 }))[0]).toMatch(
      /3 repères, minimum 10/,
    );
    const gap: TrackOnsets = {
      participant: 'a',
      video: marks.filter((t) => t !== 100),
      audio: marks,
    };
    const issues = evaluateReport(buildSyncReport([gap], { periodSec: 10 }));
    expect(issues.some((i) => i.includes('1 vidéo hors période'))).toBe(true);
  });

  it('signale l’absence de repères appariés', () => {
    const none: TrackOnsets = { participant: 'a', video: [], audio: [] };
    expect(evaluateReport(buildSyncReport([none], { periodSec: 10 }))).toEqual([
      'a bip−éclair : pas assez de repères appariés',
    ]);
  });

  it('compare l’alignement par manifestes à l’alignement par repères', () => {
    // La vidéo a commencé 120 ms après l'audio d'après les manifestes : les repères vidéo
    // arrivent donc 120 ms plus tôt dans leur fichier, soit « bip − éclair » = +120 ms.
    const t: TrackOnsets = {
      participant: 'a',
      video: marks,
      audio: marks.map((m) => m + 0.13),
      videoStartedAtNs: 1_000_000_000_000 + 120_000_000,
      audioStartedAtNs: 1_000_000_000_000,
    };
    const participant = buildSyncReport([t], { periodSec: 10 }).participants[0];
    expect(participant?.predictedFromManifestsMs).toBe(120);
    expect(participant?.audioMinusVideo?.meanMs).toBe(130);
    expect(participant?.manifestErrorMs).toBe(10);
  });

  it('les seuils par défaut sont ceux documentés', () => {
    expect(DEFAULT_THRESHOLDS).toEqual({
      maxSpanMs: 40,
      maxVideoSpanMs: 70,
      maxFittedDriftMs: 20,
      minMarkers: 10,
    });
  });
});
