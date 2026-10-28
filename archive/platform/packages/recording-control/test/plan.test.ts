import { describe, expect, it } from 'vitest';
import {
  planRecording,
  type EgressFiles,
  type EgressRecord,
  type ObservedRecordingState,
  type PublishedTrack,
  type RecordingAction,
} from '../src';

const track = (sid: string, kind: 'audio' | 'video' = 'video'): PublishedTrack => ({
  sid,
  participantId: `p-${sid}`,
  kind,
});
const egress = (
  egressId: string,
  trackSid: string,
  status: EgressRecord['status'],
  startedAtMs = 50_000,
): EgressRecord => ({ egressId, trackSid, status, startedAtMs });
const files = (egressId: string, overrides: Partial<EgressFiles> = {}): EgressFiles => ({
  egressId,
  workingFile: false,
  localOutput: false,
  verifiedInStorage: false,
  ...overrides,
});

function observed(overrides: Partial<ObservedRecordingState> = {}): ObservedRecordingState {
  return {
    nowMs: 100_000,
    recordingActive: true,
    tracks: [],
    egresses: [],
    files: [],
    workerHealthy: true,
    workerStartedAtMs: 1_000,
    unpublishedSince: {},
    ...overrides,
  };
}

const ofType = <T extends RecordingAction['type']>(
  actions: readonly RecordingAction[],
  type: T,
): Extract<RecordingAction, { type: T }>[] =>
  actions.filter((a): a is Extract<RecordingAction, { type: T }> => a.type === type);

describe('planRecording : démarrage', () => {
  it('démarre un egress pour chaque piste publiée sans egress pendant l’enregistrement', () => {
    const plan = planRecording(observed({ tracks: [track('T1'), track('T2', 'audio')] }));
    expect(ofType(plan.actions, 'START_EGRESS').map((a) => a.trackSid)).toEqual(['T1', 'T2']);
    expect(plan.tracks.map((t) => t.state)).toEqual(['MISSING', 'MISSING']);
  });

  it('ne démarre rien quand l’enregistrement n’est pas actif', () => {
    const plan = planRecording(observed({ recordingActive: false, tracks: [track('T1')] }));
    expect(ofType(plan.actions, 'START_EGRESS')).toEqual([]);
    expect(plan.tracks[0]?.state).toBeNull();
  });

  it('ne redémarre pas une piste déjà couverte par un egress actif', () => {
    const plan = planRecording(
      observed({ tracks: [track('T1')], egresses: [egress('E1', 'T1', 'ACTIVE')] }),
    );
    expect(ofType(plan.actions, 'START_EGRESS')).toEqual([]);
    expect(plan.tracks[0]?.state).toBe('AT_RISK');
  });

  it('démarre un nouvel egress quand un participant revient avec de nouvelles pistes', () => {
    const plan = planRecording(
      observed({
        tracks: [track('T1-bis')],
        egresses: [egress('E1', 'T1', 'COMPLETE')],
        files: [files('E1', { verifiedInStorage: true })],
      }),
    );
    expect(ofType(plan.actions, 'START_EGRESS').map((a) => a.trackSid)).toEqual(['T1-bis']);
    expect(plan.segments).toEqual([{ egressId: 'E1', trackSid: 'T1', state: 'SAFE' }]);
  });

  it('ne démarre pas d’egress quand le worker est arrêté et alerte', () => {
    const plan = planRecording(observed({ tracks: [track('T1')], workerHealthy: false }));
    expect(ofType(plan.actions, 'START_EGRESS')).toEqual([]);
    expect(ofType(plan.actions, 'ALERT').map((a) => a.code)).toContain('TRACK_NOT_RECORDED');
  });
});

