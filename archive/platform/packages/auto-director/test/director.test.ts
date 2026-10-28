import { describe, expect, it } from 'vitest';
import { ActiveSpeakerEngine, AutoDirector, DEFAULT_CONFIG } from '../src/index.ts';
import { buildFrames, catalog, run, sceneIds } from './trace.ts';

const people = ['A', 'B', 'C'];
const speech = -30;

describe('locuteur actif (AC-SPK-001)', () => {
  it('identifie le participant qui parle seul', () => {
    const engine = new ActiveSpeakerEngine(DEFAULT_CONFIG);
    const frames = buildFrames(people, 6000, [
      { who: 'B', fromMs: 1000, toMs: 6000, levelDb: speech },
    ]);
    const snapshots = frames.map((frame) => engine.update(frame));
    expect(snapshots.at(-1)?.active).toBe('B');
    expect(snapshots.at(-1)?.speakers).toEqual(['B']);
    expect(snapshots[5]?.active).toBeNull();
  });

  it('retourne null quand personne ne parle', () => {
    const engine = new ActiveSpeakerEngine(DEFAULT_CONFIG);
    const snapshots = buildFrames(people, 3000, []).map((frame) => engine.update(frame));
    expect(snapshots.every((s) => s.active === null && s.speakers.length === 0)).toBe(true);
  });
});

describe('moteur de parole : réglages un par un', () => {
  const snapshotsFor = (segments: Parameters<typeof buildFrames>[2], durationMs: number) => {
    const engine = new ActiveSpeakerEngine(DEFAULT_CONFIG);
    return buildFrames(people, durationMs, segments).map((frame) => engine.update(frame));
  };

  it('rejette un bruit plus court que la durée minimale de parole', () => {
    const snapshots = snapshotsFor([{ who: 'B', fromMs: 3000, toMs: 3200, levelDb: -25 }], 6000);
    expect(snapshots.every((s) => s.speakers.length === 0)).toBe(true);
  });

  it('garde la parole pendant une respiration (temps de maintien)', () => {
    const snapshots = snapshotsFor(
      [
        { who: 'A', fromMs: 1000, toMs: 4000, levelDb: speech },
        { who: 'A', fromMs: 4300, toMs: 9000, levelDb: speech },
      ],
      9000,
    );
    const before = snapshots.find((s) => s.activeSinceMs !== null)?.activeSinceMs;
    const after = snapshots.at(-1)?.activeSinceMs;
    expect(before).toBeDefined();
    expect(after).toBe(before);
  });

  it('garde le locuteur actif face à un autre à peine plus fort (marge de bascule)', () => {
    const snapshots = snapshotsFor(
      [
        { who: 'A', fromMs: 1000, toMs: 9000, levelDb: -30 },
        { who: 'B', fromMs: 2000, toMs: 9000, levelDb: -28 },
      ],
      9000,
    );
    expect(snapshots.every((s) => s.active === null || s.active === 'A')).toBe(true);
  });

  it('ne laisse pas un dépassement très bref remplacer le locuteur dominant', () => {
    const snapshots = snapshotsFor(
      [
        { who: 'A', fromMs: 1000, toMs: 9000, levelDb: -30 },
        { who: 'B', fromMs: 2000, toMs: 3500, levelDb: -33 },
        { who: 'B', fromMs: 3500, toMs: 3750, levelDb: -22 },
        { who: 'B', fromMs: 3750, toMs: 5000, levelDb: -33 },
      ],
      6000,
    );
    expect(snapshots.every((s) => s.active === null || s.active === 'A')).toBe(true);
  });
});

