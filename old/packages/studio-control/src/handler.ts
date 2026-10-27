import { isAllowed } from './permissions.ts';
import {
  DEFAULT_POLICY,
  type AssetStatus,
  type Command,
  type CommandError,
  type CommandResult,
  type ErrorCode,
  type EventType,
  type NewEvent,
  type Source,
  type StudioPolicy,
  type StudioState,
} from './types.ts';

const RETRYABLE: ReadonlySet<ErrorCode> = new Set([
  'STALE_VERSION',
  'PREVIEW_CHANGED',
  'PREVIEW_NOT_READY',
  'SOURCE_NOT_READY',
]);

const reject = (command: Command, code: ErrorCode, message: string): CommandResult => {
  const error: CommandError = { code, message, retryable: RETRYABLE.has(code) };
  return {
    ok: false,
    error,
    events: [event(command, 'CommandRejected', { type: command.type, code, message })],
  };
};

function event(
  command: Command,
  type: EventType,
  details: Record<string, string | number | boolean | null> = {},
): NewEvent {
  return {
    type,
    atMs: command.atMs,
    actorId: command.actor.id,
    commandId: command.commandId,
    correlationId: command.correlationId ?? null,
    details,
  };
}

/** Statut de chargement d'une source : prête si elle n'a pas de média, sinon selon le rapport du chargeur. */
export function sourceStatus(state: StudioState, source: Source): AssetStatus {
  if (source.assetId === undefined) return 'READY';
  return state.assets[source.assetId] ?? 'LOADING';
}

const valid = (source: Source): boolean => source.id.length > 0 && source.assetId !== '';

/**
 * Applique une commande à l'état d'un studio. Fonction pure : retourne le nouvel état et les
 * événements d'audit, ou une erreur structurée sans modifier l'état.
 *
 * Chaîne : permission, version attendue, validation, règles métier, exécution.
 * L'idempotence par `commandId` et la sérialisation des écritures sont assurées par le service.
 */
