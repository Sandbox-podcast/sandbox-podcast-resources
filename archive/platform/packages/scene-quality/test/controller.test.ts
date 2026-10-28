import { describe, expect, it } from 'vitest';
import { DEFAULT_CONFIG, DEFAULT_LEVELS, QualityController } from '../src/index.ts';

const BUDGET = DEFAULT_CONFIG.frameBudgetMs;
const STEP = 33;

/** Alimente le contrôleur : `costMs` par image pendant `durationMs`, à partir de `fromMs`. Retourne l'instant final. */
function feed(
  controller: QualityController,
  costMs: number,
  fromMs: number,
  durationMs: number,
): number {
  let now = fromMs;
  while (now < fromMs + durationMs) {
    controller.onFrame(costMs, now);
    now += STEP;
  }
  return now;
}

const LIGHT = BUDGET * 0.2;
const MARGINAL = BUDGET * 0.6;
const HEAVY = BUDGET * 1.5;

// Sans phase de chauffe, pour raisonner sur les durées exactes.
const make = (extra = {}): QualityController =>
  new QualityController({ warmupFrames: 0, ...extra });

describe('niveaux par défaut', () => {
  it('vont du plus fin au plus économe, sans jamais dépasser 30 images/s', () => {
    expect(DEFAULT_LEVELS.map((l) => l.name)).toEqual([
      'COMPLET',
      'MASQUE_RÉDUIT',
      'MASQUE_BAS',
      'SANS_DÉTOURAGE',
      'SECOURS',
    ]);
    for (let i = 1; i < DEFAULT_LEVELS.length; i += 1) {
      const previous = DEFAULT_LEVELS[i - 1];
      const level = DEFAULT_LEVELS[i];
      if (!previous || !level) throw new Error('niveau manquant');
      expect(level.compositionFps).toBeLessThanOrEqual(previous.compositionFps);
      expect(level.segmentInputHeight).toBeLessThanOrEqual(previous.segmentInputHeight);
    }
    expect(DEFAULT_LEVELS.every((l) => l.compositionFps <= 30)).toBe(true);
    expect(DEFAULT_LEVELS.filter((l) => l.segmentEvery === 0)).toHaveLength(2);
  });

  it('refuse une liste de niveaux vide', () => {
    expect(() => new QualityController({ levels: [] })).toThrow(/au moins un niveau/);
  });
});

describe('dégradation', () => {
  it('une charge légère ne change rien', () => {
    const controller = make();
    feed(controller, LIGHT, 0, 60_000);
    expect(controller.currentLevel).toBe(0);
    expect(controller.changes).toEqual([]);
  });

  it('une charge moyenne (entre marge et surcharge) ne change rien, dans aucun sens', () => {
    const controller = make();
    feed(controller, MARGINAL, 0, 60_000);
    expect(controller.currentLevel).toBe(0);
    const degraded = make();
    degraded.lock(2, 0);
    degraded.unlock(0);
    feed(degraded, MARGINAL, 100, 120_000);
    expect(degraded.currentLevel).toBe(2);
  });

  it('un pic bref ne dégrade pas', () => {
    const controller = make();
    let now = feed(controller, LIGHT, 0, 5000);
    now = feed(controller, HEAVY * 3, now, 400);
    feed(controller, LIGHT, now, 10_000);
    expect(controller.currentLevel).toBe(0);
  });

  it('une surcharge continue dégrade d’un niveau à la fois, séparés par le délai de repos', () => {
    const controller = make();
    feed(controller, HEAVY, 0, 60_000);
    expect(controller.currentLevel).toBe(DEFAULT_LEVELS.length - 1);
    const moves = controller.changes;
    expect(moves.map((m) => [m.from, m.to, m.reason])).toEqual([
      [0, 1, 'OVERLOAD'],
      [1, 2, 'OVERLOAD'],
      [2, 3, 'OVERLOAD'],
      [3, 4, 'OVERLOAD'],
    ]);
    for (let i = 1; i < moves.length; i += 1)
      expect((moves[i]?.atMs ?? 0) - (moves[i - 1]?.atMs ?? 0)).toBeGreaterThanOrEqual(
        DEFAULT_CONFIG.cooldownMs,
      );
    expect(moves[0]?.atMs).toBeGreaterThanOrEqual(DEFAULT_CONFIG.degradeAfterMs);
  });

  it('ne descend pas sous le dernier niveau', () => {
    const controller = make();
    feed(controller, HEAVY, 0, 120_000);
    expect(controller.currentLevel).toBe(4);
    expect(controller.changes).toHaveLength(4);
  });

  it('applique les réglages du niveau courant', () => {
    const controller = make();
    expect(controller.currentSettings.name).toBe('COMPLET');
    feed(controller, HEAVY, 0, 3000);
    expect(controller.currentSettings.name).toBe('MASQUE_RÉDUIT');
  });

  it('ignore les premières images (chargement du modèle) sans dégrader', () => {
    const controller = new QualityController();
    let now = 0;
    for (let i = 0; i < DEFAULT_CONFIG.warmupFrames; i += 1) {
      controller.onFrame(2000, now);
      now += STEP;
    }
    feed(controller, LIGHT, now, 20_000);
    expect(controller.currentLevel).toBe(0);
    expect(controller.changes).toEqual([]);
  });
});