describe('bruits courts (AC-SPK-002)', () => {
  it('ne déclenche pas de plan pour un clic de 40 ms', () => {
    const director = new AutoDirector(catalog);
    const frames = buildFrames(people, 8000, [{ who: 'B', fromMs: 3000, toMs: 3040, levelDb: -5 }]);
    expect(sceneIds(run(director, frames))).toEqual(['scene-group']);
  });

  it('ignore une toux de B pendant que A parle', () => {
    const director = new AutoDirector(catalog);
    const frames = buildFrames(people, 12_000, [
      { who: 'A', fromMs: 1000, toMs: 12_000, levelDb: -30 },
      { who: 'B', fromMs: 6000, toMs: 6350, levelDb: -22 },
    ]);
    const decisions = run(director, frames);
    expect(sceneIds(decisions)).toEqual(['scene-group', 'scene-focus-A']);
    expect(decisions.some((d) => d.speakerId === 'B')).toBe(false);
  });

  it('ne passe pas sur une personne qui ne fait qu’une courte interjection', () => {
    const director = new AutoDirector(catalog);
    const frames = buildFrames(people, 12_000, [
      { who: 'A', fromMs: 1000, toMs: 12_000, levelDb: -32 },
      { who: 'B', fromMs: 6000, toMs: 6600, levelDb: -20 },
    ]);
    expect(sceneIds(run(director, frames))).toEqual(['scene-group', 'scene-focus-A']);
  });
});

describe('plans et temporisation (AC-SPK-003)', () => {
  it('passe en plan serré sur le locuteur stable, pas avant la durée minimale du plan', () => {
    const director = new AutoDirector(catalog);
    const decisions = run(
      director,
      buildFrames(people, 9000, [{ who: 'A', fromMs: 1000, toMs: 9000, levelDb: speech }]),
    );
    expect(sceneIds(decisions)).toEqual(['scene-group', 'scene-focus-A']);
    const focus = decisions[1];
    expect(focus?.timestampMs).toBeGreaterThanOrEqual(2500);
    expect(focus?.timestampMs).toBeLessThan(3500);
    expect(focus?.speakerId).toBe('A');
  });

  it('respecte la durée minimale entre deux changements automatiques', () => {
    // Prise de focus rapide : c'est alors la durée minimale du plan qui retarde le changement.
    const director = new AutoDirector(catalog, { ...DEFAULT_CONFIG, focusAfterMs: 100 });
    const frames = buildFrames(people, 20_000, [
      { who: 'A', fromMs: 1000, toMs: 3500, levelDb: speech },
      { who: 'B', fromMs: 3700, toMs: 20_000, levelDb: speech },
    ]);
    const decisions = run(director, frames);
    expect(sceneIds(decisions)).toEqual(['scene-group', 'scene-focus-A', 'scene-focus-B']);
    for (let i = 1; i < decisions.length; i++) {
      const gap = (decisions[i]?.timestampMs ?? 0) - (decisions[i - 1]?.timestampMs ?? 0);
      expect(gap).toBeGreaterThanOrEqual(2500);
    }
  });

  it('ignore une toux isolée pendant un silence', () => {
    const director = new AutoDirector(catalog);
    const frames = buildFrames(people, 10_000, [
      { who: 'B', fromMs: 5000, toMs: 5350, levelDb: -22 },
    ]);
    expect(sceneIds(run(director, frames))).toEqual(['scene-group']);
  });

  it('ne change pas de plan pour un souffle bref de niveau moyen', () => {
    const director = new AutoDirector(catalog);
    const frames = buildFrames(people, 10_000, [
      { who: 'C', fromMs: 4000, toMs: 4250, levelDb: -35 },
    ]);
    expect(sceneIds(run(director, frames))).toEqual(['scene-group']);
  });

  it('revient au plan de groupe après un silence prolongé', () => {
    const director = new AutoDirector(catalog);
    const frames = buildFrames(people, 16_000, [
      { who: 'A', fromMs: 1000, toMs: 5000, levelDb: speech },
    ]);
    const decisions = run(director, frames);
    expect(sceneIds(decisions)).toEqual(['scene-group', 'scene-focus-A', 'scene-group']);
    const back = decisions[2];
    expect(back?.reason).toBe('silence prolongé');
    expect(back?.timestampMs).toBeGreaterThanOrEqual(8500);
    expect(back?.timestampMs).toBeLessThan(10_500);
  });
});