describe('planRecording : arrêt', () => {
  it('arrête les egress vivants quand l’enregistrement s’arrête', () => {
    const plan = planRecording(
      observed({
        recordingActive: false,
        tracks: [track('T1')],
        egresses: [egress('E1', 'T1', 'ACTIVE'), egress('E2', 'T2', 'STARTING')],
      }),
    );
    expect(ofType(plan.actions, 'STOP_EGRESS')).toEqual([
      { type: 'STOP_EGRESS', egressId: 'E1', reason: 'RECORDING_STOPPED' },
      { type: 'STOP_EGRESS', egressId: 'E2', reason: 'RECORDING_STOPPED' },
    ]);
  });

  it('arrête un egress actif dont la piste a disparu depuis plus que le délai de grâce', () => {
    const plan = planRecording(
      observed({
        tracks: [],
        egresses: [egress('E1', 'T1', 'ACTIVE')],
        unpublishedSince: { T1: 80_000 },
      }),
    );
    expect(ofType(plan.actions, 'STOP_EGRESS')).toEqual([
      { type: 'STOP_EGRESS', egressId: 'E1', reason: 'STUCK' },
    ]);
  });

  it('attend le délai de grâce avant d’arrêter un egress dont la piste vient de disparaître', () => {
    const plan = planRecording(
      observed({
        egresses: [egress('E1', 'T1', 'ACTIVE')],
        unpublishedSince: { T1: 95_000 },
      }),
    );
    expect(ofType(plan.actions, 'STOP_EGRESS')).toEqual([]);
  });
});

describe('planRecording : états de sécurité', () => {
  it('ne déclare SAFE que si le fichier est vérifié dans le stockage', () => {
    const plan = planRecording(
      observed({
        recordingActive: false,
        egresses: [egress('E1', 'T1', 'COMPLETE'), egress('E2', 'T2', 'COMPLETE')],
        files: [
          files('E1', { localOutput: true, verifiedInStorage: true }),
          files('E2', { localOutput: true }),
        ],
      }),
    );
    expect(plan.segments.map((s) => s.state)).toEqual(['SAFE', 'UPLOADING']);
    expect(ofType(plan.actions, 'UPLOAD')).toEqual([{ type: 'UPLOAD', egressId: 'E2' }]);
  });

  it('signale un egress terminé sans aucun fichier', () => {
    const plan = planRecording(
      observed({ recordingActive: false, egresses: [egress('E1', 'T1', 'COMPLETE')] }),
    );
    expect(plan.segments[0]?.state).toBe('FAILED');
    expect(ofType(plan.actions, 'ALERT').map((a) => a.code)).toEqual([
      'EGRESS_COMPLETE_WITHOUT_FILE',
    ]);
  });

  it('classe RECOVERABLE un egress en échec dont le fichier de travail existe', () => {
    const plan = planRecording(
      observed({
        recordingActive: false,
        egresses: [egress('E1', 'T1', 'FAILED')],
        files: [files('E1', { workingFile: true })],
      }),
    );
    expect(plan.segments[0]?.state).toBe('RECOVERABLE');
    expect(ofType(plan.actions, 'RUN_RECOVERY')).toEqual([
      { type: 'RUN_RECOVERY', egressIds: ['E1'] },
    ]);
  });

  it('classe FAILED un egress en échec sans aucun fichier et alerte', () => {
    const plan = planRecording(
      observed({ recordingActive: false, egresses: [egress('E1', 'T1', 'FAILED')] }),
    );
    expect(plan.segments[0]?.state).toBe('FAILED');
    expect(ofType(plan.actions, 'ALERT').map((a) => a.code)).toEqual(['EGRESS_FAILED']);
  });

  it('retient le pire état parmi les segments d’une même piste', () => {
    const plan = planRecording(
      observed({
        recordingActive: false,
        tracks: [track('T1')],
        egresses: [egress('E1', 'T1', 'COMPLETE'), egress('E2', 'T1', 'FAILED')],
        files: [files('E1', { verifiedInStorage: true })],
      }),
    );
    expect(plan.tracks[0]?.state).toBe('FAILED');
  });
});

