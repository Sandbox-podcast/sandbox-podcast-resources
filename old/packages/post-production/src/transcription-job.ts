import { z } from 'zod';
import {
  createTranscript,
  transcriptSegmentSchema,
  type TranscriptDocument,
  type TranscriptSegment,
} from './transcript.ts';

/**
 * Abstraction du fournisseur de transcription : le domaine ne dépend d'aucun fournisseur.
 * Un fournisseur retourne des segments bruts, qui sont validés avant d'être acceptés.
 */
export interface TranscriptionProvider {
  readonly name: string;
  transcribe(request: { mediaRef: string; mediaDurationSec: number }): Promise<unknown>;
}

export type JobStatus = 'QUEUED' | 'RUNNING' | 'SUCCEEDED' | 'FAILED_RETRYABLE' | 'FAILED_FINAL';

export interface TranscriptionJob {
  readonly id: string;
  readonly mediaRef: string;
  readonly mediaDurationSec: number;
  readonly status: JobStatus;
  readonly attempts: number;
  /** Instant (ms) avant lequel un nouvel essai est refusé. */
  readonly nextAttemptAtMs: number;
  readonly lastError: string | null;
  readonly document: TranscriptDocument | null;
  /** Toujours vrai : l'état de la transcription n'a aucun effet sur l'accès au média (AC-TRANSCRIPT-005). */
  readonly mediaAccessible: true;
}

export interface RetryPolicy {
  maxAttempts: number;
  baseDelayMs: number;
  maxDelayMs: number;
}

export const DEFAULT_RETRY: RetryPolicy = {
  maxAttempts: 4,
  baseDelayMs: 30_000,
  maxDelayMs: 600_000,
};

export const newTranscriptionJob = (input: {
  id: string;
  mediaRef: string;
  mediaDurationSec: number;
}): TranscriptionJob => ({
  ...input,
  status: 'QUEUED',
  attempts: 0,
  nextAttemptAtMs: 0,
  lastError: null,
  document: null,
  mediaAccessible: true,
});

const rawSchema = z.array(transcriptSegmentSchema);

export type AttemptResult =
  | { kind: 'RAN'; job: TranscriptionJob }
  | { kind: 'TOO_EARLY'; retryAtMs: number }
  | { kind: 'NOT_RUNNABLE'; status: JobStatus };

/**
 * Un essai de transcription. La sortie du fournisseur est validée contre le schéma et la durée
 * réelle du média avant d'être acceptée ; sinon l'essai échoue comme n'importe quelle panne.
 * Délai exponentiel entre les essais, nombre d'essais borné, échec final explicite.
 */
export async function attemptTranscription(
  job: TranscriptionJob,
  provider: TranscriptionProvider,
  nowMs: number,
  policy: RetryPolicy = DEFAULT_RETRY,
): Promise<AttemptResult> {
  if (job.status === 'SUCCEEDED' || job.status === 'FAILED_FINAL')
    return { kind: 'NOT_RUNNABLE', status: job.status };
  if (nowMs < job.nextAttemptAtMs) return { kind: 'TOO_EARLY', retryAtMs: job.nextAttemptAtMs };

  const attempts = job.attempts + 1;
  const fail = (message: string): AttemptResult => {
    const final = attempts >= policy.maxAttempts;
    const delay = Math.min(policy.maxDelayMs, policy.baseDelayMs * 2 ** (attempts - 1));
    return {
      kind: 'RAN',
      job: {
        ...job,
        status: final ? 'FAILED_FINAL' : 'FAILED_RETRYABLE',
        attempts,
        nextAttemptAtMs: final ? job.nextAttemptAtMs : nowMs + delay,
        lastError: message,
      },
    };
  };

  let raw: unknown;
  try {
    raw = await provider.transcribe({
      mediaRef: job.mediaRef,
      mediaDurationSec: job.mediaDurationSec,
    });
  } catch (error) {
    return fail(`${provider.name} : ${error instanceof Error ? error.message : String(error)}`);
  }
  const parsed = rawSchema.safeParse(raw);
  if (!parsed.success)
    return fail(`${provider.name} : sortie invalide (${parsed.error.issues[0]?.message ?? '?'})`);
  const created = createTranscript({
    id: `transcript-${job.id}`,
    mediaRef: job.mediaRef,
    mediaDurationSec: job.mediaDurationSec,
    segments: parsed.data,
  });
  if (!created.ok)
    return fail(`${provider.name} : sortie incohérente (${created.issues[0]?.message ?? '?'})`);
  return {
    kind: 'RAN',
    job: {
      ...job,
      status: 'SUCCEEDED',
      attempts,
      lastError: null,
      document: created.document,
    },
  };
}

/** Relance manuelle d'un échec final : repart de zéro essai, sans toucher au média. */
export const resetJob = (job: TranscriptionJob): TranscriptionJob =>
  job.status === 'FAILED_FINAL'
    ? { ...job, status: 'QUEUED', attempts: 0, nextAttemptAtMs: 0, lastError: null }
    : job;

/**
 * Faux fournisseur déterministe, pour les tests et les démonstrations : produit des tours de
 * parole réguliers entre les locuteurs donnés. Ce n'est PAS une transcription de l'audio.
 */
export class ScriptedProvider implements TranscriptionProvider {
  readonly name = 'scripted';
  calls = 0;
  private readonly failures: (Error | null)[];
  private readonly output: (mediaDurationSec: number) => unknown;

  constructor(options: {
    speakers: readonly string[];
    turnSec?: number;
    /** Une entrée par appel : une erreur à lever, ou `null` pour réussir. */
    failures?: readonly (Error | null)[];
    output?: (mediaDurationSec: number) => unknown;
  }) {
    this.failures = [...(options.failures ?? [])];
    const turnSec = options.turnSec ?? 20;
    this.output =
      options.output ??
      ((duration) => {
        const segments: TranscriptSegment[] = [];
        for (let start = 0, i = 0; start + turnSec <= duration; start += turnSec, i += 1) {
          segments.push({
            id: `seg-${String(i + 1)}`,
            speakerId: options.speakers[i % options.speakers.length] ?? 'inconnu',
            startSec: start,
            endSec: start + turnSec,
            text: `Tour de parole ${String(i + 1)}`,
          });
        }
        return segments;
      });
  }

  transcribe(request: { mediaDurationSec: number }): Promise<unknown> {
    this.calls += 1;
    const failure = this.failures.shift();
    if (failure) return Promise.reject(failure);
    return Promise.resolve(this.output(request.mediaDurationSec));
  }
}