describe('conversation croisée (AC-SPK-004)', () => {
  it('passe au plan de groupe sans osciller', () => {
    const director = new AutoDirector(catalog);
    const frames = buildFrames(people, 16_000, [
      { who: 'A', fromMs: 1000, toMs: 3000, levelDb: speech },
      { who: 'A', fromMs: 3000, toMs: 12_000, levelDb: -30 },
      { who: 'B', fromMs: 3000, toMs: 12_000, levelDb: -31 },
    ]);
    const decisions = run(director, frames);
    expect(sceneIds(decisions)).toEqual(['scene-group', 'scene-focus-A', 'scene-group']);
    expect(decisions[2]?.reason).toBe('conversation croisée');
  });

  it('détecte un duo quand deux personnes se répondent vivement', () => {
    const director = new AutoDirector(catalog);
    const frames = buildFrames(people, 16_000, [
      { who: 'A', fromMs: 1000, toMs: 2000, levelDb: speech },
      { who: 'B', fromMs: 2200, toMs: 3200, levelDb: speech },
      { who: 'A', fromMs: 3400, toMs: 4400, levelDb: speech },
      { who: 'B', fromMs: 4600, toMs: 5600, levelDb: speech },
      { who: 'A', fromMs: 5800, toMs: 6800, levelDb: speech },
      { who: 'B', fromMs: 7000, toMs: 8000, levelDb: speech },
    ]);
    const decisions = run(director, frames);
    expect(sceneIds(decisions)).toContain('scene-duo-A-B');
    expect(decisions.find((d) => d.shot.mode === 'DUO')?.shot.participants).toEqual(['A', 'B']);
  });
});

describe('réalisation manuelle (AC-SPK-005)', () => {
  it('cesse toute décision automatique dès que le Producer reprend la main', () => {
    const director = new AutoDirector(catalog);
    const frames = buildFrames(people, 20_000, [
      { who: 'A', fromMs: 1000, toMs: 4000, levelDb: speech },
      { who: 'B', fromMs: 6000, toMs: 20_000, levelDb: speech },
    ]);
    const before = run(
      director,
      frames.filter((f) => f.timeMs <= 4500),
    );
    director.setAuto(false, 4500);
    const during = run(
      director,
      frames.filter((f) => f.timeMs > 4500),
    );
    expect(sceneIds(before)).toEqual(['scene-group', 'scene-focus-A']);
    expect(during).toEqual([]);
    expect(director.isAuto).toBe(false);
    expect(director.events).toEqual([{ timestampMs: 4500, type: 'AUTO_DISABLED' }]);
  });

  it('journalise une prise manuelle et coupe l’automatique', () => {
    const director = new AutoDirector(catalog);
    run(
      director,
      buildFrames(people, 5000, [{ who: 'A', fromMs: 1000, toMs: 5000, levelDb: speech }]),
    );
    const take = director.manualTake(
      { mode: 'MANUAL', participants: [], sceneId: 'scene-3-speakers' },
      5100,
    );
    expect(take.source).toBe('MANUAL');
    expect(take.reason).toBe('prise manuelle du Producer');
    expect(director.isAuto).toBe(false);
    expect(director.shot?.sceneId).toBe('scene-3-speakers');
  });

  it('laisse au plan courant sa durée minimale quand l’automatique reprend', () => {
    const director = new AutoDirector(catalog);
    const frames = buildFrames(people, 20_000, [
      { who: 'B', fromMs: 1000, toMs: 20_000, levelDb: speech },
    ]);
    director.setAuto(false, 0);
    run(
      director,
      frames.filter((f) => f.timeMs < 8000),
    );
    director.manualTake({ mode: 'MANUAL', participants: [], sceneId: 'scene-manual' }, 8000);
    director.setAuto(true, 8100);
    const after = run(
      director,
      frames.filter((f) => f.timeMs >= 8100),
    );
    expect(after[0]?.timestampMs).toBeGreaterThanOrEqual(8100 + 2500);
    expect(after[0]?.shot.sceneId).toBe('scene-focus-B');
  });

  it('suspend les décisions automatiques pendant une présentation', () => {
    const director = new AutoDirector(catalog);
    const frames = buildFrames(people, 20_000, [
      { who: 'A', fromMs: 1000, toMs: 8000, levelDb: speech },
      { who: 'B', fromMs: 9000, toMs: 20_000, levelDb: speech },
    ]);
    run(
      director,
      frames.filter((f) => f.timeMs < 3000),
    );
    const start = director.setPresentation(true, 3000);
    const during = run(
      director,
      frames.filter((f) => f.timeMs >= 3000 && f.timeMs < 12_000),
    );
    const end = director.setPresentation(false, 12_000);
    expect(start?.shot.mode).toBe('PRESENTATION');
    expect(during).toEqual([]);
    expect(end?.shot.mode).toBe('GROUP');
    const after = run(
      director,
      frames.filter((f) => f.timeMs > 12_000),
    );
    expect(sceneIds(after)).toEqual(['scene-focus-B']);
  });
});

