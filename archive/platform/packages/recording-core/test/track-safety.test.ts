import { describe, expect, it } from 'vitest';
import {
  chunkSafety,
  evaluateTrack,
  type LocalCopy,
  type SafetyState,
  type UploadStatus,
} from '../src';
import { makeChunk } from './fixtures';

describe('chunkSafety', () => {
  it.each<[UploadStatus, LocalCopy, SafetyState]>([
    ['VERIFIED', 'DURABLE', 'SAFE'],
    ['VERIFIED', 'MEMORY', 'SAFE'],
    ['VERIFIED', 'NONE', 'SAFE'],
    ['UPLOADED', 'DURABLE', 'UPLOADING'],
    ['UPLOADED', 'MEMORY', 'AT_RISK'],
    ['UPLOADED', 'NONE', 'AT_RISK'],
    ['UPLOADING', 'DURABLE', 'UPLOADING'],
    ['UPLOADING', 'MEMORY', 'AT_RISK'],
    ['UPLOADING', 'NONE', 'AT_RISK'],
    ['NOT_UPLOADED', 'DURABLE', 'RECOVERABLE'],
    ['NOT_UPLOADED', 'MEMORY', 'AT_RISK'],
    ['NOT_UPLOADED', 'NONE', 'MISSING'],
    ['REJECTED', 'DURABLE', 'RECOVERABLE'],
    ['REJECTED', 'MEMORY', 'FAILED'],
    ['REJECTED', 'NONE', 'FAILED'],
  ])('%s + copie %s → %s', (uploadStatus, localCopy, expected) => {
    expect(chunkSafety({ uploadStatus, localCopy })).toBe(expected);
  });
});

describe('evaluateTrack', () => {
  const verified = (sequenceNumber: number) => makeChunk({ sequenceNumber });

  it('retourne SAFE quand tous les chunks sont vérifiés par le serveur', () => {
    const result = evaluateTrack([verified(0), verified(1), verified(2)], {
      expectedChunkCount: 3,
    });
    expect(result.state).toBe('SAFE');
    expect(result.counts.SAFE).toBe(3);
    expect(result.missingSequences).toEqual([]);
    expect(result.isFinal).toBe(true);
  });

  it('ne retourne pas SAFE si un chunk attend sa vérification', () => {
    const result = evaluateTrack([
      verified(0),
      makeChunk({ sequenceNumber: 1, uploadStatus: 'UPLOADED' }),
    ]);
    expect(result.state).toBe('UPLOADING');
  });

  it('retourne RECOVERABLE quand le serveur n’a pas tout mais la copie locale est durable', () => {
    const result = evaluateTrack([
      verified(0),
      makeChunk({ sequenceNumber: 1, uploadStatus: 'NOT_UPLOADED', localCopy: 'DURABLE' }),
    ]);
    expect(result.state).toBe('RECOVERABLE');
  });

  it('retourne AT_RISK si un chunk n’existe qu’en mémoire', () => {
    const result = evaluateTrack([
      verified(0),
      makeChunk({ sequenceNumber: 1, uploadStatus: 'NOT_UPLOADED', localCopy: 'MEMORY' }),
    ]);
    expect(result.state).toBe('AT_RISK');
  });

  it('détecte un trou dans la séquence et retourne MISSING', () => {
    const result = evaluateTrack([verified(0), verified(1), verified(4)]);
    expect(result.state).toBe('MISSING');
    expect(result.missingSequences).toEqual([2, 3]);
    expect(result.counts.MISSING).toBe(2);
    expect(result.expectedChunkCount).toBe(5);
    expect(result.isFinal).toBe(false);
  });

  it('détecte les chunks manquants en fin de piste quand le total attendu est connu', () => {
    const result = evaluateTrack([verified(0), verified(1)], { expectedChunkCount: 4 });
    expect(result.state).toBe('MISSING');
    expect(result.missingSequences).toEqual([2, 3]);
  });

  it('ne voit pas un trou en fin de piste tant que le total attendu est inconnu', () => {
    const result = evaluateTrack([verified(0), verified(1)]);
    expect(result.state).toBe('SAFE');
    expect(result.isFinal).toBe(false);
  });

  it('retient le pire état parmi les chunks', () => {
    const result = evaluateTrack([
      verified(0),
      makeChunk({ sequenceNumber: 1, uploadStatus: 'UPLOADING' }),
      makeChunk({ sequenceNumber: 2, uploadStatus: 'NOT_UPLOADED' }),
      makeChunk({ sequenceNumber: 3, uploadStatus: 'REJECTED', localCopy: 'NONE' }),
    ]);
    expect(result.state).toBe('FAILED');
    expect(result.counts).toEqual({
      SAFE: 1,
      UPLOADING: 1,
      RECOVERABLE: 1,
      AT_RISK: 0,
      FAILED: 1,
      MISSING: 0,
    });
  });

  it('classe MISSING avant FAILED quand les deux existent', () => {
    const result = evaluateTrack([
      verified(0),
      makeChunk({ sequenceNumber: 2, uploadStatus: 'REJECTED', localCopy: 'NONE' }),
    ]);
    expect(result.state).toBe('MISSING');
    expect(result.counts.FAILED).toBe(1);
  });

  it('retourne null, et pas SAFE, pour une piste sans aucun chunk', () => {
    const result = evaluateTrack([]);
    expect(result.state).toBeNull();
    expect(result.expectedChunkCount).toBe(0);
  });

  it('retourne MISSING pour une piste vide dont des chunks sont attendus', () => {
    const result = evaluateTrack([], { expectedChunkCount: 3 });
    expect(result.state).toBe('MISSING');
    expect(result.missingSequences).toEqual([0, 1, 2]);
  });

  it('évalue aussi les chunks au-delà du total attendu', () => {
    const result = evaluateTrack(
      [
        verified(0),
        makeChunk({ sequenceNumber: 1, uploadStatus: 'NOT_UPLOADED', localCopy: 'MEMORY' }),
      ],
      { expectedChunkCount: 1 },
    );
    expect(result.state).toBe('AT_RISK');
  });

  it('refuse des chunks de pistes différentes', () => {
    expect(() =>
      evaluateTrack([verified(0), makeChunk({ sequenceNumber: 1, trackId: 'autre' })]),
    ).toThrow(/une seule piste/);
  });

  it('refuse un numéro de séquence en double', () => {
    expect(() => evaluateTrack([verified(0), verified(0)])).toThrow(/en double/);
  });
});
