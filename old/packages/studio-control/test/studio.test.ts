import { describe, expect, it } from 'vitest';
import {
  InMemoryStudioStore,
  StudioService,
  handleCommand,
  initialState,
  type Actor,
  type Command,
  type CommandBody,
  type ErrorCode,
  type Source,
  type SourceKind,
  type StudioPolicy,
} from '../src/index.ts';

const producer: Actor = { id: 'lou', kind: 'USER', roles: ['PRODUCER'] };
const host: Actor = { id: 'sam', kind: 'USER', roles: ['HOST'] };
const guest: Actor = { id: 'invite', kind: 'USER', roles: ['GUEST'] };
const editor: Actor = { id: 'edi', kind: 'USER', roles: ['EDITOR'] };
const mcpGuest: Actor = { id: 'agent', kind: 'MCP', roles: ['GUEST'] };
const loader: Actor = { id: 'loader', kind: 'SYSTEM', roles: [] };
const auto: Actor = { id: 'auto-director', kind: 'AUTO_DIRECTOR', roles: [] };

const group: Source = { kind: 'scene', id: 'scene-group' };
const slides: Source = { kind: 'presentation', id: 'slides-1', assetId: 'asset-slides' };
const clip: Source = { kind: 'video', id: 'clip-1', assetId: 'asset-clip' };

const pick = <T>(list: readonly T[], index: number): T => {
  const item = list[index];
  if (item === undefined) throw new Error(`élément ${String(index)} manquant`);
  return item;
};

let counter = 0;
const cmd = (
  actor: Actor,
  body: CommandBody,
  overrides: { commandId?: string; atMs?: number; expectedVersion?: number } = {},
): Command => ({
  commandId: overrides.commandId ?? `cmd-${String((counter += 1))}`,
  actor,
  atMs: overrides.atMs ?? 1000 + counter,
  ...(overrides.expectedVersion !== undefined
    ? { expectedVersion: overrides.expectedVersion }
    : {}),
  ...body,
});

const newService = (policy?: StudioPolicy, yieldBeforeCommit = false) =>
  new StudioService(new InMemoryStudioStore({ yieldBeforeCommit }), policy);

const errorCode = (executed: {
  result: { ok: boolean } & Record<string, unknown>;
}): ErrorCode | null => {
  const result = executed.result as { ok: false; error: { code: ErrorCode } } | { ok: true };
  return result.ok ? null : result.error.code;
};

describe('Preview et Program (AC-REGIE-001, AC-SCENE-006)', () => {
  it('choisir la Preview ne modifie pas le Program', async () => {
    const service = newService();
    await service.execute('s', cmd(producer, { type: 'CUT', source: group }));
    const before = await service.state('s');
    await service.execute('s', cmd(producer, { type: 'SET_PREVIEW', source: slides }));
    const after = await service.state('s');
    expect(after.program).toEqual(before.program);
    expect(after.preview).toEqual(slides);
  });

  it('accepte les types de source de la régie (AC-REGIE-004)', async () => {
    const service = newService();
    const kinds: SourceKind[] = [
      'scene',
      'image',
      'video',
      'presentation',
      'screenshare',
      'graphic',
      'document',
      'webpage',
    ];
    for (const kind of kinds) {
      const executed = await service.execute(
        's',
        cmd(producer, { type: 'SET_PREVIEW', source: { kind, id: `src-${kind}` } }),
      );
      expect(executed.result.ok).toBe(true);
    }
  });
});

