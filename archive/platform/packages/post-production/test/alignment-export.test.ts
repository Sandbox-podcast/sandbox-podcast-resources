import { describe, expect, it } from 'vitest';
import {
  ExportPlanError,
  alignToReference,
  buildClipArgs,
  cancelExport,
  exportRecord,
  filePosition,
  newExportJob,
  retryExport,
  runExport,
  timelinePosition,
  type EditDecisionList,
  type ExportExecutors,
  type ExportJob,
} from '../src/index.ts';

describe('alignement sur une référence', () => {
  const marks = Array.from({ length: 60 }, (_, i) => 10 + i * 10);

  it('retrouve le décalage de départ et la dérive', () => {
    // Le fichier commence 2,5 s après la référence et son horloge avance de 40 ppm plus vite.
    const file = marks.map((t) => (t - 2.5) * (1 + 40e-6));
    const alignment = alignToReference('a1', marks, file, { maxGapSec: 4, minMarkers: 10 });
    expect(alignment.offsetSec).toBeCloseTo(2.5, 6);
    expect(alignment.driftPpm).toBeCloseTo(40, 3);
    expect(alignment.markers).toBe(60);
    expect(alignment.residualRmsMs).toBeLessThan(0.001);
  });

  it('un fichier qui commence avant la référence a un décalage négatif', () => {
    const file = marks.map((t) => t + 1.2);
    expect(
      alignToReference('a1', marks, file, { maxGapSec: 4, minMarkers: 10 }).offsetSec,
    ).toBeCloseTo(-1.2, 6);
  });

  it('tolère un repère manquant au milieu', () => {
    const file = marks.filter((_, i) => i !== 20).map((t) => t - 1);
    const alignment = alignToReference('a1', marks, file, { maxGapSec: 4, minMarkers: 10 });
    expect(alignment.markers).toBe(59);
    expect(alignment.offsetSec).toBeCloseTo(1, 6);
  });

  it('refuse un alignement fondé sur trop peu de repères', () => {
    expect(() =>
      alignToReference('a1', marks, marks.slice(0, 5), { maxGapSec: 4, minMarkers: 10 }),
    ).toThrow(/5 repère/);
    expect(() => alignToReference('a1', marks, [], { maxGapSec: 4, minMarkers: 10 })).toThrow(
      /0 repère/,
    );
  });

  it('positions : aller-retour entre ligne de temps et fichier', () => {
    const a = { offsetSec: 2.5, driftPpm: 40 };
    expect(filePosition(a, 12.5)).toBeCloseTo(10 * (1 + 40e-6), 9);
    expect(timelinePosition(a, filePosition(a, 123.4))).toBeCloseTo(123.4, 9);
    expect(filePosition({ offsetSec: 0, driftPpm: 0 }, 7)).toBe(7);
  });
});

const edl: EditDecisionList = {
  version: 3,
  episodeId: 'ep-1',
  tracks: [
    {
      trackId: 'v1',
      kind: 'video',
      participantId: 'ana',
      sourcePath: '/src/ana.mp4',
      offsetSec: 0,
      driftPpm: 0,
      markers: 100,
      residualRmsMs: 1,
    },
    {
      trackId: 'a1',
      kind: 'audio',
      participantId: 'ana',
      sourcePath: '/src/ana.ogg',
      offsetSec: 0.2,
      driftPpm: 38,
      markers: 100,
      residualRmsMs: 1,
    },
    {
      trackId: 'a2',
      kind: 'audio',
      participantId: 'ben',
      sourcePath: '/src/ben.ogg',
      offsetSec: 1.5,
      driftPpm: 0,
      markers: 100,
      residualRmsMs: 1,
    },
  ],
};

const plan = (extra: object = {}) => ({
  edl,
  startSec: 60,
  endSec: 90,
  videoTrackId: 'v1',
  audioTrackIds: ['a1', 'a2'],
  format: '9:16' as const,
  crop: { x: 656, y: 0, width: 608, height: 1080 },
  outputPath: '/tmp/export/out.mp4',
  ...extra,
});

const after = (args: string[], flag: string, occurrence = 0): string | undefined => {
  const index = args.reduce<number[]>((acc, a, i) => (a === flag ? [...acc, i] : acc), [])[
    occurrence
  ];
  return index === undefined ? undefined : args[index + 1];
};

