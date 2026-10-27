import { SAFETY_STATES, type SafetyState } from '@podcast/recording-core';

/** Statuts d'un egress vus par LiveKit. `ACTIVE` ne prouve pas qu'il enregistre (POC 3, S3). */
export type EgressStatus =
  'STARTING' | 'ACTIVE' | 'ENDING' | 'COMPLETE' | 'FAILED' | 'ABORTED' | 'LIMIT_REACHED';

export interface PublishedTrack {
  sid: string;
  participantId: string;
  kind: 'audio' | 'video';
}

export interface EgressRecord {
  egressId: string;
  trackSid: string;
  status: EgressStatus;
  /** Heure de démarrage de l'egress (ms epoch), pour reconnaître ceux d'un worker disparu. */
  startedAtMs: number;
}

/** Ce que l'on observe sur disque et dans le stockage pour un egress. */
export interface EgressFiles {
  egressId: string;
  /** Fichier de travail d'Egress, en cours d'écriture ou laissé par un crash. */
  workingFile: boolean;
  /** Fichier terminé (ou récupéré) sur le disque local, pas encore vérifié dans le stockage. */
  localOutput: boolean;
  /** Fichier relu depuis le stockage et comparé par checksum. */
  verifiedInStorage: boolean;
}

export interface ObservedRecordingState {
  nowMs: number;
  /** L'enregistrement est-il demandé (START_RECORDING accepté, pas encore arrêté) ? */
  recordingActive: boolean;
  tracks: readonly PublishedTrack[];
  egresses: readonly EgressRecord[];
  files: readonly EgressFiles[];
  /** Le conteneur ou le processus Egress tourne-t-il ? Ne pas se fier au statut LiveKit. */
  workerHealthy: boolean;
  /** Heure de démarrage du worker actuel (ms epoch). Un egress plus ancien est périmé. */
  workerStartedAtMs: number;
  /** Pour une piste qui n'est plus publiée : depuis quand (ms epoch). */
  unpublishedSince: Readonly<Record<string, number>>;
}

export interface RecordingPolicy {
  /** Délai avant d'arrêter un egress `ACTIVE` dont la piste a disparu. */
  stuckGraceMs: number;
}

export const DEFAULT_POLICY: RecordingPolicy = { stuckGraceMs: 10_000 };

export type AlertCode =
  | 'WORKER_DOWN'
  | 'ZOMBIE_EGRESS'
  | 'TRACK_NOT_RECORDED'
  | 'EGRESS_FAILED'
  | 'EGRESS_COMPLETE_WITHOUT_FILE';

export type RecordingAction =
  | { type: 'START_EGRESS'; trackSid: string }
  | { type: 'STOP_EGRESS'; egressId: string; reason: 'RECORDING_STOPPED' | 'STUCK' }
  | { type: 'RUN_RECOVERY'; egressIds: string[] }
  | { type: 'RESTART_WORKER' }
  | { type: 'UPLOAD'; egressId: string }
  | { type: 'ALERT'; code: AlertCode; subject: string; message: string };

export interface SegmentState {
  egressId: string;
  trackSid: string;
  state: SafetyState;
}

export interface TrackState {
  trackSid: string;
  /** `null` : la piste n'a jamais eu d'egress et aucun enregistrement n'est demandé. */
  state: SafetyState | null;
}

export interface RecordingPlan {
  segments: SegmentState[];
  tracks: TrackState[];
  actions: RecordingAction[];
}

const severity = (state: SafetyState): number => SAFETY_STATES.indexOf(state);
const worst = (states: readonly SafetyState[]): SafetyState | null =>
  states.reduce<SafetyState | null>(
    (current, candidate) =>
      current === null || severity(candidate) > severity(current) ? candidate : current,
    null,
  );

/** Ordre d'exécution : récupérer, relancer le worker, relancer l'enregistrement, puis le reste. */
const PRIORITY: Record<RecordingAction['type'], number> = {
  RUN_RECOVERY: 0,
  RESTART_WORKER: 1,
  START_EGRESS: 2,
  STOP_EGRESS: 3,
  UPLOAD: 4,
  ALERT: 5,
};
const byPriority = (a: RecordingAction, b: RecordingAction): number =>
  PRIORITY[a.type] - PRIORITY[b.type];

const LIVE: ReadonlySet<EgressStatus> = new Set(['STARTING', 'ACTIVE', 'ENDING']);
const BROKEN: ReadonlySet<EgressStatus> = new Set(['FAILED', 'ABORTED', 'LIMIT_REACHED']);

/**
 * Décide quoi faire pour que chaque piste publiée soit enregistrée, et calcule l'état de
 * sécurité de chaque segment et de chaque piste. Fonction pure : aucune I/O.
 *
 * Règles issues du POC 3 :
 * - `SAFE` seulement si le fichier est vérifié dans le stockage.
 * - Le statut `ACTIVE` de LiveKit ne prouve rien : un egress est « périmé » (zombie) si le
 *   worker est arrêté ou s'il a été démarré avant le worker actuel. On juge alors sur les fichiers.
 * - On ne redémarre pas le worker avant d'avoir récupéré ses fichiers de travail
 *   (Egress les efface au démarrage).
 * - Un egress dont la piste a disparu (redémarrage du SFU) reste `ACTIVE` : on l'arrête.
 */