describe('TAKE (AC-REGIE-002, AC-REGIE-003)', () => {
  const ready = async () => {
    const service = newService();
    await service.execute('s', cmd(producer, { type: 'CUT', source: group }));
    await service.execute('s', cmd(producer, { type: 'SET_PREVIEW', source: slides }));
    return service;
  };

  it('fait passer la Preview prête en Program, une seule fois, et audite', async () => {
    const service = await ready();
    await service.execute(
      's',
      cmd(loader, { type: 'REPORT_ASSET', assetId: 'asset-slides', status: 'READY' }),
    );
    const taken = await service.execute(
      's',
      cmd(producer, { type: 'TAKE', expectPreviewId: 'slides-1' }),
    );
    expect(taken.result.ok).toBe(true);
    const state = await service.state('s');
    expect(state.program).toEqual(slides);
    expect(state.preview).toEqual(group);
    const changes = (await service.auditLog('s')).filter((e) => e.type === 'ProgramSceneChanged');
    expect(changes.map((e) => e.details['to'])).toEqual(['scene-group', 'slides-1']);
  });

  it('refuse le TAKE tant que le média charge, sans toucher au Program', async () => {
    const service = await ready();
    const rejected = await service.execute(
      's',
      cmd(producer, { type: 'TAKE', expectPreviewId: 'slides-1' }),
    );
    expect(errorCode(rejected)).toBe('PREVIEW_NOT_READY');
    expect((await service.state('s')).program).toEqual(group);
  });

  it('une erreur de chargement en Preview ne remplace pas le Program', async () => {
    const service = await ready();
    await service.execute(
      's',
      cmd(loader, { type: 'REPORT_ASSET', assetId: 'asset-slides', status: 'ERROR' }),
    );
    const rejected = await service.execute(
      's',
      cmd(producer, { type: 'TAKE', expectPreviewId: 'slides-1' }),
    );
    expect(errorCode(rejected)).toBe('PREVIEW_NOT_READY');
    expect((await service.state('s')).program).toEqual(group);
    // On peut ensuite passer en Program une source valide.
    await service.execute(
      's',
      cmd(producer, { type: 'SET_PREVIEW', source: { kind: 'scene', id: 'scene-duo' } }),
    );
    const retry = await service.execute(
      's',
      cmd(producer, { type: 'TAKE', expectPreviewId: 'scene-duo' }),
    );
    expect(retry.result.ok).toBe(true);
  });

  it('signale sans le changer le Program dont le média tombe en erreur', async () => {
    const service = newService();
    await service.execute(
      's',
      cmd(loader, { type: 'REPORT_ASSET', assetId: 'asset-clip', status: 'READY' }),
    );
    await service.execute('s', cmd(producer, { type: 'CUT', source: clip }));
    await service.execute(
      's',
      cmd(loader, { type: 'REPORT_ASSET', assetId: 'asset-clip', status: 'ERROR' }),
    );
    expect((await service.state('s')).program).toEqual(clip);
    const alerts = (await service.auditLog('s')).filter((e) => e.type === 'ProgramAssetError');
    expect(alerts).toHaveLength(1);
  });

  it('refuse un TAKE quand la Preview est vide', async () => {
    const service = newService();
    const rejected = await service.execute(
      's',
      cmd(producer, { type: 'TAKE', expectPreviewId: 'x' }),
    );
    expect(errorCode(rejected)).toBe('NOTHING_IN_PREVIEW');
  });
});