describe('lissage et durées continues', () => {
  it('une alternance d’images lourdes et légères dont la moyenne est en surcharge dégrade quand même', () => {
    const controller = make();
    let now = 0;
    for (let i = 0; i < 400; i += 1) {
      controller.onFrame(i % 2 === 0 ? BUDGET * 2 : BUDGET * 0.1, now);
      now += STEP;
    }
    expect(controller.currentLevel).toBeGreaterThan(0);
  });

  it('une surcharge interrompue remet le compteur à zéro', () => {
    const controller = make();
    let now = feed(controller, LIGHT, 0, 3000);
    now = feed(controller, HEAVY, now, 1000);
    now = feed(controller, MARGINAL, now, 15_000);
    feed(controller, HEAVY, now, 700);
    expect(controller.currentLevel).toBe(0);
  });

  it('une marge interrompue par une surcharge repart de zéro (sans lissage, la charge saute d’un état à l’autre)', () => {
    const controller = make({ smoothing: 1 });
    controller.lock(2, 0);
    controller.unlock(0);
    let now = feed(controller, LIGHT, 1, 12_000);
    now = feed(controller, HEAVY, now, 1000);
    feed(controller, LIGHT, now, 6000);
    expect(controller.currentLevel).toBe(2);
  });
});

describe('remontée', () => {
  it('remonte d’un niveau après une marge continue, pas avant', () => {
    const controller = make();
    controller.lock(3, 0);
    controller.unlock(0);
    const justBefore = feed(controller, LIGHT, 1, DEFAULT_CONFIG.upgradeAfterMs - 1500);
    expect(controller.currentLevel).toBe(3);
    feed(controller, LIGHT, justBefore, 3000);
    expect(controller.currentLevel).toBe(2);
    expect(controller.changes.at(-1)).toMatchObject({ from: 3, to: 2, reason: 'HEADROOM' });
  });

  it('remonte un niveau à la fois, avec un nouveau délai entre deux remontées', () => {
    const controller = make();
    controller.lock(4, 0);
    controller.unlock(0);
    feed(controller, LIGHT, 1, 200_000);
    expect(controller.currentLevel).toBe(0);
    const ups = controller.changes.filter((c) => c.reason === 'HEADROOM');
    expect(ups.map((c) => [c.from, c.to])).toEqual([
      [4, 3],
      [3, 2],
      [2, 1],
      [1, 0],
    ]);
    for (let i = 1; i < ups.length; i += 1)
      expect((ups[i]?.atMs ?? 0) - (ups[i - 1]?.atMs ?? 0)).toBeGreaterThanOrEqual(
        DEFAULT_CONFIG.upgradeAfterMs,
      );
  });

  it('une charge qui remonte au milieu de la marge remet le compteur à zéro', () => {
    const controller = make();
    controller.lock(2, 0);
    controller.unlock(0);
    let now = feed(controller, LIGHT, 1, 10_000);
    now = feed(controller, MARGINAL, now, 8000);
    feed(controller, LIGHT, now, 10_000);
    expect(controller.currentLevel).toBe(2);
  });

  it('ne remonte pas au-dessus du niveau 0', () => {
    const controller = make();
    feed(controller, LIGHT, 0, 100_000);
    expect(controller.currentLevel).toBe(0);
  });
});

describe('protection contre les oscillations', () => {
  it('écarte pendant un moment le niveau dont la remontée vient d’échouer', () => {
    const controller = make();
    controller.lock(1, 0);
    controller.unlock(0);
    // Marge : remonte au niveau 0.
    let now = feed(controller, LIGHT, 1, DEFAULT_CONFIG.upgradeAfterMs + 2000);
    expect(controller.currentLevel).toBe(0);
    // Surcharge juste après : redescend, et le niveau 0 est écarté.
    now = feed(controller, HEAVY, now, 4000);
    expect(controller.currentLevel).toBe(1);
    const failedAt = controller.changes.at(-1)?.atMs ?? 0;
    // Marge de nouveau, mais pas de remontée tant que l'interdiction court.
    now = feed(controller, LIGHT, now, DEFAULT_CONFIG.banMs - (now - failedAt) - 1000);
    expect(controller.currentLevel).toBe(1);
    // Après l'interdiction, la remontée est de nouveau permise.
    feed(controller, LIGHT, now, 40_000);
    expect(controller.currentLevel).toBe(0);
  });

  it('n’écarte pas un niveau quand la dégradation n’a pas suivi une remontée récente', () => {
    const controller = make();
    let now = feed(controller, HEAVY, 0, 10_000);
    expect(controller.currentLevel).toBeGreaterThan(0);
    now = feed(controller, LIGHT, now, 120_000);
    expect(controller.currentLevel).toBe(0);
    expect(now).toBeGreaterThan(0);
  });
});

describe('verrou manuel', () => {
  it('fige le niveau choisi quelle que soit la charge, et le journalise', () => {
    const controller = make();
    const decision = controller.lock(3, 100);
    expect(decision).toMatchObject({ level: 3, changed: true, reason: 'MANUAL_LOCK' });
    feed(controller, HEAVY * 3, 200, 60_000);
    expect(controller.currentLevel).toBe(3);
    feed(controller, LIGHT, 70_000, 120_000);
    expect(controller.currentLevel).toBe(3);
    expect(controller.changes).toHaveLength(1);
  });

  it('borne un niveau hors de la liste', () => {
    const controller = make();
    expect(controller.lock(99, 0).level).toBe(4);
    expect(controller.lock(-5, 1).level).toBe(0);
  });

  it('verrouiller le niveau courant ne change rien', () => {
    const controller = make();
    expect(controller.lock(0, 0)).toMatchObject({ level: 0, changed: false });
    expect(controller.changes).toEqual([]);
  });

  it('libéré, le contrôleur reprend la main sans saut immédiat', () => {
    const controller = make();
    controller.lock(3, 0);
    const released = controller.unlock(100);
    expect(released).toMatchObject({ level: 3, changed: false, reason: 'MANUAL_RELEASE' });
    expect(controller.unlock(200)).toMatchObject({ reason: null });
    feed(controller, LIGHT, 300, 20_000);
    expect(controller.currentLevel).toBe(2);
  });
});
