/**
 * Régulation de la qualité du studio virtuel sur une machine qui peine : un « escalier » de niveaux
 * qui dégradent d'abord le détail du détourage, jamais la fluidité de la composition, et remontent
 * seulement quand la machine a de la marge.
 */

export interface QualityLevel {
  /** Nom court affichable à la régie. */
  readonly name: string;
  /** Détourage une image sur N (le masque précédent est réutilisé entre-temps). 0 : détourage coupé. */
  readonly segmentEvery: number;
  /** Hauteur de l'image donnée au modèle de détourage, en pixels. */
  readonly segmentInputHeight: number;
  /** Images par seconde de la composition. */
  readonly compositionFps: number;
}

/** Du meilleur au plus économe. Le dernier niveau n'utilise plus aucun modèle : cadre fixe aux bords adoucis. */
export const DEFAULT_LEVELS: readonly QualityLevel[] = [
  { name: 'COMPLET', segmentEvery: 1, segmentInputHeight: 720, compositionFps: 30 },
  { name: 'MASQUE_RÉDUIT', segmentEvery: 2, segmentInputHeight: 720, compositionFps: 30 },
  { name: 'MASQUE_BAS', segmentEvery: 3, segmentInputHeight: 360, compositionFps: 30 },
  { name: 'SANS_DÉTOURAGE', segmentEvery: 0, segmentInputHeight: 0, compositionFps: 30 },
  { name: 'SECOURS', segmentEvery: 0, segmentInputHeight: 0, compositionFps: 15 },
];

export interface QualityConfig {
  levels: readonly QualityLevel[];
  /** Budget par image de la composition, en ms (33,3 pour 30 images/s). */
  frameBudgetMs: number;
  /** Au-delà de cette part du budget (moyenne lissée), on est en surcharge. */
  overloadRatio: number;
  /** En dessous de cette part, on a de la marge. */
  headroomRatio: number;
  /** Surcharge continue exigée avant de dégrader. */
  degradeAfterMs: number;
  /** Marge continue exigée avant de remonter. */
  upgradeAfterMs: number;
  /** Délai minimal entre deux changements de niveau. */
  cooldownMs: number;
  /** Après une remontée suivie d'une nouvelle dégradation dans ce délai, on n'y retourne pas avant `banMs`. */
  probationMs: number;
  banMs: number;
  /** Poids de la dernière mesure dans la moyenne lissée (0 à 1). */
  smoothing: number;
  /** Premières images ignorées : chargement du modèle, compilation des shaders. */
  warmupFrames: number;
}

export const DEFAULT_CONFIG: QualityConfig = {
  levels: DEFAULT_LEVELS,
  frameBudgetMs: 1000 / 30,
  overloadRatio: 0.8,
  headroomRatio: 0.45,
  degradeAfterMs: 1500,
  upgradeAfterMs: 15_000,
  cooldownMs: 3000,
  probationMs: 20_000,
  banMs: 60_000,
  smoothing: 0.1,
  warmupFrames: 15,
};

export type Reason = 'OVERLOAD' | 'HEADROOM' | 'MANUAL_LOCK' | 'MANUAL_RELEASE';

export interface Decision {
  /** Indice du niveau en vigueur. */
  level: number;
  changed: boolean;
  reason: Reason | null;
  /** Charge lissée (coût / budget), pour l'affichage et le journal. */
  load: number;
}

export interface ChangeRecord {
  atMs: number;
  from: number;
  to: number;
  reason: Reason;
  load: number;
}

/**
 * Contrôleur à hystérésis. Il ne regarde qu'une chose : le coût mesuré de chaque image de composition
 * (détourage compris). Dégrade d'un seul niveau à la fois, après une surcharge continue ; remonte d'un
 * seul niveau après une marge continue et assez longue ; ne remonte pas vers un niveau qui vient d'échouer.
 * Le Producer peut figer un niveau (verrou) : le contrôleur n'y touche plus jusqu'à la libération.
 */
