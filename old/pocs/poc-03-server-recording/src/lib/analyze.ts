import { z } from 'zod';

const streamSchema = z.looseObject({
  codec_type: z.string(),
  codec_name: z.string().optional(),
  width: z.number().optional(),
  height: z.number().optional(),
  avg_frame_rate: z.string().optional(),
});

const ffprobeSchema = z.looseObject({
  streams: z.array(streamSchema),
  format: z.looseObject({
    format_name: z.string().optional(),
    duration: z.string().optional(),
    size: z.string().optional(),
    bit_rate: z.string().optional(),
  }),
});

export interface MediaSummary {
  kind: 'video' | 'audio';
  container: string | undefined;
  codec: string | undefined;
  width: number | undefined;
  height: number | undefined;
  fps: number | undefined;
  durationSec: number | undefined;
  bitrateKbps: number | undefined;
  sizeBytes: number | undefined;
}

export interface MediaExpectation {
  kind: 'video' | 'audio';
  expectedDurationSec: number;
  durationToleranceSec: number;
  minWidth?: number;
  minHeight?: number;
  minFps?: number;
  codecs?: readonly string[];
}

const toNumber = (value: string | undefined): number | undefined => {
  if (value === undefined) return undefined;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
};

/** "30000/1001" → 29.97, "0/0" → undefined. */
export function parseFrameRate(rate: string | undefined): number | undefined {
  if (rate === undefined) return undefined;
  const [numerator, denominator] = rate.split('/').map(Number);
  if (numerator === undefined || denominator === undefined || !denominator) return undefined;
  const fps = numerator / denominator;
  return Number.isFinite(fps) && fps > 0 ? fps : undefined;
}

/** Lit la sortie de `ffprobe -show_format -show_streams -of json`. */
export function parseFfprobe(json: unknown): MediaSummary {
  const probe = ffprobeSchema.parse(json);
  const stream =
    probe.streams.find((s) => s.codec_type === 'video') ??
    probe.streams.find((s) => s.codec_type === 'audio');
  if (!stream) throw new Error('Aucun flux audio ou vidéo dans la sortie ffprobe');

  const bitRate = toNumber(probe.format.bit_rate);
  return {
    kind: stream.codec_type === 'video' ? 'video' : 'audio',
    container: probe.format.format_name,
    codec: stream.codec_name,
    width: stream.width,
    height: stream.height,
    fps: parseFrameRate(stream.avg_frame_rate),
    durationSec: toNumber(probe.format.duration),
    bitrateKbps: bitRate === undefined ? undefined : bitRate / 1000,
    sizeBytes: toNumber(probe.format.size),
  };
}

/** Liste les écarts entre un fichier enregistré et ce qu'on en attend. Vide = conforme. */
export function checkAgainst(summary: MediaSummary, expected: MediaExpectation): string[] {
  const issues: string[] = [];

  if (summary.kind !== expected.kind) {
    issues.push(`type ${summary.kind}, attendu ${expected.kind}`);
  }
  if (
    expected.codecs &&
    (summary.codec === undefined || !expected.codecs.includes(summary.codec))
  ) {
    issues.push(`codec ${summary.codec ?? 'inconnu'}, attendu ${expected.codecs.join(' ou ')}`);
  }
  if (summary.durationSec === undefined) {
    issues.push('durée inconnue');
  } else if (
    Math.abs(summary.durationSec - expected.expectedDurationSec) > expected.durationToleranceSec
  ) {
    issues.push(
      `durée ${summary.durationSec.toFixed(1)} s, attendu ${String(expected.expectedDurationSec)} s ± ${String(expected.durationToleranceSec)} s`,
    );
  }
  if (expected.minWidth !== undefined && (summary.width ?? 0) < expected.minWidth) {
    issues.push(
      `largeur ${String(summary.width ?? 'inconnue')}, minimum ${String(expected.minWidth)}`,
    );
  }
  if (expected.minHeight !== undefined && (summary.height ?? 0) < expected.minHeight) {
    issues.push(
      `hauteur ${String(summary.height ?? 'inconnue')}, minimum ${String(expected.minHeight)}`,
    );
  }
  if (expected.minFps !== undefined && (summary.fps ?? 0) < expected.minFps) {
    issues.push(
      `${summary.fps?.toFixed(1) ?? 'inconnu'} images/s, minimum ${String(expected.minFps)}`,
    );
  }
  return issues;
}
