import { describe, expect, it } from 'vitest';
import { parseDockerStatsLine, summarizeStats } from '../src/lib/docker-stats.ts';

describe('parseDockerStatsLine', () => {
  it('lit le CPU et la mémoire en MiB', () => {
    expect(parseDockerStatsLine('poc03-egress-1;12.50%;256.5MiB / 15.53GiB')).toEqual({
      name: 'poc03-egress-1',
      cpuPercent: 12.5,
      memMiB: 256.5,
    });
  });

  it('convertit les GiB et les KiB', () => {
    expect(parseDockerStatsLine('a;0.00%;1.5GiB / 15GiB')?.memMiB).toBe(1536);
    expect(parseDockerStatsLine('a;0.00%;512KiB / 15GiB')?.memMiB).toBe(0.5);
  });

  it('accepte un CPU supérieur à 100 %', () => {
    expect(parseDockerStatsLine('a;215.30%;10MiB / 1GiB')?.cpuPercent).toBe(215.3);
  });

  it.each(['', 'a;b', 'a;--;--', 'a;1.0%;??', 'a;1.0%;10 TB / 1GiB'])(
    'retourne undefined pour %j',
    (line) => {
      expect(parseDockerStatsLine(line)).toBeUndefined();
    },
  );
});

describe('summarizeStats', () => {
  it('calcule moyenne et maxima par conteneur', () => {
    const summary = summarizeStats([
      { name: 'egress', cpuPercent: 10, memMiB: 100 },
      { name: 'egress', cpuPercent: 30, memMiB: 150 },
      { name: 'livekit', cpuPercent: 5, memMiB: 40 },
    ]);
    expect(summary).toEqual([
      { name: 'egress', samples: 2, cpuAvgPercent: 20, cpuMaxPercent: 30, memMaxMiB: 150 },
      { name: 'livekit', samples: 1, cpuAvgPercent: 5, cpuMaxPercent: 5, memMaxMiB: 40 },
    ]);
  });

  it('retourne une liste vide sans relevé', () => {
    expect(summarizeStats([])).toEqual([]);
  });
});