export class QualityController {
  private readonly config: QualityConfig;
  private level = 0;
  private load = 0;
  private seeded = false;
  private framesSeen = 0;
  private overloadSinceMs: number | null = null;
  private headroomSinceMs: number | null = null;
  private lastChangeMs = Number.NEGATIVE_INFINITY;
  private lastUpgradeMs = Number.NEGATIVE_INFINITY;
  private locked: number | null = null;
  /** Niveau → instant jusqu'auquel on n'y remonte pas. */
  private readonly banned = new Map<number, number>();
  readonly changes: ChangeRecord[] = [];

  constructor(config: Partial<QualityConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    if (this.config.levels.length === 0) throw new Error('au moins un niveau est nécessaire');
  }

  get currentLevel(): number {
    return this.level;
  }

  get currentSettings(): QualityLevel {
    const settings = this.config.levels[this.level];
    if (!settings) throw new Error('niveau hors de la liste');
    return settings;
  }

  private move(to: number, reason: Reason, nowMs: number): Decision {
    const from = this.level;
    this.level = to;
    this.lastChangeMs = nowMs;
    this.overloadSinceMs = null;
    this.headroomSinceMs = null;
    this.changes.push({ atMs: nowMs, from, to, reason, load: this.load });
    return { level: to, changed: true, reason, load: this.load };
  }

  /** Fige le niveau (choix du Producer). */
  lock(level: number, nowMs: number): Decision {
    const clamped = Math.min(Math.max(0, level), this.config.levels.length - 1);
    this.locked = clamped;
    return clamped === this.level
      ? { level: this.level, changed: false, reason: null, load: this.load }
      : this.move(clamped, 'MANUAL_LOCK', nowMs);
  }

  unlock(nowMs: number): Decision {
    if (this.locked === null)
      return { level: this.level, changed: false, reason: null, load: this.load };
    this.locked = null;
    this.lastChangeMs = nowMs;
    this.changes.push({
      atMs: nowMs,
      from: this.level,
      to: this.level,
      reason: 'MANUAL_RELEASE',
      load: this.load,
    });
    return { level: this.level, changed: false, reason: 'MANUAL_RELEASE', load: this.load };
  }

  /** À appeler pour chaque image composée, avec son coût total en ms. */
  onFrame(costMs: number, nowMs: number): Decision {
    this.framesSeen += 1;
    const hold = (): Decision => ({
      level: this.level,
      changed: false,
      reason: null,
      load: this.load,
    });
    if (this.framesSeen <= this.config.warmupFrames) return hold();
    const ratio = costMs / this.config.frameBudgetMs;
    this.load = this.seeded ? this.load + this.config.smoothing * (ratio - this.load) : ratio;
    this.seeded = true;
    if (this.locked !== null) return hold();

    if (this.load > this.config.overloadRatio) {
      this.headroomSinceMs = null;
      this.overloadSinceMs ??= nowMs;
      const lastLevel = this.config.levels.length - 1;
      if (
        nowMs - this.overloadSinceMs >= this.config.degradeAfterMs &&
        nowMs - this.lastChangeMs >= this.config.cooldownMs &&
        this.level < lastLevel
      ) {
        // Une dégradation qui suit de près une remontée : ce niveau n'est pas tenable, on l'écarte un moment.
        if (nowMs - this.lastUpgradeMs < this.config.probationMs)
          this.banned.set(this.level, nowMs + this.config.banMs);
        return this.move(this.level + 1, 'OVERLOAD', nowMs);
      }
      return hold();
    }
    this.overloadSinceMs = null;

    if (this.load < this.config.headroomRatio && this.level > 0) {
      this.headroomSinceMs ??= nowMs;
      const target = this.level - 1;
      const bannedUntil = this.banned.get(target) ?? 0;
      if (
        nowMs - this.headroomSinceMs >= this.config.upgradeAfterMs &&
        nowMs - this.lastChangeMs >= this.config.cooldownMs &&
        nowMs >= bannedUntil
      ) {
        this.lastUpgradeMs = nowMs;
        return this.move(target, 'HEADROOM', nowMs);
      }
      return hold();
    }
    this.headroomSinceMs = null;
    return hold();
  }
}
