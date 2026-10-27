import { z } from 'zod';

/** AC-TRANSCRIPT-001 : chaque segment a un locuteur, un début, une fin et un texte. */
export const transcriptSegmentSchema = z.strictObject({
  id: z.string().min(1),
  speakerId: z.string().min(1),
  startSec: z.number().min(0),
  endSec: z.number().min(0),
  text: z.string().max(5000),
});
export type TranscriptSegment = z.infer<typeof transcriptSegmentSchema>;

export interface TranscriptIssue {
  segmentId: string | null;
  message: string;
}

/**
 * Contrôles sur une suite de segments : fin après début, dans la durée réelle du média,
 * ordre chronologique, identifiants uniques, pas de chevauchement d'un même locuteur avec lui-même
 * (deux locuteurs différents peuvent parler en même temps).
 */
export function validateTranscript(
  segments: readonly TranscriptSegment[],
  mediaDurationSec: number,
): TranscriptIssue[] {
  const issues: TranscriptIssue[] = [];
  const seen = new Set<string>();
  const lastEndBySpeaker = new Map<string, number>();
  let previousStart = 0;
  for (const segment of segments) {
    const at = segment.id;
    if (seen.has(segment.id)) issues.push({ segmentId: at, message: 'identifiant en double' });
    seen.add(segment.id);
    if (segment.endSec <= segment.startSec)
      issues.push({ segmentId: at, message: 'la fin doit suivre le début' });
    if (segment.endSec > mediaDurationSec)
      issues.push({ segmentId: at, message: 'la fin dépasse la durée du média' });
    if (segment.startSec < previousStart)
      issues.push({ segmentId: at, message: 'segments non triés par début' });
    previousStart = Math.max(previousStart, segment.startSec);
    const lastEnd = lastEndBySpeaker.get(segment.speakerId);
    if (lastEnd !== undefined && segment.startSec < lastEnd)
      issues.push({ segmentId: at, message: 'chevauche un autre segment du même locuteur' });
    lastEndBySpeaker.set(segment.speakerId, Math.max(lastEnd ?? 0, segment.endSec));
  }
  return issues;
}

export interface AuditedChange {
  version: number;
  segmentId: string;
  field: 'text' | 'speakerId';
  before: string;
  after: string;
  actorId: string;
  at: number;
}

/**
 * Transcription versionnée. Une correction produit une nouvelle version complète ; l'historique
 * et le journal des changements restent. Le document ne contient qu'une référence au média :
 * il n'existe aucune opération qui le modifie (AC-TRANSCRIPT-003, 004).
 */
export interface TranscriptDocument {
  readonly id: string;
  readonly mediaRef: string;
  readonly mediaDurationSec: number;
  readonly version: number;
  readonly segments: readonly TranscriptSegment[];
  readonly history: readonly { version: number; segments: readonly TranscriptSegment[] }[];
  readonly changes: readonly AuditedChange[];
}

export type CreateResult =
  { ok: true; document: TranscriptDocument } | { ok: false; issues: TranscriptIssue[] };

export function createTranscript(input: {
  id: string;
  mediaRef: string;
  mediaDurationSec: number;
  segments: readonly TranscriptSegment[];
}): CreateResult {
  const parsed = z.array(transcriptSegmentSchema).safeParse(input.segments);
  if (!parsed.success) {
    return {
      ok: false,
      issues: parsed.error.issues.map((i) => ({ segmentId: null, message: i.message })),
    };
  }
  const issues = validateTranscript(parsed.data, input.mediaDurationSec);
  if (issues.length > 0) return { ok: false, issues };
  return {
    ok: true,
    document: {
      id: input.id,
      mediaRef: input.mediaRef,
      mediaDurationSec: input.mediaDurationSec,
      version: 1,
      segments: parsed.data,
      history: [{ version: 1, segments: parsed.data }],
      changes: [],
    },
  };
}

export interface Correction {
  segmentId: string;
  text?: string;
  speakerId?: string;
  actorId: string;
  at: number;
}

export type CorrectionResult =
  | { ok: true; document: TranscriptDocument }
  | { ok: false; reason: 'SEGMENT_NOT_FOUND' | 'NO_CHANGE' | 'INVALID'; message: string };

export function correctSegment(
  document: TranscriptDocument,
  correction: Correction,
): CorrectionResult {
  const index = document.segments.findIndex((s) => s.id === correction.segmentId);
  const current = document.segments[index];
  if (!current) return { ok: false, reason: 'SEGMENT_NOT_FOUND', message: 'segment introuvable' };
  const next: TranscriptSegment = {
    ...current,
    ...(correction.text === undefined ? {} : { text: correction.text }),
    ...(correction.speakerId === undefined ? {} : { speakerId: correction.speakerId }),
  };
  if (next.text === current.text && next.speakerId === current.speakerId)
    return { ok: false, reason: 'NO_CHANGE', message: 'aucune modification' };
  const parsed = transcriptSegmentSchema.safeParse(next);
  if (!parsed.success)
    return { ok: false, reason: 'INVALID', message: parsed.error.issues[0]?.message ?? 'invalide' };

  const version = document.version + 1;
  const segments = document.segments.map((s, i) => (i === index ? parsed.data : s));
  const issues = validateTranscript(segments, document.mediaDurationSec);
  if (issues.length > 0)
    return { ok: false, reason: 'INVALID', message: issues[0]?.message ?? 'invalide' };
  const changes: AuditedChange[] = [];
  if (next.text !== current.text)
    changes.push({
      version,
      segmentId: current.id,
      field: 'text',
      before: current.text,
      after: next.text,
      actorId: correction.actorId,
      at: correction.at,
    });
  if (next.speakerId !== current.speakerId)
    changes.push({
      version,
      segmentId: current.id,
      field: 'speakerId',
      before: current.speakerId,
      after: next.speakerId,
      actorId: correction.actorId,
      at: correction.at,
    });
  return {
    ok: true,
    document: {
      ...document,
      version,
      segments,
      history: [...document.history, { version, segments }],
      changes: [...document.changes, ...changes],
    },
  };
}

/** Segment à écouter pour un instant donné : celui qui le contient, sinon le plus proche dans la tolérance. */
export function findSegmentAt(
  segments: readonly TranscriptSegment[],
  timeSec: number,
  toleranceSec: number,
): TranscriptSegment | null {
  const containing = segments.find((s) => timeSec >= s.startSec && timeSec < s.endSec);
  if (containing) return containing;
  let best: TranscriptSegment | null = null;
  let bestDistance = Number.POSITIVE_INFINITY;
  for (const s of segments) {
    const distance = timeSec < s.startSec ? s.startSec - timeSec : timeSec - s.endSec;
    if (distance < bestDistance) {
      best = s;
      bestDistance = distance;
    }
  }
  return best && bestDistance <= toleranceSec ? best : null;
}

/** Position du lecteur quand on clique un segment : son début, avec une courte amorce (jamais avant 0). */
export function seekTimeFor(segment: TranscriptSegment, prerollSec = 0.5): number {
  return Math.max(0, segment.startSec - prerollSec);
}
