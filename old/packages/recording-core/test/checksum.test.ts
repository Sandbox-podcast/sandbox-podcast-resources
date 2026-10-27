import { describe, expect, it } from 'vitest';
import { matchesChecksum, sha256Hex } from '../src';

const encode = (text: string): Uint8Array<ArrayBuffer> => new TextEncoder().encode(text);

describe('sha256Hex', () => {
  it('retourne le vecteur de référence pour "abc"', async () => {
    expect(await sha256Hex(encode('abc'))).toBe(
      'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad',
    );
  });

  it('retourne le vecteur de référence pour une entrée vide', async () => {
    expect(await sha256Hex(encode(''))).toBe(
      'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    );
  });
});

describe('matchesChecksum', () => {
  const abc = 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad';

  it('accepte un checksum identique', async () => {
    expect(await matchesChecksum(encode('abc'), abc)).toBe(true);
  });

  it('accepte un checksum en majuscules', async () => {
    expect(await matchesChecksum(encode('abc'), abc.toUpperCase())).toBe(true);
  });

  it('refuse un octet modifié', async () => {
    expect(await matchesChecksum(encode('abd'), abc)).toBe(false);
  });
});