describe('planRecording : crash du worker (POC 3, S3)', () => {
  const crashed = (extra: Partial<ObservedRecordingState> = {}): ObservedRecordingState =>
    observed({
      tracks: [track('T1'), track('T2', 'audio')],
      egresses: [egress('E1', 'T1', 'ACTIVE'), egress('E2', 'T2', 'ACTIVE')],
      files: [files('E1', { workingFile: true }), files('E2', { workingFile: true })],
      workerHealthy: false,
      ...extra,
    });

  it('ne se fie pas au statut ACTIVE : RECOVERABLE avec alerte ZOMBIE_EGRESS', () => {
    const plan = planRecording(crashed());
    expect(plan.segments.map((s) => s.state)).toEqual(['RECOVERABLE', 'RECOVERABLE']);
    const codes = ofType(plan.actions, 'ALERT').map((a) => a.code);
    expect(codes).toContain('WORKER_DOWN');
    expect(codes.filter((c) => c === 'ZOMBIE_EGRESS')).toHaveLength(2);
  });

  it('récupère les fichiers avant de redémarrer le worker', () => {
    const plan = planRecording(crashed());
    expect(ofType(plan.actions, 'RUN_RECOVERY')).toEqual([
      { type: 'RUN_RECOVERY', egressIds: ['E1', 'E2'] },
    ]);
    expect(ofType(plan.actions, 'RESTART_WORKER')).toEqual([]);
  });

  it('redémarre le worker une fois les fichiers récupérés', () => {
    const plan = planRecording(
      crashed({
        files: [files('E1', { localOutput: true }), files('E2', { localOutput: true })],
      }),
    );
    expect(ofType(plan.actions, 'RUN_RECOVERY')).toEqual([]);
    expect(ofType(plan.actions, 'RESTART_WORKER')).toHaveLength(1);
    expect(plan.segments.map((s) => s.state)).toEqual(['UPLOADING', 'UPLOADING']);
    expect(ofType(plan.actions, 'UPLOAD').map((a) => a.egressId)).toEqual(['E1', 'E2']);
  });

  it('classe MISSING un egress actif sans worker et sans aucun fichier', () => {
    const plan = planRecording(crashed({ files: [] }));
    expect(plan.segments.map((s) => s.state)).toEqual(['MISSING', 'MISSING']);
    expect(ofType(plan.actions, 'RESTART_WORKER')).toHaveLength(1);
  });
});

describe('planRecording : après le redémarrage du worker', () => {
  const restarted = (extra: Partial<ObservedRecordingState> = {}): ObservedRecordingState =>
    observed({
      tracks: [track('T1')],
      // LiveKit affiche encore l'ancien egress comme actif (POC 3, S3).
      egresses: [egress('E1', 'T1', 'ACTIVE', 50_000)],
      files: [files('E1', { verifiedInStorage: true })],
      workerStartedAtMs: 90_000,
      ...extra,
    });

  it('ne compte pas un egress démarré avant le worker comme enregistrant la piste', () => {
    const plan = planRecording(restarted());
    expect(ofType(plan.actions, 'START_EGRESS').map((a) => a.trackSid)).toEqual(['T1']);
  });

  it('garde SAFE le segment récupéré et vérifié, malgré le statut ACTIVE', () => {
    const plan = planRecording(restarted());
    expect(plan.segments).toEqual([{ egressId: 'E1', trackSid: 'T1', state: 'SAFE' }]);
  });

  it('ne tente pas d’arrêter un egress fantôme : son worker ne peut plus répondre', () => {
    const plan = planRecording(restarted());
    expect(ofType(plan.actions, 'STOP_EGRESS')).toEqual([]);
  });

  it('relance le worker et l’enregistrement avant l’envoi des fichiers', () => {
    const plan = planRecording(
      observed({
        tracks: [track('T1')],
        egresses: [egress('E1', 'T1', 'ACTIVE', 50_000)],
        files: [files('E1', { localOutput: true })],
        workerHealthy: false,
      }),
    );
    const order = plan.actions.map((a) => a.type).filter((type) => type !== 'ALERT');
    expect(order).toEqual(['RESTART_WORKER', 'UPLOAD']);
  });

  it('compte comme vivant un egress démarré après le worker', () => {
    const plan = planRecording(
      restarted({
        egresses: [egress('E1', 'T1', 'ACTIVE', 50_000), egress('E2', 'T1', 'ACTIVE', 95_000)],
        files: [files('E1', { verifiedInStorage: true })],
      }),
    );
    expect(ofType(plan.actions, 'START_EGRESS')).toEqual([]);
    expect(plan.tracks[0]?.state).toBe('AT_RISK');
  });
});

describe('planRecording : plan vide', () => {
  it('ne produit aucune action pour un état sain', () => {
    const plan = planRecording(
      observed({ tracks: [track('T1')], egresses: [egress('E1', 'T1', 'ACTIVE')] }),
    );
    expect(plan.actions).toEqual([]);
  });
});