describe('arguments ffmpeg d’un clip (AC-EXPORT-001, 002)', () => {
  it('positionne chaque entrée à l’endroit aligné et ne modifie aucune source', () => {
    const args = buildClipArgs(plan());
    expect(after(args, '-ss', 0)).toBe('60.000');
    expect(after(args, '-i', 0)).toBe('/src/ana.mp4');
    expect(after(args, '-ss', 1)).toBe((59.8 * (1 + 38e-6)).toFixed(3));
    expect(after(args, '-i', 1)).toBe('/src/ana.ogg');
    expect(after(args, '-ss', 2)).toBe('58.500');
    expect(args.at(-1)).toBe('/tmp/export/out.mp4');
    // La sortie est la dernière valeur ; aucune source n'apparaît comme sortie.
    expect(args.filter((a) => a.startsWith('/src/') && args.at(-1) === a)).toEqual([]);
  });

  it('recadre en 9:16, corrige la dérive audio et mixe sans normalisation automatique', () => {
    const filter = after(buildClipArgs(plan()), '-filter_complex') ?? '';
    expect(filter).toContain('[0:v]crop=608:1080:656:0,scale=1080:1920');
    expect(filter).toContain(`atempo=${(1 / (1 + 38e-6)).toFixed(9)}`);
    expect(filter).toContain('amix=inputs=2:duration=longest:normalize=0');
    expect(filter).not.toContain('loudnorm');
  });

  it('n’applique pas atempo à une piste sans dérive', () => {
    const filter = after(buildClipArgs(plan({ audioTrackIds: ['a2'] })), '-filter_complex') ?? '';
    expect(filter).not.toContain('atempo');
  });

  it('ajoute la normalisation demandée', () => {
    const filter = after(buildClipArgs(plan({ targetLufs: -16 })), '-filter_complex') ?? '';
    expect(filter).toContain('loudnorm=I=-16');
  });

  it('retarde l’audio d’un fichier qui commence après le départ du clip', () => {
    const args = buildClipArgs(plan({ startSec: 1, endSec: 31 }));
    // a2 commence à 1,5 s de la ligne de temps : au départ (1 s) il manque 0,5 s.
    expect(after(args, '-ss', 2)).toBe('0.000');
    expect(after(args, '-filter_complex')).toContain('adelay=500:all=1');
  });

  it('16:9 sans recadrage, avec sortie 1920x1080', () => {
    const filter =
      after(buildClipArgs(plan({ format: '16:9', crop: undefined })), '-filter_complex') ?? '';
    expect(filter).toContain('[0:v]scale=1920:1080');
    expect(filter).not.toContain('crop=');
  });

  it.each([
    ['durée nulle', { endSec: 60 }, /durée/],
    ['piste vidéo inconnue', { videoTrackId: 'zz' }, /inconnue/],
    ['une piste audio donnée comme vidéo', { videoTrackId: 'a1' }, /pas une piste vidéo/],
    ['une piste vidéo donnée comme audio', { audioTrackIds: ['v1'] }, /pas une piste audio/],
    ['aucune piste audio', { audioTrackIds: [] }, /aucune piste audio/],
    ['recadrage manquant en 9:16', { crop: undefined }, /recadrage/],
    ['clip avant le début de la vidéo', { startSec: -5, endSec: 20 }, /avant le début/],
  ])('refuse : %s', (_label, extra, message) => {
    expect(() => buildClipArgs(plan(extra))).toThrow(ExportPlanError);
    expect(() => buildClipArgs(plan(extra))).toThrow(message);
  });

  it('ne passe jamais par un shell : tout est un tableau d’arguments sans guillemets', () => {
    const hostile = plan({ outputPath: "/tmp/x; rm -rf / '.mp4" });
    const args = buildClipArgs(hostile);
    expect(args.at(-1)).toBe("/tmp/x; rm -rf / '.mp4");
    expect(Array.isArray(args)).toBe(true);
  });
});

