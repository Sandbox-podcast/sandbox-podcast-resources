import { describe, expect, it } from 'vitest';
import { extractAnnexB } from '../src/lib/mp4-recovery.ts';

const u32 = (value: number): number[] => [
  (value >>> 24) & 0xff,
  (value >>> 16) & 0xff,
  (value >>> 8) & 0xff,
  value & 0xff,
];
const ascii = (text: string): number[] => Array.from(text, (char) => char.charCodeAt(0));

/** Fichier tronqué tel que laissé par Egress : ftyp, free, puis mdat de taille 0. */
function truncatedMp4(nals: number[][], tail: number[] = []): Uint8Array {
  const payload = nals.flatMap((nal) => [...u32(nal.length), ...nal]);
  return Uint8Array.from([
    ...u32(16),
    ...ascii('ftyp'),
    ...ascii('mp42'),
    ...u32(0),
    ...u32(8),
    ...ascii('free'),
    ...u32(0),
    ...ascii('mdat'),
    ...payload,
    ...tail,
  ]);
}

describe('extractAnnexB', () => {
  const sps = [0x67, 0x42, 0xc0, 0x29];
  const pps = [0x68, 0xce, 0x3c, 0x80];
  const idr = [0x65, 0x88, 0x84, 0x00, 0x10];

  it('réécrit les NAL à longueur préfixée en Annex B', () => {
    const result = extractAnnexB(truncatedMp4([sps, pps, idr]));
    expect(result.nalCount).toBe(3);
    expect(result.droppedTailBytes).toBe(0);
    expect([...result.annexB]).toEqual([
      0,
      0,
      0,
      1,
      ...sps,
      0,
      0,
      0,
      1,
      ...pps,
      0,
      0,
      0,
      1,
      ...idr,
    ]);
  });

  it('ignore un dernier NAL coupé par le crash', () => {
    const cutNal = [...u32(100), 0x41, 0x9a];
    const result = extractAnnexB(truncatedMp4([sps, idr], cutNal));
    expect(result.nalCount).toBe(2);
    expect(result.droppedTailBytes).toBe(cutNal.length);
  });

  it('respecte la taille d’un mdat complet', () => {
    const payload = [...u32(idr.length), ...idr];
    const file = Uint8Array.from([
      ...u32(16),
      ...ascii('ftyp'),
      ...ascii('mp42'),
      ...u32(0),
      ...u32(8 + payload.length),
      ...ascii('mdat'),
      ...payload,
      ...ascii('moov'),
    ]);
    const result = extractAnnexB(file);
    expect(result.nalCount).toBe(1);
    expect(result.droppedTailBytes).toBe(0);
  });

  it('retourne un flux vide pour un mdat sans données', () => {
    const result = extractAnnexB(truncatedMp4([]));
    expect(result.nalCount).toBe(0);
    expect(result.annexB).toHaveLength(0);
  });

  it('refuse un fichier sans mdat', () => {
    const noMdat = Uint8Array.from([...u32(16), ...ascii('ftyp'), ...ascii('mp42'), ...u32(0)]);
    expect(() => extractAnnexB(noMdat)).toThrow(/mdat/);
  });
});