export function handleCommand(
  state: StudioState,
  command: Command,
  policy: StudioPolicy = DEFAULT_POLICY,
): CommandResult {
  if (!isAllowed(command, policy)) {
    return reject(command, 'FORBIDDEN', `${command.actor.id} ne peut pas exécuter ${command.type}`);
  }
  if (command.expectedVersion !== undefined && command.expectedVersion !== state.version) {
    return reject(
      command,
      'STALE_VERSION',
      `version attendue ${String(command.expectedVersion)}, version actuelle ${String(state.version)}`,
    );
  }

  const next = (changes: Partial<StudioState>, events: NewEvent[]): CommandResult => ({
    ok: true,
    state: { ...state, ...changes, version: state.version + 1 },
    events,
  });

  switch (command.type) {
    case 'SET_PREVIEW': {
      if (!valid(command.source)) return reject(command, 'VALIDATION', 'source invalide');
      // Choisir la Preview ne touche jamais au Program.
      return next({ preview: command.source }, [
        event(command, 'PreviewChanged', {
          sourceId: command.source.id,
          kind: command.source.kind,
          status: sourceStatus(state, command.source),
        }),
      ]);
    }

    case 'TAKE': {
      if (state.preview === null)
        return reject(command, 'NOTHING_IN_PREVIEW', 'la Preview est vide');
      if (state.preview.id !== command.expectPreviewId) {
        return reject(
          command,
          'PREVIEW_CHANGED',
          `la Preview n'est plus ${command.expectPreviewId} (elle est ${state.preview.id})`,
        );
      }
      if (sourceStatus(state, state.preview) !== 'READY') {
        return reject(
          command,
          'PREVIEW_NOT_READY',
          `la Preview n'est pas prête (${sourceStatus(state, state.preview)})`,
        );
      }
      // Comme un mélangeur vidéo : la Preview passe en Program, l'ancien Program devient la Preview.
      return next({ program: state.preview, preview: state.program }, [
        event(command, 'ProgramSceneChanged', {
          from: state.program?.id ?? null,
          to: state.preview.id,
          via: 'TAKE',
          transition: command.transition ?? 'CUT',
        }),
      ]);
    }

    case 'CUT': {
      if (!valid(command.source)) return reject(command, 'VALIDATION', 'source invalide');
      const automatic = command.actor.kind === 'AUTO_DIRECTOR';
      if (automatic && !state.autoDirector) {
        return reject(command, 'AUTO_DIRECTOR_OFF', "le réalisateur automatique n'est pas actif");
      }
      if (sourceStatus(state, command.source) !== 'READY') {
        return reject(
          command,
          'SOURCE_NOT_READY',
          `la source n'est pas prête (${sourceStatus(state, command.source)})`,
        );
      }
      const events = [
        event(command, 'ProgramSceneChanged', {
          from: state.program?.id ?? null,
          to: command.source.id,
          via: automatic ? 'AUTO_DIRECTOR' : 'CUT',
        }),
      ];
      // Une coupure manuelle reprend la main : la réalisation automatique s'arrête.
      const disableAuto = !automatic && state.autoDirector;
      if (disableAuto)
        events.push(event(command, 'AutoDirectorToggled', { on: false, reason: 'prise manuelle' }));
      return next(
        { program: command.source, autoDirector: disableAuto ? false : state.autoDirector },
        events,
      );
    }

    case 'REPORT_ASSET': {
      const events = [
        event(command, 'AssetStatusReported', { assetId: command.assetId, status: command.status }),
      ];
      // Une erreur sur le média du Program est signalée mais ne change pas le Program.
      if (command.status === 'ERROR' && state.program?.assetId === command.assetId) {
        events.push(
          event(command, 'ProgramAssetError', {
            assetId: command.assetId,
            sourceId: state.program.id,
          }),
        );
      }
      return next({ assets: { ...state.assets, [command.assetId]: command.status } }, events);
    }

    case 'SHOW_OVERLAY':
    case 'HIDE_OVERLAY': {
      const show = command.type === 'SHOW_OVERLAY';
      const present = state.overlays.includes(command.overlayId);
      const overlays = show
        ? present
          ? state.overlays
          : [...state.overlays, command.overlayId]
        : state.overlays.filter((id) => id !== command.overlayId);
      return next({ overlays }, [
        event(command, 'OverlayChanged', { overlayId: command.overlayId, visible: show }),
      ]);
    }

    case 'START_RECORDING': {
      if (state.recording.status === 'RECORDING') {
        return reject(command, 'ALREADY_RECORDING', `déjà en cours (${state.recording.sessionId})`);
      }
      const missing = policy.requiredConsentFrom.filter((id) => state.consents[id] !== true);
      if (missing.length > 0) {
        return reject(command, 'CONSENT_REQUIRED', `consentement manquant : ${missing.join(', ')}`);
      }
      if (command.sessionId.length === 0) return reject(command, 'VALIDATION', 'sessionId vide');
      return next(
        {
          recording: {
            status: 'RECORDING',
            sessionId: command.sessionId,
            startedAtMs: command.atMs,
          },
        },
        [event(command, 'RecordingStarted', { sessionId: command.sessionId })],
      );
    }

    case 'STOP_RECORDING': {
      if (state.recording.status !== 'RECORDING')
        return reject(command, 'NOT_RECORDING', 'aucun enregistrement en cours');
      return next({ recording: { status: 'IDLE', lastSessionId: state.recording.sessionId } }, [
        event(command, 'RecordingStopped', {
          sessionId: state.recording.sessionId,
          durationMs: command.atMs - state.recording.startedAtMs,
        }),
      ]);
    }

    case 'SET_AUTO_DIRECTOR':
      return next({ autoDirector: command.on }, [
        event(command, 'AutoDirectorToggled', { on: command.on, reason: 'demande du Producer' }),
      ]);

    case 'SET_SEQUENCE': {
      if (command.sequenceId.length === 0) return reject(command, 'VALIDATION', 'séquence vide');
      // Changer de séquence ne touche ni à l'enregistrement ni au Program.
      return next({ currentSequenceId: command.sequenceId }, [
        event(command, 'SequenceChanged', {
          from: state.currentSequenceId,
          to: command.sequenceId,
        }),
      ]);
    }

    case 'GRANT_CONSENT':
      return next({ consents: { ...state.consents, [command.participantId]: true } }, [
        event(command, 'ConsentGranted', { participantId: command.participantId }),
      ]);
  }
}
