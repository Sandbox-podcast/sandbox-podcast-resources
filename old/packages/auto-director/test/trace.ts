import {
  AutoDirector,
  type DirectorDecision,
  type LevelFrame,
  type SceneCatalog,
} from '../src/index.ts';

export const catalog: SceneCatalog = {
  group: 'scene-group',
  focus: (id) => `scene-focus-${id}`,
  duo: (a, b) => `scene-duo-${a}-${b}`,
  presentation: 'scene-presentation',
};

export interface Segment {
  who: string;
  fromMs: number;
  toMs: number;
  levelDb: number;
}

/** Générateur pseudo-aléatoire déterministe (mulberry32). */
function random(seed: number): () => number {
  let state = seed;
  return () => {
    state = (state + 0x6d2b79f5) | 0;
    let t = Math.imul(state ^ (state >>> 15), 1 | state);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * Trace de niveaux synthétique : bruit de fond à -62 dBFS, segments de parole au niveau voulu,
 * petite variation aléatoire reproductible.
 */
export function buildFrames(
  participants: readonly string[],
  durationMs: number,
  segments: readonly Segment[],
  options: { tickMs?: number; floorDb?: number; jitterDb?: number; seed?: number } = {},
): LevelFrame[] {
  const tickMs = options.tickMs ?? 50;
  const floorDb = options.floorDb ?? -62;
  const jitterDb = options.jitterDb ?? 2;
  const next = random(options.seed ?? 1);
  const frames: LevelFrame[] = [];
  for (let timeMs = 0; timeMs <= durationMs; timeMs += tickMs) {
    const levelsDb: Record<string, number> = {};
    for (const who of participants) {
      let level = floorDb;
      for (const s of segments) {
        if (s.who === who && timeMs >= s.fromMs && timeMs < s.toMs)
          level = Math.max(level, s.levelDb);
      }
      levelsDb[who] = level + (next() * 2 - 1) * jitterDb;
    }
    frames.push({ timeMs, levelsDb });
  }
  return frames;
}

export function run(director: AutoDirector, frames: readonly LevelFrame[]): DirectorDecision[] {
  const decisions: DirectorDecision[] = [];
  for (const frame of frames) {
    const decision = director.tick(frame);
    if (decision) decisions.push(decision);
  }
  return decisions;
}

export const sceneIds = (decisions: readonly DirectorDecision[]): string[] =>
  decisions.map((d) => d.shot.sceneId);
