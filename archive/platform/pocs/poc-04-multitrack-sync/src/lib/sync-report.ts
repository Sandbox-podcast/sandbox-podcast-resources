import {
  irregularIntervals,
  pairMarkers,
  summarizeOffsets,
  type OffsetSummary,
} from './markers.ts';

export interface TrackOnsets {
  participant: string;
  /** Heures des bips dans la ligne de temps du fichier audio (s). */
  audio: readonly number[];
  /** Heures des éclairs dans la ligne de temps du fichier vidéo (s). */
  video: readonly number[];
  /** Début de l'egress d'après son manifeste (ns depuis l'époque Unix), s'il est connu. */
  audioStartedAtNs?: number;
  videoStartedAtNs?: number;
}

export interface ParticipantSync {
  participant: string;
  audioMarkers: number;
  videoMarkers: number;
  audioIrregular: number;
  videoIrregular: number;
  /** Heure du bip moins heure de l'éclair, par repère. */
  audioMinusVideo: OffsetSummary | undefined;
  /** Même écart prédit par les manifestes (début vidéo − début audio), en ms. */
  predictedFromManifestsMs: number | undefined;
  /** Écart mesuré moins prédit : ce que les métadonnées seules ne savent pas corriger. */
  manifestErrorMs: number | undefined;
}

export interface CrossSync {
  participant: string;
  versus: string;
  video: OffsetSummary | undefined;
  audio: OffsetSummary | undefined;
}

export interface SyncReport {
  periodSec: number;
  participants: ParticipantSync[];
  cross: CrossSync[];
}

export interface ReportOptions {
  periodSec: number;
  /** Écart maximal entre deux repères pour les apparier (s). */
  maxPairGapSec?: number;
  /** Tolérance sur la période entre deux repères consécutifs (s). */
  intervalToleranceSec?: number;
}

const summarizePairs = (
  pairs: { a: number; b: number }[],
  sign: 1 | -1,
): OffsetSummary | undefined =>
  pairs.length >= 2
    ? summarizeOffsets(
        pairs.map((p) => p.a),
        pairs.map((p) => sign * (p.b - p.a)),
      )
    : undefined;

export function buildSyncReport(
  tracks: readonly TrackOnsets[],
  options: ReportOptions,
): SyncReport {
  const maxGap = options.maxPairGapSec ?? options.periodSec / 2;
  const tolerance = options.intervalToleranceSec ?? 0.5;

  const participants = tracks.map((track): ParticipantSync => {
    // Écart « bip − éclair » à l'instant (vidéo) du repère.
    const pairs = pairMarkers(track.video, track.audio, maxGap);
    const summary = summarizePairs(pairs, 1);
    const predicted =
      track.videoStartedAtNs !== undefined && track.audioStartedAtNs !== undefined
        ? (track.videoStartedAtNs - track.audioStartedAtNs) / 1e6
        : undefined;
    return {
      participant: track.participant,
      audioMarkers: track.audio.length,
      videoMarkers: track.video.length,
      audioIrregular: irregularIntervals(track.audio, options.periodSec, tolerance).length,
      videoIrregular: irregularIntervals(track.video, options.periodSec, tolerance).length,
      audioMinusVideo: summary,
      predictedFromManifestsMs:
        predicted === undefined ? undefined : Math.round(predicted * 100) / 100,
      manifestErrorMs:
        predicted === undefined || summary === undefined
          ? undefined
          : Math.round((summary.meanMs - predicted) * 100) / 100,
    };
  });

  const reference = tracks[0];
  const cross: CrossSync[] = [];
  if (reference) {
    for (const track of tracks.slice(1)) {
      cross.push({
        participant: track.participant,
        versus: reference.participant,
        video: summarizePairs(pairMarkers(reference.video, track.video, maxGap), 1),
        audio: summarizePairs(pairMarkers(reference.audio, track.audio, maxGap), 1),
      });
    }
  }
  return { periodSec: options.periodSec, participants, cross };
}

export interface SyncThresholds {
  /** Amplitude maximale (max − min) du décalage pendant la session, pour une série qui n'implique que de l'audio. */
  maxSpanMs: number;
  /**
   * Amplitude maximale quand la série implique de la vidéo : un repère vidéo n'est connu qu'à l'image
   * près (33,3 ms), donc l'écart entre deux séries vidéo peut valoir deux images sans aucun défaut.
   */
  maxVideoSpanMs: number;
  /** Dérive ajustée maximale entre le début et la fin de la session. */
  maxFittedDriftMs: number;
  /** Au moins ce nombre de repères appariés. */
  minMarkers: number;
}

/**
 * Seuils proposés (décision de l'agent, à valider par le propriétaire) : le son ne doit pas
 * précéder l'image de plus de 40 ms (EBU R37), et la dérive ajustée reste sous 20 ms.
 */
export const DEFAULT_THRESHOLDS: SyncThresholds = {
  maxSpanMs: 40,
  maxVideoSpanMs: 70,
  maxFittedDriftMs: 20,
  minMarkers: 10,
};

/** Liste des écarts aux seuils ; vide si tout est conforme. */
export function evaluateReport(
  report: SyncReport,
  thresholds: SyncThresholds = DEFAULT_THRESHOLDS,
): string[] {
  const issues: string[] = [];
  const check = (
    label: string,
    summary: OffsetSummary | undefined,
    involvesVideo: boolean,
  ): void => {
    if (!summary) {
      issues.push(`${label} : pas assez de repères appariés`);
      return;
    }
    if (summary.count < thresholds.minMarkers)
      issues.push(
        `${label} : ${String(summary.count)} repères, minimum ${String(thresholds.minMarkers)}`,
      );
    const maxSpan = involvesVideo ? thresholds.maxVideoSpanMs : thresholds.maxSpanMs;
    if (summary.spanMs > maxSpan)
      issues.push(`${label} : amplitude ${String(summary.spanMs)} ms > ${String(maxSpan)} ms`);
    if (Math.abs(summary.fittedDriftMs) > thresholds.maxFittedDriftMs)
      issues.push(
        `${label} : dérive ajustée ${String(summary.fittedDriftMs)} ms > ${String(thresholds.maxFittedDriftMs)} ms`,
      );
  };
  for (const p of report.participants) {
    check(`${p.participant} bip−éclair`, p.audioMinusVideo, true);
    if (p.audioIrregular > 0 || p.videoIrregular > 0)
      issues.push(
        `${p.participant} : ${String(p.audioIrregular)} intervalle(s) audio et ${String(p.videoIrregular)} vidéo hors période`,
      );
  }
  for (const c of report.cross) {
    check(`${c.participant} contre ${c.versus}, vidéo`, c.video, true);
    check(`${c.participant} contre ${c.versus}, audio`, c.audio, false);
  }
  return issues;
}
