export type Role = 'ADMIN' | 'PRODUCER' | 'HOST' | 'EDITOR' | 'GUEST';

/** D'où vient la commande. Les permissions sont les mêmes quel que soit le canal (UI, API, WebSocket, MCP). */
export type ActorKind = 'USER' | 'AUTO_DIRECTOR' | 'MCP' | 'SYSTEM';

export interface Actor {
  id: string;
  kind: ActorKind;
  roles: readonly Role[];
}

export type SourceKind =
  'scene' | 'image' | 'video' | 'presentation' | 'document' | 'webpage' | 'screenshare' | 'graphic';

export interface Source {
  kind: SourceKind;
  id: string;
  /** Média à charger avant de pouvoir passer à l'antenne. Sans `assetId`, la source est prête. */
  assetId?: string;
}

export type AssetStatus = 'LOADING' | 'READY' | 'ERROR';

export type RecordingState =
  | { status: 'IDLE'; lastSessionId: string | null }
  | { status: 'RECORDING'; sessionId: string; startedAtMs: number };

/** État d'un studio, source de vérité côté serveur. `version` augmente à chaque commande acceptée. */
export interface StudioState {
  studioId: string;
  version: number;
  program: Source | null;
  preview: Source | null;
  assets: Readonly<Record<string, AssetStatus>>;
  overlays: readonly string[];
  recording: RecordingState;
  autoDirector: boolean;
  currentSequenceId: string | null;
  consents: Readonly<Record<string, boolean>>;
}

interface BaseCommand {
  /** Clé d'idempotence : rejouer la même commande ne l'exécute pas deux fois. */
  commandId: string;
  actor: Actor;
  atMs: number;
  /** Si fourni, la commande n'est acceptée que si l'état n'a pas changé depuis cette version. */
  expectedVersion?: number;
  correlationId?: string;
}

export type Command = BaseCommand &
  (
    | { type: 'SET_PREVIEW'; source: Source }
    | { type: 'TAKE'; expectPreviewId: string; transition?: 'CUT' | 'MIX' }
    | { type: 'CUT'; source: Source }
    | { type: 'REPORT_ASSET'; assetId: string; status: AssetStatus }
    | { type: 'SHOW_OVERLAY'; overlayId: string }
    | { type: 'HIDE_OVERLAY'; overlayId: string }
    | { type: 'START_RECORDING'; sessionId: string }
    | { type: 'STOP_RECORDING' }
    | { type: 'SET_AUTO_DIRECTOR'; on: boolean }
    | { type: 'SET_SEQUENCE'; sequenceId: string }
    | { type: 'GRANT_CONSENT'; participantId: string }
  );

type DistributiveOmit<T, K extends PropertyKey> = T extends unknown ? Omit<T, K> : never;

/** Le contenu propre d'une commande, sans les champs communs (clé, auteur, heure, version attendue). */
export type CommandBody = DistributiveOmit<
  Command,
  'commandId' | 'actor' | 'atMs' | 'expectedVersion' | 'correlationId'
>;

export type CommandType = Command['type'];

export type ErrorCode =
  | 'FORBIDDEN'
  | 'STALE_VERSION'
  | 'VALIDATION'
  | 'NOTHING_IN_PREVIEW'
  | 'PREVIEW_CHANGED'
  | 'PREVIEW_NOT_READY'
  | 'SOURCE_NOT_READY'
  | 'AUTO_DIRECTOR_OFF'
  | 'ALREADY_RECORDING'
  | 'NOT_RECORDING'
  | 'CONSENT_REQUIRED';

export interface CommandError {
  code: ErrorCode;
  message: string;
  /** Réessayer a un sens (état périmé, chargement en cours) ou non (interdit, invalide). */
  retryable: boolean;
}

export type EventType =
  | 'PreviewChanged'
  | 'ProgramSceneChanged'
  | 'ProgramAssetError'
  | 'AssetStatusReported'
  | 'OverlayChanged'
  | 'RecordingStarted'
  | 'RecordingStopped'
  | 'AutoDirectorToggled'
  | 'SequenceChanged'
  | 'ConsentGranted'
  | 'CommandRejected';

/** Événement du journal d'audit. */
export interface StudioEvent {
  /** Numéro d'ordre dans le journal du studio, attribué à l'enregistrement. */
  seq: number;
  type: EventType;
  atMs: number;
  actorId: string;
  commandId: string;
  correlationId: string | null;
  details: Readonly<Record<string, string | number | boolean | null>>;
}

export type NewEvent = Omit<StudioEvent, 'seq'>;

export type CommandResult =
  | { ok: true; state: StudioState; events: NewEvent[] }
  | { ok: false; error: CommandError; events: NewEvent[] };

export interface StudioPolicy {
  /** Un Host peut-il piloter la régie ? Désactivé par défaut. */
  hostsMayControl: boolean;
  /** Participants dont le consentement est requis avant de démarrer l'enregistrement. */
  requiredConsentFrom: readonly string[];
}

export const DEFAULT_POLICY: StudioPolicy = { hostsMayControl: false, requiredConsentFrom: [] };

export function initialState(studioId: string): StudioState {
  return {
    studioId,
    version: 0,
    program: null,
    preview: null,
    assets: {},
    overlays: [],
    recording: { status: 'IDLE', lastSessionId: null },
    autoDirector: false,
    currentSequenceId: null,
    consents: {},
  };
}