describe('permissions côté serveur (AC-REGIE-005, AC-SEC-002)', () => {
  const commands = (actor: Actor): Command[] => [
    cmd(actor, { type: 'SET_PREVIEW', source: group }),
    cmd(actor, { type: 'TAKE', expectPreviewId: 'scene-group' }),
    cmd(actor, { type: 'CUT', source: group }),
    cmd(actor, { type: 'START_RECORDING', sessionId: 'rec-1' }),
    cmd(actor, { type: 'STOP_RECORDING' }),
    cmd(actor, { type: 'SET_AUTO_DIRECTOR', on: true }),
    cmd(actor, { type: 'SHOW_OVERLAY', overlayId: 'lower-third' }),
  ];

  it.each([
    ['un invité', guest],
    ['un éditeur', editor],
    ['un agent MCP sans rôle de régie', mcpGuest],
    ['un Host quand la politique ne l’autorise pas', host],
  ])('refuse à %s toute commande de régie, sans modifier l’état', async (_label, actor) => {
    const service = newService();
    for (const command of commands(actor)) {
      const executed = await service.execute('s', command);
      expect(errorCode(executed)).toBe('FORBIDDEN');
    }
    expect(await service.state('s')).toEqual(initialState('s'));
    expect((await service.auditLog('s')).every((e) => e.type === 'CommandRejected')).toBe(true);
  });

  it('autorise un Host quand la politique le permet, sauf l’enregistrement', async () => {
    const service = newService({ hostsMayControl: true, requiredConsentFrom: [] });
    expect((await service.execute('s', cmd(host, { type: 'CUT', source: group }))).result.ok).toBe(
      true,
    );
    const recording = await service.execute(
      's',
      cmd(host, { type: 'START_RECORDING', sessionId: 'rec-1' }),
    );
    expect(errorCode(recording)).toBe('FORBIDDEN');
  });

  it('seul un participant peut donner son propre consentement', async () => {
    const service = newService();
    const forged = await service.execute(
      's',
      cmd(producer, { type: 'GRANT_CONSENT', participantId: 'invite' }),
    );
    const own = await service.execute(
      's',
      cmd(guest, { type: 'GRANT_CONSENT', participantId: 'invite' }),
    );
    expect(errorCode(forged)).toBe('FORBIDDEN');
    expect(own.result.ok).toBe(true);
  });

  it('seul le système peut rapporter l’état d’un média', async () => {
    const service = newService();
    const executed = await service.execute(
      's',
      cmd(producer, { type: 'REPORT_ASSET', assetId: 'a', status: 'READY' }),
    );
    expect(errorCode(executed)).toBe('FORBIDDEN');
  });
});

