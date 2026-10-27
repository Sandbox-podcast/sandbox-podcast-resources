import { describe, expect, it } from 'vitest';
import { cpuPercentOfCore, summarizeVideo, type VideoSample } from '../src/lib/summary.ts';

const sample = (overrides: Partial<VideoSample>): VideoSample => ({
  at: 0,
  bytesSent: 0,
  framesEncoded: 0,
  totalEncodeTime: 0,
  frameWidth: 1920,
  frameHeight: 1080,
  framesPerSecond: 30,
  qualityLimitationReason: 'none',
  encoderImplementation: 'OpenH264',
  codec: 'video/H264',
  ...overrides,
});

describe('summarizeVideo', () => {
  it('calcule le débit moyen entre le premier et le dernier relevé', () => {
    const summary = summarizeVideo([
      sample({ at: 0, bytesSent: 0 }),
      sample({ at: 10_000, bytesSent: 5_000_000 }),
    ]);
    // 5 Mo en 10 s = 4000 kb/s
    expect(summary.avgBitrateKbps).toBe(4000);
  });

  it('calcule le temps d’encodage moyen par image', () => {
    const summary = summarizeVideo([
      sample({ at: 0, framesEncoded: 0, totalEncodeTime: 0 }),
      sample({ at: 10_000, bytesSent: 1, framesEncoded: 300, totalEncodeTime: 1.5 }),
    ]);
    // 1,5 s pour 300 images = 5 ms par image
    expect(summary.avgEncodeMsPerFrame).toBe(5);
  });

  it('compte les raisons de limitation de qualité', () => {
    const summary = summarizeVideo([
      sample({ qualityLimitationReason: 'none' }),
      sample({ qualityLimitationReason: 'bandwidth' }),
      sample({ qualityLimitationReason: 'bandwidth' }),
      sample({ qualityLimitationReason: undefined }),
    ]);
    expect(summary.limitationReasons).toEqual({ none: 1, bandwidth: 2, inconnu: 1 });
  });

  it('retient la dernière résolution connue, le codec et l’encodeur', () => {
    const summary = summarizeVideo([
      sample({ frameWidth: 1280, frameHeight: 720 }),
      sample({ frameWidth: 1920, frameHeight: 1080 }),
      sample({ frameWidth: undefined, frameHeight: undefined }),
    ]);
    expect(summary.resolution).toBe('1920x1080');
    expect(summary.codec).toBe('video/H264');
    expect(summary.encoder).toBe('OpenH264');
  });

  it('ne calcule rien sans relevé exploitable', () => {
    const summary = summarizeVideo([]);
    expect(summary.avgBitrateKbps).toBeUndefined();
    expect(summary.avgFps).toBeUndefined();
    expect(summary.resolution).toBeUndefined();
  });
});

describe('cpuPercentOfCore', () => {
  it('convertit un temps CPU cumulé en pourcentage d’un cœur', () => {
    expect(
      cpuPercentOfCore([
        { atMs: 0, cpuSeconds: 10 },
        { atMs: 10_000, cpuSeconds: 15 },
      ]),
    ).toBe(50);
  });

  it('peut dépasser 100 % quand plusieurs cœurs travaillent', () => {
    expect(
      cpuPercentOfCore([
        { atMs: 0, cpuSeconds: 0 },
        { atMs: 5000, cpuSeconds: 15 },
      ]),
    ).toBe(300);
  });

  it('retourne undefined avec moins de deux relevés', () => {
    expect(cpuPercentOfCore([{ atMs: 0, cpuSeconds: 1 }])).toBeUndefined();
    expect(cpuPercentOfCore([])).toBeUndefined();
  });
});