export function planRecording(
  observed: ObservedRecordingState,
  policy: RecordingPolicy = DEFAULT_POLICY,
): RecordingPlan {
  const actions: RecordingAction[] = [];
  const segments: SegmentState[] = [];
  const filesById = new Map(observed.files.map((f) => [f.egressId, f]));
  const publishedSids = new Set(observed.tracks.map((t) => t.sid));
  const alert = (code: AlertCode, subject: string, message: string): void => {
    actions.push({ type: 'ALERT', code, subject, message });
  };

  if (!observed.workerHealthy) {
    alert('WORKER_DOWN', 'egress', 'Le conteneur Egress ne tourne pas.');
  }

  const toRecover: string[] = [];
  const isZombie = (e: EgressRecord): boolean =>
    LIVE.has(e.status) && (!observed.workerHealthy || e.startedAtMs < observed.workerStartedAtMs);

  for (const egress of observed.egresses) {
    const files = filesById.get(egress.egressId);
    const hasWorking = files?.workingFile ?? false;
    const hasLocal = files?.localOutput ?? false;
    const verified = files?.verifiedInStorage ?? false;
    const zombie = isZombie(egress);
    let state: SafetyState;

    if (verified) {
      state = 'SAFE';
    } else if (egress.status === 'COMPLETE') {
      if (hasLocal) {
        state = 'UPLOADING';
        actions.push({ type: 'UPLOAD', egressId: egress.egressId });
      } else {
        state = 'FAILED';
        alert(
          'EGRESS_COMPLETE_WITHOUT_FILE',
          egress.egressId,
          'Egress terminé sans fichier récupérable.',
        );
      }
    } else if (BROKEN.has(egress.status)) {
      if (hasWorking || hasLocal) {
        state = hasWorking ? 'RECOVERABLE' : 'UPLOADING';
        if (hasWorking) toRecover.push(egress.egressId);
        else actions.push({ type: 'UPLOAD', egressId: egress.egressId });
      } else {
        state = 'FAILED';
        alert(
          'EGRESS_FAILED',
          egress.egressId,
          `Egress en échec (${egress.status}) sans fichier récupérable.`,
        );
      }
    } else if (!zombie) {
      state = 'AT_RISK';
    } else if (hasWorking) {
      state = 'RECOVERABLE';
      toRecover.push(egress.egressId);
      alert(
        'ZOMBIE_EGRESS',
        egress.egressId,
        'Egress affiché actif alors que son worker a disparu : fichiers à récupérer.',
      );
    } else if (hasLocal) {
      state = 'UPLOADING';
      actions.push({ type: 'UPLOAD', egressId: egress.egressId });
    } else {
      state = 'MISSING';
      alert(
        'ZOMBIE_EGRESS',
        egress.egressId,
        'Egress affiché actif, worker disparu, aucun fichier récupérable.',
      );
    }
    segments.push({ egressId: egress.egressId, trackSid: egress.trackSid, state });

    // Un egress périmé ne peut plus être arrêté (son worker a disparu, la requête expire) : on l'ignore.
    if (observed.workerHealthy && LIVE.has(egress.status) && !zombie) {
      if (!observed.recordingActive) {
        actions.push({
          type: 'STOP_EGRESS',
          egressId: egress.egressId,
          reason: 'RECORDING_STOPPED',
        });
      } else if (!publishedSids.has(egress.trackSid)) {
        const since = observed.unpublishedSince[egress.trackSid];
        if (since !== undefined && observed.nowMs - since >= policy.stuckGraceMs) {
          actions.push({ type: 'STOP_EGRESS', egressId: egress.egressId, reason: 'STUCK' });
        }
      }
    }
  }

  // Récupération avant tout redémarrage du worker.
  if (toRecover.length > 0) actions.push({ type: 'RUN_RECOVERY', egressIds: toRecover });
  if (!observed.workerHealthy && toRecover.length === 0) actions.push({ type: 'RESTART_WORKER' });

  // Pistes publiées : chacune doit avoir un egress vivant tant que l'enregistrement est actif.
  const tracks: TrackState[] = observed.tracks.map((track) => {
    const own = segments.filter((s) => s.trackSid === track.sid);
    const covered = observed.egresses.some(
      (e) => e.trackSid === track.sid && LIVE.has(e.status) && !isZombie(e),
    );
    let states = own.map((s) => s.state);
    if (observed.recordingActive && !covered) {
      states = [...states, 'MISSING'];
      if (observed.workerHealthy) {
        actions.push({ type: 'START_EGRESS', trackSid: track.sid });
      } else {
        alert('TRACK_NOT_RECORDED', track.sid, 'Piste publiée sans egress et worker arrêté.');
      }
    }
    return { trackSid: track.sid, state: worst(states) };
  });

  return { segments, tracks, actions: actions.sort(byPriority) };
}
