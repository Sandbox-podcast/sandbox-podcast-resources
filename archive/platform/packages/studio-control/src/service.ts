import { handleCommand } from './handler.ts';
import {
  DEFAULT_POLICY,
  initialState,
  type Command,
  type CommandResult,
  type StudioEvent,
  type StudioPolicy,
  type StudioState,
} from './types.ts';

export type CommitOutcome =
  | { kind: 'OK'; events: StudioEvent[] }
  | { kind: 'CONFLICT' }
  | { kind: 'DUPLICATE'; result: CommandResult; events: StudioEvent[] };

/**
 * Stockage d'un studio. L'écriture est atomique : état, événements d'audit et résultat de la
 * commande (pour l'idempotence) sont enregistrés ensemble, seulement si la version n'a pas changé.
 * En production : une transaction PostgreSQL avec contrainte d'unicité sur (studio, commandId).
 */
export interface StudioStore {
  load(studioId: string): Promise<StudioState>;
  getResult(
    studioId: string,
    commandId: string,
  ): Promise<{ result: CommandResult; events: StudioEvent[] } | undefined>;
  commit(
    studioId: string,
    expectedVersion: number,
    commandId: string,
    result: CommandResult,
  ): Promise<CommitOutcome>;
  events(studioId: string): Promise<StudioEvent[]>;
}

/** Implémentation en mémoire. `yieldBeforeCommit` entrelace les appels concurrents pour les tests. */
export class InMemoryStudioStore implements StudioStore {
  private readonly states = new Map<string, StudioState>();
  private readonly logs = new Map<string, StudioEvent[]>();
  private readonly results = new Map<string, { result: CommandResult; events: StudioEvent[] }>();
  private readonly yieldBeforeCommit: boolean;

  constructor(options: { yieldBeforeCommit?: boolean } = {}) {
    this.yieldBeforeCommit = options.yieldBeforeCommit ?? false;
  }

  load(studioId: string): Promise<StudioState> {
    return Promise.resolve(this.states.get(studioId) ?? initialState(studioId));
  }

  getResult(studioId: string, commandId: string) {
    return Promise.resolve(this.results.get(`${studioId}:${commandId}`));
  }

  async commit(
    studioId: string,
    expectedVersion: number,
    commandId: string,
    result: CommandResult,
  ): Promise<CommitOutcome> {
    if (this.yieldBeforeCommit) await new Promise((resolve) => setImmediate(resolve));
    const key = `${studioId}:${commandId}`;
    const known = this.results.get(key);
    if (known) return { kind: 'DUPLICATE', ...known };
    const current = this.states.get(studioId) ?? initialState(studioId);
    if (current.version !== expectedVersion) return { kind: 'CONFLICT' };

    const log = this.logs.get(studioId) ?? [];
    const events = result.events.map((e, i): StudioEvent => ({ ...e, seq: log.length + i + 1 }));
    this.logs.set(studioId, [...log, ...events]);
    if (result.ok) this.states.set(studioId, result.state);
    this.results.set(key, { result, events });
    return { kind: 'OK', events };
  }

  events(studioId: string): Promise<StudioEvent[]> {
    return Promise.resolve(this.logs.get(studioId) ?? []);
  }
}

export interface Executed {
  result: CommandResult;
  /** Événements d'audit enregistrés pour cette commande, avec leur numéro d'ordre. */
  events: StudioEvent[];
  /** Vrai si la commande avait déjà été exécutée : on renvoie le résultat d'origine. */
  replayed: boolean;
}

const MAX_ATTEMPTS = 50;

/**
 * Point d'entrée unique des commandes de régie : UI, API, WebSocket et MCP passent par ici.
 * Garantit : une commande n'a d'effet qu'une fois (clé d'idempotence), les écritures concurrentes
 * ne produisent jamais d'état incohérent (version optimiste), tout est audité.
 */
export class StudioService {
  private readonly store: StudioStore;
  private readonly policy: StudioPolicy;

  constructor(store: StudioStore, policy: StudioPolicy = DEFAULT_POLICY) {
    this.store = store;
    this.policy = policy;
  }

  private readonly tails = new Map<string, Promise<void>>();

  /**
   * Les commandes d'un même studio sont traitées l'une après l'autre dans ce processus.
   * La version optimiste protège en plus contre les écritures d'un autre processus.
   */
  async execute(studioId: string, command: Command): Promise<Executed> {
    const previous = this.tails.get(studioId) ?? Promise.resolve();
    let release: () => void = () => undefined;
    const mine = new Promise<void>((resolve) => {
      release = resolve;
    });
    const tail = previous.then(() => mine);
    this.tails.set(studioId, tail);
    await previous;
    try {
      return await this.executeSerialized(studioId, command);
    } finally {
      release();
      if (this.tails.get(studioId) === tail) this.tails.delete(studioId);
    }
  }

  private async executeSerialized(studioId: string, command: Command): Promise<Executed> {
    for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
      const prior = await this.store.getResult(studioId, command.commandId);
      if (prior) return { ...prior, replayed: true };

      const state = await this.store.load(studioId);
      const result = handleCommand(state, command, this.policy);
      const outcome = await this.store.commit(studioId, state.version, command.commandId, result);
      if (outcome.kind === 'OK') return { result, events: outcome.events, replayed: false };
      if (outcome.kind === 'DUPLICATE') {
        return { result: outcome.result, events: outcome.events, replayed: true };
      }
      // CONFLICT : quelqu'un a modifié l'état entre la lecture et l'écriture, on recommence.
    }
    throw new Error(`Trop de conflits d'écriture sur le studio ${studioId}`);
  }

  state(studioId: string): Promise<StudioState> {
    return this.store.load(studioId);
  }

  auditLog(studioId: string): Promise<StudioEvent[]> {
    return this.store.events(studioId);
  }
}