describe('commandes en double ou concurrentes (AC-REGIE-006, AC-REC-009)', () => {
  it('rejouer la même commande ne l’exécute pas deux fois', async () => {
    const service = newService();
    await service.execute('s', cmd(producer, { type: 'CUT', source: group }));
    await service.execute(
      's',
      cmd(producer, { type: 'SET_PREVIEW', source: { kind: 'scene', id: 'scene-duo' } }),
    );
    const take = cmd(
      producer,
      { type: 'TAKE', expectPreviewId: 'scene-duo' },
      { commandId: 'take-1' },
    );
    const first = await service.execute('s', take);
    const second = await service.execute('s', take);
    expect(first.replayed).toBe(false);
    expect(second.replayed).toBe(true);
    expect(second.result).toEqual(first.result);
    const taken = (await service.auditLog('s')).filter((e) => e.commandId === 'take-1');
    expect(taken).toHaveLength(1);
    expect((await service.state('s')).program?.id).toBe('scene-duo');
  });

  it('deux TAKE différents sur la même Preview : un seul réussit', async () => {
    const service = newService(undefined, true);
    await service.execute('s', cmd(producer, { type: 'CUT', source: group }));
    await service.execute(
      's',
      cmd(producer, { type: 'SET_PREVIEW', source: { kind: 'scene', id: 'scene-duo' } }),
    );
    const results = await Promise.all([
      service.execute('s', cmd(producer, { type: 'TAKE', expectPreviewId: 'scene-duo' })),
      service.execute('s', cmd(producer, { type: 'TAKE', expectPreviewId: 'scene-duo' })),
    ]);
    expect(results.filter((r) => r.result.ok)).toHaveLength(1);
    expect(results.map((r) => errorCode(r)).filter(Boolean)).toEqual(['PREVIEW_CHANGED']);
    const state = await service.state('s');
    expect(state.program?.id).toBe('scene-duo');
    expect(state.preview?.id).toBe('scene-group');
  });

  it('la même commande envoyée deux fois en même temps n’agit qu’une fois', async () => {
    const service = newService(undefined, true);
    const start = cmd(
      producer,
      { type: 'START_RECORDING', sessionId: 'rec-1' },
      { commandId: 'start-1' },
    );
    const [a, b] = await Promise.all([service.execute('s', start), service.execute('s', start)]);
    expect([a.replayed, b.replayed].sort()).toEqual([false, true]);
    const starts = (await service.auditLog('s')).filter((e) => e.type === 'RecordingStarted');
    expect(starts).toHaveLength(1);
  });

  it('deux START_RECORDING différents : une seule session active', async () => {
    const service = newService(undefined, true);
    const results = await Promise.all([
      service.execute('s', cmd(producer, { type: 'START_RECORDING', sessionId: 'rec-A' })),
      service.execute('s', cmd(producer, { type: 'START_RECORDING', sessionId: 'rec-B' })),
    ]);
    expect(results.filter((r) => r.result.ok)).toHaveLength(1);
    expect(results.map((r) => errorCode(r)).filter(Boolean)).toEqual(['ALREADY_RECORDING']);
    const state = await service.state('s');
    expect(state.recording.status).toBe('RECORDING');
  });

  it('cinquante commandes concurrentes laissent un état cohérent et un journal ordonné', async () => {
    const service = newService(undefined, true);
    const executed = await Promise.all(
      Array.from({ length: 50 }, (_, i) =>
        service.execute(
          's',
          cmd(producer, { type: 'CUT', source: { kind: 'scene', id: `scene-${String(i)}` } }),
        ),
      ),
    );
    expect(executed.every((e) => e.result.ok)).toBe(true);
    const state = await service.state('s');
    expect(state.version).toBe(50);
    const log = await service.auditLog('s');
    expect(log.map((e) => e.seq)).toEqual(Array.from({ length: log.length }, (_, i) => i + 1));
    expect(new Set(log.map((e) => e.commandId)).size).toBe(50);
  });

  it('deux processus qui écrivent en même temps : la version optimiste évite tout état incohérent', async () => {
    const store = new InMemoryStudioStore({ yieldBeforeCommit: true });
    const processes = Array.from({ length: 5 }, () => new StudioService(store));
    const executed = await Promise.all(
      Array.from({ length: 50 }, (_, i) =>
        pick(processes, i % 5).execute(
          's',
          cmd(producer, { type: 'CUT', source: { kind: 'scene', id: `scene-${String(i)}` } }),
        ),
      ),
    );
    expect(executed.every((e) => e.result.ok)).toBe(true);
    const state = await pick(processes, 0).state('s');
    expect(state.version).toBe(50);
    const log = await pick(processes, 0).auditLog('s');
    expect(log.map((e) => e.seq)).toEqual(Array.from({ length: 50 }, (_, i) => i + 1));
  });

  it('deux processus qui démarrent l’enregistrement ensemble : une seule session', async () => {
    const store = new InMemoryStudioStore({ yieldBeforeCommit: true });
    const [a, b] = [new StudioService(store), new StudioService(store)];
    const results = await Promise.all([
      a.execute('s', cmd(producer, { type: 'START_RECORDING', sessionId: 'rec-A' })),
      b.execute('s', cmd(producer, { type: 'START_RECORDING', sessionId: 'rec-B' })),
    ]);
    expect(results.filter((r) => r.result.ok)).toHaveLength(1);
    expect(results.map((r) => errorCode(r)).filter(Boolean)).toEqual(['ALREADY_RECORDING']);
  });

  it('la même commande reçue par deux processus n’agit qu’une fois', async () => {
    const store = new InMemoryStudioStore({ yieldBeforeCommit: true });
    const [a, b] = [new StudioService(store), new StudioService(store)];
    const command = cmd(producer, { type: 'CUT', source: group }, { commandId: 'same' });
    const [x, y] = await Promise.all([a.execute('s', command), b.execute('s', command)]);
    expect([x.replayed, y.replayed].sort()).toEqual([false, true]);
    expect((await a.auditLog('s')).filter((e) => e.commandId === 'same')).toHaveLength(1);
  });

  it('refuse une commande fondée sur une version périmée', async () => {
    const service = newService();
    await service.execute('s', cmd(producer, { type: 'CUT', source: group }));
    const stale = await service.execute(
      's',
      cmd(producer, { type: 'SET_PREVIEW', source: slides }, { expectedVersion: 0 }),
    );
    expect(errorCode(stale)).toBe('STALE_VERSION');
    const fresh = await service.execute(
      's',
      cmd(producer, { type: 'SET_PREVIEW', source: slides }, { expectedVersion: 1 }),
    );
    expect(fresh.result.ok).toBe(true);
  });
});