describe('tâche d’export (AC-EXPORT-003, 004, 005)', () => {
  const job = (): ExportJob =>
    newExportJob({
      id: 'x1',
      episodeId: 'ep-1',
      presetVersion: 2,
      editDecisionVersion: 3,
      sourceTrackIds: ['v1', 'a1', 'a2'],
      createdAt: 1700000000000,
      createdBy: 'lou',
      tempDir: '/exports/tmp/x1',
      outputPath: '/exports/tmp/x1/out.mp4',
    });

  function executors(overrides: Partial<ExportExecutors> = {}) {
    const calls: string[] = [];
    const removed: string[][] = [];
    const base: ExportExecutors = {
      render: () => {
        calls.push('render');
        return Promise.resolve();
      },
      verify: () => {
        calls.push('verify');
        return Promise.resolve();
      },
      checksum: () => {
        calls.push('checksum');
        return Promise.resolve('abc123');
      },
      remove: (paths) => {
        removed.push([...paths]);
        return Promise.resolve();
      },
    };
    return { executors: { ...base, ...overrides }, calls, removed };
  }

  it('exécute les étapes dans l’ordre et conserve la traçabilité', async () => {
    const { executors: ex, calls } = executors();
    const done = await runExport(job(), ex);
    expect(done.status).toBe('SUCCEEDED');
    expect(calls).toEqual(['render', 'verify', 'checksum']);
    expect(exportRecord(done)).toEqual({
      episodeId: 'ep-1',
      presetVersion: 2,
      editDecisionVersion: 3,
      sourceTrackIds: ['v1', 'a1', 'a2'],
      createdAt: 1700000000000,
      createdBy: 'lou',
      checksum: 'abc123',
    });
  });

  it('pas de traçabilité tant que l’export n’a pas réussi', async () => {
    expect(exportRecord(job())).toBeNull();
    const { executors: ex } = executors({
      verify: () => Promise.reject(new Error('durée incorrecte')),
    });
    expect(exportRecord(await runExport(job(), ex))).toBeNull();
  });

  it('la traçabilité n’est donnée que pour un export réussi, même si une empreinte est présente', async () => {
    const done = await runExport(job(), executors().executors);
    expect(exportRecord({ ...done, status: 'CANCELLED' })).toBeNull();
    expect(exportRecord({ ...done, status: 'FAILED' })).toBeNull();
    expect(exportRecord(done)).not.toBeNull();
  });

  it('un échec de vérification n’oblige pas à rendre à nouveau (reprise par étapes)', async () => {
    let verifyCalls = 0;
    const { executors: ex, calls } = executors({
      verify: () => {
        verifyCalls += 1;
        return verifyCalls === 1 ? Promise.reject(new Error('fichier tronqué')) : Promise.resolve();
      },
    });
    const failed = await runExport(job(), ex);
    expect(failed.status).toBe('FAILED');
    expect(failed.steps.RENDER.status).toBe('DONE');
    expect(failed.steps.VERIFY).toEqual({
      status: 'FAILED',
      attempts: 1,
      error: 'fichier tronqué',
    });
    expect(failed.steps.CHECKSUM.status).toBe('PENDING');

    const retried = await runExport(retryExport(failed), ex);
    expect(retried.status).toBe('SUCCEEDED');
    expect(calls.filter((c) => c === 'render')).toHaveLength(1);
    expect(retried.steps.VERIFY.attempts).toBe(2);
    expect(retried.checksum).toBe('abc123');
  });

  it('un export échoué n’est pas relancé sans demande, un export réussi ne se rejoue pas', async () => {
    const { executors: ex, calls } = executors({
      render: () => Promise.reject(new Error('disque plein')),
    });
    const failed = await runExport(job(), ex);
    expect(failed.steps.RENDER).toMatchObject({ status: 'FAILED', error: 'disque plein' });
    expect(retryExport(job()).status).toBe('PENDING');
    const ok = await runExport(job(), executors().executors);
    expect(await runExport(ok, ex)).toBe(ok);
    expect(calls).toEqual([]);
  });

  it('annulation : arrête le rendu, supprime le dossier temporaire du job et rien d’autre', async () => {
    const controller = new AbortController();
    const {
      executors: ex,
      removed,
      calls,
    } = executors({
      render: (_job, signal) =>
        new Promise<void>((_resolve, reject) => {
          signal.addEventListener('abort', () => {
            reject(new Error('interrompu'));
          });
          controller.abort();
        }),
    });
    const cancelled = await runExport(job(), ex, controller.signal);
    expect(cancelled.status).toBe('CANCELLED');
    expect(removed).toEqual([['/exports/tmp/x1']]);
    expect(calls).toEqual([]);
  });

  it('annuler avant le démarrage nettoie aussi, annuler après réussite ne supprime rien', async () => {
    const { executors: ex, removed } = executors();
    const controller = new AbortController();
    controller.abort();
    expect((await runExport(job(), ex, controller.signal)).status).toBe('CANCELLED');
    expect(removed).toEqual([['/exports/tmp/x1']]);

    const done = await runExport(job(), executors().executors);
    const second = executors();
    expect(await cancelExport(done, second.executors)).toBe(done);
    expect(second.removed).toEqual([]);
  });

  it('un export annulé ne reprend pas tout seul', async () => {
    const { executors: ex, calls } = executors();
    const cancelled = await cancelExport(job(), ex);
    expect(cancelled.status).toBe('CANCELLED');
    expect(await runExport(cancelled, ex)).toBe(cancelled);
    expect(calls).toEqual([]);
  });
});
