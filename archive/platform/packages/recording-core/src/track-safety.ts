import type { ChunkMetadata } from './chunk.ts';

/**
 * États de sécurité des données (master prompt §18). Du moins grave au plus grave.
 * Règles détaillées et limites : docs/recording.md.
 */
export const SAFETY_STATES = [
  'SAFE',
  'UPLOADING',
  'RECOVERABLE',
  'AT_RISK',
  'FAILED',
  'MISSING',
] as const;

export type SafetyState = (typeof SAFETY_STATES)[number];

const severity = (state: SafetyState): number => SAFETY_STATES.indexOf(state);

/** État d'un chunk présent dans le manifeste. */
export function chunkSafety(chunk: Pick<ChunkMetadata, 'uploadStatus' | 'localCopy'>): SafetyState {
  const { uploadStatus, localCopy } = chunk;
  switch (uploadStatus) {
    case 'VERIFIED':
      return 'SAFE';
    case 'REJECTED':
      return localCopy === 'DURABLE' ? 'RECOVERABLE' : 'FAILED';
    case 'UPLOADING':
    case 'UPLOADED':
      return localCopy === 'DURABLE' ? 'UPLOADING' : 'AT_RISK';
    case 'NOT_UPLOADED':
      if (localCopy === 'DURABLE') return 'RECOVERABLE';
      return localCopy === 'MEMORY' ? 'AT_RISK' : 'MISSING';
  }
}

export interface TrackSafety {
  /**
   * Pire état parmi les chunks et les trous de séquence.
   * `null` : aucun chunk et aucune attente, il n'y a rien à évaluer. Ne jamais l'afficher comme SAFE.
   */
  state: SafetyState | null;
  counts: Record<SafetyState, number>;
  /** Numéros de séquence absents du manifeste entre 0 et `expectedChunkCount - 1`. */
  missingSequences: number[];
  expectedChunkCount: number;
  /**
   * `true` si le nombre de chunks attendu était fourni (piste arrêtée).
   * Sinon il est déduit du plus grand numéro vu : un trou en fin de piste est invisible.
   */
  isFinal: boolean;
}

export interface EvaluateTrackOptions {
  expectedChunkCount?: number;
}

/**
 * Évalue la sécurité d'une piste à partir de son manifeste.
 * Lève une erreur si les chunks viennent de pistes différentes ou si un numéro de séquence
 * apparaît deux fois : c'est un bug de l'appelant, pas une donnée à interpréter.
 */
export function evaluateTrack(
  chunks: readonly ChunkMetadata[],
  options: EvaluateTrackOptions = {},
): TrackSafety {
  const trackIds = new Set(chunks.map((chunk) => chunk.trackId));
  if (trackIds.size > 1) {
    throw new Error(`evaluateTrack attend une seule piste, reçu : ${[...trackIds].join(', ')}`);
  }

  const bySequence = new Map<number, ChunkMetadata>();
  for (const chunk of chunks) {
    if (bySequence.has(chunk.sequenceNumber)) {
      throw new Error(`Numéro de séquence en double : ${String(chunk.sequenceNumber)}`);
    }
    bySequence.set(chunk.sequenceNumber, chunk);
  }

  const highestSequence = Math.max(-1, ...bySequence.keys());
  const expectedChunkCount = options.expectedChunkCount ?? highestSequence + 1;

  const counts: Record<SafetyState, number> = {
    SAFE: 0,
    UPLOADING: 0,
    RECOVERABLE: 0,
    AT_RISK: 0,
    FAILED: 0,
    MISSING: 0,
  };
  const missingSequences: number[] = [];

  for (let sequence = 0; sequence < expectedChunkCount; sequence++) {
    const chunk = bySequence.get(sequence);
    if (chunk) {
      counts[chunkSafety(chunk)]++;
    } else {
      counts.MISSING++;
      missingSequences.push(sequence);
    }
  }
  // Chunks au-delà du nombre attendu : on les évalue quand même plutôt que de les ignorer.
  for (const [sequence, chunk] of bySequence) {
    if (sequence >= expectedChunkCount) counts[chunkSafety(chunk)]++;
  }

  const present = SAFETY_STATES.filter((state) => counts[state] > 0);
  const state = present.reduce<SafetyState | null>(
    (worst, candidate) =>
      worst === null || severity(candidate) > severity(worst) ? candidate : worst,
    null,
  );

  return {
    state,
    counts,
    missingSequences,
    expectedChunkCount,
    isFinal: options.expectedChunkCount !== undefined,
  };
}