describe('enregistrement, consentement et séquences (AC-REC-008, AC-REC-010, AC-RUNDOWN-003)', () => {
  it('démarre puis arrête, avec la durée dans l’audit', async () => {
    const service = newService();
    await service.execute(
      's',
      cmd(producer, { type: 'START_RECORDING', sessionId: 'rec-1' }, { atMs: 10_000 }),
    );
    expect((await service.state('s')).recording).toEqual({
      status: 'RECORDING',
      sessionId: 'rec-1',
      startedAtMs: 10_000,
    });
    const stopped = await service.execute(
      's',
      cmd(producer, { type: 'STOP_RECORDING' }, { atMs: 70_000 }),
    );
    expect(stopped.events[0]?.details).toEqual({ sessionId: 'rec-1', durationMs: 60_000 });
    expect((await service.state('s')).recording).toEqual({
      status: 'IDLE',
      lastSessionId: 'rec-1',
    });
  });

  it('refuse d’arrêter ce qui n’a pas démarré', async () => {
    const service = newService();
    expect(errorCode(await service.execute('s', cmd(producer, { type: 'STOP_RECORDING' })))).toBe(
      'NOT_RECORDING',
    );
  });

  it('exige le consentement des participants requis avant de démarrer', async () => {
    const service = newService({ hostsMayControl: false, requiredConsentFrom: ['invite', 'sam'] });
    const refused = await service.execute(
      's',
      cmd(producer, { type: 'START_RECORDING', sessionId: 'rec-1' }),
    );
    expect(errorCode(refused)).toBe('CONSENT_REQUIRED');
    await service.execute('s', cmd(guest, { type: 'GRANT_CONSENT', participantId: 'invite' }));
    expect(
      errorCode(
        await service.execute('s', cmd(producer, { type: 'START_RECORDING', sessionId: 'rec-1' })),
      ),
    ).toBe('CONSENT_REQUIRED');
    await service.execute('s', cmd(host, { type: 'GRANT_CONSENT', participantId: 'sam' }));
    expect(
      (await service.execute('s', cmd(producer, { type: 'START_RECORDING', sessionId: 'rec-1' })))
        .result.ok,
    ).toBe(true);
  });

  it('changer de séquence ne coupe pas l’enregistrement', async () => {
    const service = newService();
    await service.execute('s', cmd(producer, { type: 'START_RECORDING', sessionId: 'rec-1' }));
    await service.execute('s', cmd(producer, { type: 'SET_SEQUENCE', sequenceId: 'seq-2' }));
    const state = await service.state('s');
    expect(state.currentSequenceId).toBe('seq-2');
    expect(state.recording.status).toBe('RECORDING');
  });
});

