/** Calculs de synthèse sur les relevés WebRTC d'un participant (fonctions pures, testées). */

export interface VideoSample {
  at: number;
  bytesSent: number | undefined;
  framesEncoded: number | undefined;
  totalEncodeTime: number | undefined;
  frameWidth: number | undefined;
  frameHeight: number | undefined;
  framesPerSecond: number | undefined;
  qualityLimitationReason: string | undefined;
  encoderImplementation: string | undefined;
  codec: string | undefined;
}

export interface ParticipantSummary {
  samples: number;
  codec: string | undefined;
  encoder: string | undefined;
  resolution: string | undefined;
  /** Débit moyen d'émission entre le premier et le dernier relevé, en kb/s. */
  avgBitrateKbps: number | undefined;
  avgFps: number | undefined;
  /** Temps moyen d'encodage par image, en ms. */
  avgEncodeMsPerFrame: number | undefined;
  limitationReasons: Record<string, number>;
}

const mean = (values: readonly number[]): number | undefined =>
  values.length === 0 ? undefined : values.reduce((a, b) => a + b, 0) / values.length;

const round = (value: number | undefined, digits = 1): number | undefined =>
  value === undefined ? undefined : Number(value.toFixed(digits));

export function summarizeVideo(samples: readonly VideoSample[]): ParticipantSummary {
  const first = samples.find((s) => s.bytesSent !== undefined);
  const last = [...samples].reverse().find((s) => s.bytesSent !== undefined);
  let avgBitrateKbps: number | undefined;
  let avgEncodeMsPerFrame: number | undefined;
  if (
    first &&
    last &&
    last.at > first.at &&
    first.bytesSent !== undefined &&
    last.bytesSent !== undefined
  ) {
    avgBitrateKbps =
      ((last.bytesSent - first.bytesSent) * 8) / ((last.at - first.at) / 1000) / 1000;
    if (
      first.framesEncoded !== undefined &&
      last.framesEncoded !== undefined &&
      first.totalEncodeTime !== undefined &&
      last.totalEncodeTime !== undefined &&
      last.framesEncoded > first.framesEncoded
    ) {
      avgEncodeMsPerFrame =
        ((last.totalEncodeTime - first.totalEncodeTime) /
          (last.framesEncoded - first.framesEncoded)) *
        1000;
    }
  }

  const limitationReasons: Record<string, number> = {};
  for (const s of samples) {
    const reason = s.qualityLimitationReason ?? 'inconnu';
    limitationReasons[reason] = (limitationReasons[reason] ?? 0) + 1;
  }

  const lastWithSize = [...samples].reverse().find((s) => s.frameWidth !== undefined);
  return {
    samples: samples.length,
    codec: samples.find((s) => s.codec !== undefined)?.codec,
    encoder: samples.find((s) => s.encoderImplementation !== undefined)?.encoderImplementation,
    resolution:
      lastWithSize?.frameWidth !== undefined && lastWithSize.frameHeight !== undefined
        ? `${String(lastWithSize.frameWidth)}x${String(lastWithSize.frameHeight)}`
        : undefined,
    avgBitrateKbps: round(avgBitrateKbps, 0),
    avgFps: round(mean(samples.flatMap((s) => s.framesPerSecond ?? [])), 1),
    avgEncodeMsPerFrame: round(avgEncodeMsPerFrame, 2),
    limitationReasons,
  };
}

/** CPU moyen d'un processus entre deux relevés du temps CPU cumulé, en % d'un cœur. */
export function cpuPercentOfCore(
  samples: readonly { atMs: number; cpuSeconds: number }[],
): number | undefined {
  const first = samples[0];
  const last = samples.at(-1);
  if (!first || !last || last.atMs <= first.atMs) return undefined;
  return round(((last.cpuSeconds - first.cpuSeconds) / ((last.atMs - first.atMs) / 1000)) * 100, 1);
}

export interface TimelinePoint {
  tSec: number;
  resolution: string;
  fps: number | undefined;
  kbps: number | undefined;
  limitation: string;
}

/** Chronologie des relevés : résolution, images/s et débit instantané entre deux relevés. */
export function timeline(samples: readonly VideoSample[]): TimelinePoint[] {
  const origin = samples[0]?.at;
  if (origin === undefined) return [];
  return samples.map((sample, index) => {
    const previous = samples[index - 1];
    let kbps: number | undefined;
    if (
      previous?.bytesSent !== undefined &&
      sample.bytesSent !== undefined &&
      sample.at > previous.at
    ) {
      kbps = Math.round(
        ((sample.bytesSent - previous.bytesSent) * 8) / ((sample.at - previous.at) / 1000) / 1000,
      );
    }
    return {
      tSec: Math.round((sample.at - origin) / 1000),
      resolution:
        sample.frameWidth !== undefined && sample.frameHeight !== undefined
          ? `${String(sample.frameWidth)}x${String(sample.frameHeight)}`
          : '?',
      fps: sample.framesPerSecond,
      kbps,
      limitation: sample.qualityLimitationReason ?? '?',
    };
  });
}

/** Premier instant (en secondes) où la résolution demandée est atteinte, sinon undefined. */
export function timeToResolution(
  points: readonly TimelinePoint[],
  resolution: string,
): number | undefined {
  return points.find((p) => p.resolution === resolution)?.tSec;
}
