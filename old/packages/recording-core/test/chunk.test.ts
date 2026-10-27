import { describe, expect, it } from 'vitest';
import { chunkMetadataSchema } from '../src';
import { makeChunk } from './fixtures';

describe('chunkMetadataSchema', () => {
  it('accepte des métadonnées valides', () => {
    expect(chunkMetadataSchema.safeParse(makeChunk()).success).toBe(true);
  });

  it.each([
    ['checksum trop court', { checksum: 'abc' }],
    ['checksum en majuscules', { checksum: 'BA7816BF'.padEnd(64, 'A') }],
    ['numéro de séquence négatif', { sequenceNumber: -1 }],
    ['numéro de séquence non entier', { sequenceNumber: 1.5 }],
    ['fin avant début', { startTimestampMs: 5000, endTimestampMs: 4000 }],
    ['identifiant de piste vide', { trackId: '' }],
    ['taille négative', { sizeBytes: -1 }],
    ['statut d’upload inconnu', { uploadStatus: 'DONE' }],
    ['copie locale inconnue', { localCopy: 'DISK' }],
  ])('refuse : %s', (_label, overrides) => {
    expect(chunkMetadataSchema.safeParse({ ...makeChunk(), ...overrides }).success).toBe(false);
  });

  it('refuse un champ inconnu', () => {
    expect(chunkMetadataSchema.safeParse({ ...makeChunk(), extra: true }).success).toBe(false);
  });

  it('refuse un champ obligatoire absent', () => {
    const withoutCodec = Object.fromEntries(
      Object.entries(makeChunk()).filter(([key]) => key !== 'codec'),
    );
    expect(chunkMetadataSchema.safeParse(withoutCodec).success).toBe(false);
  });
});