describe('réalisateur automatique et réalisation manuelle (AC-SPK-005)', () => {
  it('refuse une coupure automatique quand le réalisateur automatique est arrêté', async () => {
    const service = newService();
    const executed = await service.execute('s', cmd(auto, { type: 'CUT', source: group }));
    expect(errorCode(executed)).toBe('AUTO_DIRECTOR_OFF');
  });

  it('accepte une coupure automatique quand il est actif', async () => {
    const service = newService();
    await service.execute('s', cmd(producer, { type: 'SET_AUTO_DIRECTOR', on: true }));
    const executed = await service.execute('s', cmd(auto, { type: 'CUT', source: group }));
    expect(executed.result.ok).toBe(true);
  });

  it('une coupure manuelle arrête le réalisateur automatique, dont les décisions périmées sont alors refusées', async () => {
    const service = newService();
    await service.execute('s', cmd(producer, { type: 'SET_AUTO_DIRECTOR', on: true }));
    await service.execute('s', cmd(producer, { type: 'CUT', source: group }));
    expect((await service.state('s')).autoDirector).toBe(false);
    const stale = await service.execute(
      's',
      cmd(auto, { type: 'CUT', source: { kind: 'scene', id: 'scene-focus-a' } }),
    );
    expect(errorCode(stale)).toBe('AUTO_DIRECTOR_OFF');
    expect((await service.state('s')).program).toEqual(group);
  });

  it('le réalisateur automatique ne peut rien faire d’autre que couper', async () => {
    const service = newService();
    await service.execute('s', cmd(producer, { type: 'SET_AUTO_DIRECTOR', on: true }));
    const attempts = [
      cmd(auto, { type: 'TAKE', expectPreviewId: 'x' }),
      cmd(auto, { type: 'START_RECORDING', sessionId: 'rec-1' }),
      cmd(auto, { type: 'SET_AUTO_DIRECTOR', on: false }),
    ];
    for (const attempt of attempts) {
      expect(errorCode(await service.execute('s', attempt))).toBe('FORBIDDEN');
    }
  });
});

describe('audit (AC-SEC-007)', () => {
  it('journalise chaque commande, acceptée ou refusée, avec son auteur', async () => {
    const service = newService();
    await service.execute(
      's',
      cmd(producer, { type: 'CUT', source: group }, { commandId: 'ok-1' }),
    );
    await service.execute('s', cmd(guest, { type: 'CUT', source: group }, { commandId: 'ko-1' }));
    const log = await service.auditLog('s');
    expect(log.map((e) => [e.commandId, e.actorId, e.type])).toEqual([
      ['ok-1', 'lou', 'ProgramSceneChanged'],
      ['ko-1', 'invite', 'CommandRejected'],
    ]);
    for (const entry of log) {
      expect(entry.atMs).toBeGreaterThan(0);
      expect(entry.seq).toBeGreaterThan(0);
    }
  });

  it('les erreurs de validation et de permission ne sont pas à réessayer, les autres si', () => {
    const state = initialState('s');
    const forbidden = handleCommand(state, cmd(guest, { type: 'CUT', source: group }));
    const stale = handleCommand(
      state,
      cmd(producer, { type: 'CUT', source: group }, { expectedVersion: 9 }),
    );
    expect(!forbidden.ok && forbidden.error.retryable).toBe(false);
    expect(!stale.ok && stale.error.retryable).toBe(true);
  });
});

describe('performance du traitement d’une commande (AC-PERF-003, partie métier)', () => {
  it('traite 100 000 TAKE en moins de 2 secondes', () => {
    let state = initialState('s');
    const setup = handleCommand(state, cmd(producer, { type: 'CUT', source: group }));
    if (setup.ok) state = setup.state;
    const startedAt = performance.now();
    for (let i = 0; i < 100_000; i++) {
      const preview = handleCommand(
        state,
        cmd(producer, { type: 'SET_PREVIEW', source: { kind: 'scene', id: `s-${String(i % 2)}` } }),
      );
      if (preview.ok) state = preview.state;
      const take = handleCommand(
        state,
        cmd(producer, { type: 'TAKE', expectPreviewId: `s-${String(i % 2)}` }),
      );
      if (take.ok) state = take.state;
    }
    expect(performance.now() - startedAt).toBeLessThan(2000);
  });
});