describe('journal (AC-SPK-006)', () => {
  it('enregistre pour chaque décision tous les champs demandés', () => {
    const director = new AutoDirector(catalog);
    run(
      director,
      buildFrames(people, 16_000, [
        { who: 'A', fromMs: 1000, toMs: 5000, levelDb: speech },
        { who: 'B', fromMs: 6000, toMs: 12_000, levelDb: speech },
      ]),
    );
    expect(director.journal.length).toBeGreaterThanOrEqual(3);
    for (const decision of director.journal) {
      expect(decision.timestampMs).toBeGreaterThanOrEqual(0);
      expect(decision.shot.mode.length).toBeGreaterThan(0);
      expect(['AUTO', 'MANUAL']).toContain(decision.source);
      expect(decision.shot.sceneId.length).toBeGreaterThan(0);
      expect(decision.reason.length).toBeGreaterThan(0);
      expect(decision.confidence).toBeGreaterThanOrEqual(0);
      expect(decision.confidence).toBeLessThanOrEqual(1);
      expect(decision.speakerId === null || typeof decision.speakerId === 'string').toBe(true);
    }
  });

  it('associe la décision au locuteur qui l’a provoquée', () => {
    const director = new AutoDirector(catalog);
    run(
      director,
      buildFrames(people, 8000, [{ who: 'C', fromMs: 1000, toMs: 8000, levelDb: speech }]),
    );
    expect(director.journal.at(-1)?.speakerId).toBe('C');
  });
});

describe('robustesse', () => {
  it('n’oscille pas quand le niveau d’un participant frôle les seuils (hystérésis)', () => {
    const engine = new ActiveSpeakerEngine(DEFAULT_CONFIG);
    let transitions = 0;
    let wasSpeaking = false;
    for (let t = 0; t <= 20_000; t += 50) {
      const level = Math.floor(t / 100) % 2 === 0 ? -44 : -40;
      const speaking = engine.update({ timeMs: t, levelsDb: { A: level } }).speakers.includes('A');
      if (speaking !== wasSpeaking) transitions += 1;
      wasSpeaking = speaking;
    }
    expect(transitions).toBeLessThanOrEqual(2);
  });

  it('produit exactement les mêmes décisions pour la même trace', () => {
    const frames = buildFrames(people, 20_000, [
      { who: 'A', fromMs: 1000, toMs: 6000, levelDb: speech },
      { who: 'B', fromMs: 6500, toMs: 12_000, levelDb: speech },
      { who: 'C', fromMs: 13_000, toMs: 18_000, levelDb: speech },
    ]);
    const first = run(new AutoDirector(catalog), frames);
    const second = run(new AutoDirector(catalog), frames);
    expect(second).toEqual(first);
  });

  it('traite une heure de trames à 50 ms en moins de 3 secondes', () => {
    const director = new AutoDirector(catalog);
    const frames = buildFrames(people, 3_600_000, [
      { who: 'A', fromMs: 1000, toMs: 1_800_000, levelDb: speech },
      { who: 'B', fromMs: 1_800_000, toMs: 3_600_000, levelDb: speech },
    ]);
    const startedAt = performance.now();
    run(director, frames);
    expect(performance.now() - startedAt).toBeLessThan(3000);
  });
});
