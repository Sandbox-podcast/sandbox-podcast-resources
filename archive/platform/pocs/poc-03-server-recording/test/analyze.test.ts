import { describe, expect, it } from 'vitest';
import { checkAgainst, parseFfprobe, parseFrameRate } from '../src/lib/analyze.ts';
import { audioProbe, videoProbe } from './fixtures.ts';

describe('parseFrameRate', () => {
  it.each([
    ['30/1', 30],
    ['60/1', 60],
    ['25/1', 25],
  ])('%s → %s', (rate, expected) => {
    expect(parseFrameRate(rate)).toBe(expected);
  });

  it('gère les fractions NTSC', () => {
    expect(parseFrameRate('30000/1001')).toBeCloseTo(29.97, 2);
  });

  it.each(['0/0', '30/0', 'abc', ''])('retourne undefined pour %j', (rate) => {
    expect(parseFrameRate(rate)).toBeUndefined();
  });

  it('retourne undefined sans valeur', () => {
    expect(parseFrameRate(undefined)).toBeUndefined();
  });
});

describe('parseFfprobe', () => {
  it('résume un fichier vidéo', () => {
    expect(parseFfprobe(videoProbe)).toEqual({
      kind: 'video',
      container: 'mov,mp4,m4a,3gp,3g2,mj2',
      codec: 'h264',
      width: 1920,
      height: 1080,
      fps: 30,
      durationSec: 60.033,
      bitrateKbps: 4000,
      sizeBytes: 30_000_000,
    });
  });

  it('résume un fichier audio', () => {
    const summary = parseFfprobe(audioProbe);
    expect(summary.kind).toBe('audio');
    expect(summary.codec).toBe('opus');
    expect(summary.width).toBeUndefined();
    expect(summary.durationSec).toBeCloseTo(59.98, 2);
  });

  it('refuse une sortie sans flux', () => {
    expect(() => parseFfprobe({ streams: [], format: {} })).toThrow(/Aucun flux/);
  });

  it('refuse une sortie qui n’est pas du ffprobe', () => {
    expect(() => parseFfprobe({ nope: true })).toThrow();
  });
});

describe('checkAgainst', () => {
  const expectation = {
    kind: 'video' as const,
    expectedDurationSec: 60,
    durationToleranceSec: 2,
    minWidth: 1920,
    minHeight: 1080,
    minFps: 29,
    codecs: ['h264'],
  };

  it('accepte un fichier conforme', () => {
    expect(checkAgainst(parseFfprobe(videoProbe), expectation)).toEqual([]);
  });

  it('signale une durée trop courte', () => {
    const summary = { ...parseFfprobe(videoProbe), durationSec: 41 };
    expect(checkAgainst(summary, expectation)).toEqual([expect.stringContaining('durée 41.0 s')]);
  });

  it('signale une résolution et un débit d’images insuffisants', () => {
    const summary = { ...parseFfprobe(videoProbe), width: 1280, height: 720, fps: 15 };
    const issues = checkAgainst(summary, expectation);
    expect(issues).toHaveLength(3);
    expect(issues.join(' ')).toMatch(/largeur 1280/);
    expect(issues.join(' ')).toMatch(/hauteur 720/);
    expect(issues.join(' ')).toMatch(/15.0 images\/s/);
  });

  it('signale un mauvais type et un mauvais codec', () => {
    const issues = checkAgainst(parseFfprobe(audioProbe), { ...expectation, codecs: ['h264'] });
    expect(issues.join(' ')).toMatch(/type audio, attendu video/);
    expect(issues.join(' ')).toMatch(/codec opus/);
  });

  it('signale une durée inconnue', () => {
    const summary = { ...parseFfprobe(videoProbe), durationSec: undefined };
    expect(checkAgainst(summary, expectation)).toContain('durée inconnue');
  });
});
