export interface ContainerStats {
  name: string;
  /** 100 % = un cœur complet, la valeur peut dépasser 100. */
  cpuPercent: number;
  memMiB: number;
}

const UNIT_TO_MIB: Record<string, number> = {
  B: 1 / (1024 * 1024),
  KiB: 1 / 1024,
  MiB: 1,
  GiB: 1024,
};

/** Lit une ligne de `docker stats --no-stream --format "{{.Name}};{{.CPUPerc}};{{.MemUsage}}"`. */
export function parseDockerStatsLine(line: string): ContainerStats | undefined {
  const [name, cpu, mem] = line.trim().split(';');
  if (name === undefined || cpu === undefined || mem === undefined) return undefined;
  const cpuMatch = /^([\d.]+)%$/.exec(cpu);
  const memMatch = /^([\d.]+)\s*(B|KiB|MiB|GiB)\b/.exec(mem);
  const unit = memMatch?.[2];
  if (!cpuMatch?.[1] || !memMatch?.[1] || unit === undefined) return undefined;
  const factor = UNIT_TO_MIB[unit];
  if (factor === undefined) return undefined;
  return {
    name,
    cpuPercent: Number(cpuMatch[1]),
    memMiB: Number((Number(memMatch[1]) * factor).toFixed(1)),
  };
}

export interface StatsSummary {
  name: string;
  samples: number;
  cpuAvgPercent: number;
  cpuMaxPercent: number;
  memMaxMiB: number;
}

/** Moyenne et maxima par conteneur sur une série de relevés. */
export function summarizeStats(samples: readonly ContainerStats[]): StatsSummary[] {
  const byName = new Map<string, ContainerStats[]>();
  for (const sample of samples)
    byName.set(sample.name, [...(byName.get(sample.name) ?? []), sample]);
  return [...byName].map(([name, group]) => ({
    name,
    samples: group.length,
    cpuAvgPercent: Number(
      (group.reduce((sum, s) => sum + s.cpuPercent, 0) / group.length).toFixed(1),
    ),
    cpuMaxPercent: Math.max(...group.map((s) => s.cpuPercent)),
    memMaxMiB: Math.max(...group.map((s) => s.memMiB)),
  }));
}
