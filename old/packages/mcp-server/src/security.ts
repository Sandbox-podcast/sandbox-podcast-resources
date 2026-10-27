import { createHash, randomUUID } from 'node:crypto';

export const SCOPES = [
  'episode:read',
  'episode:write',
  'asset:read',
  'presentation:read',
  'presentation:write',
] as const;
export type Scope = (typeof SCOPES)[number];

/**
 * Identifiant machine d'une intégration (agent IA). Il est lié à un seul podcast et à un humain
 * responsable (`actorId`) : les actions de l'agent sont imputées à cet humain dans l'audit.
 */
export interface Credential {
  id: string;
  actorId: string;
  podcastId: string;
  scopes: readonly Scope[];
  expiresAtMs: number | null;
  revoked: boolean;
}

/** En production : table des intégrations. Le serveur relit le credential à chaque appel : une révocation est immédiate. */
export interface CredentialStore {
  get(credentialId: string): Credential | null;
}

export class InMemoryCredentialStore implements CredentialStore {
  private readonly credentials = new Map<string, Credential>();

  issue(credential: Credential): void {
    this.credentials.set(credential.id, credential);
  }

  revoke(credentialId: string): void {
    const credential = this.credentials.get(credentialId);
    if (credential) this.credentials.set(credentialId, { ...credential, revoked: true });
  }

  setScopes(credentialId: string, scopes: readonly Scope[]): void {
    const credential = this.credentials.get(credentialId);
    if (credential) this.credentials.set(credentialId, { ...credential, scopes });
  }

  get(credentialId: string): Credential | null {
    return this.credentials.get(credentialId) ?? null;
  }
}

export type AuditResult =
  | 'OK'
  | 'UNCHANGED'
  | 'DENIED'
  | 'INVALID'
  | 'NOT_FOUND'
  | 'CONFLICT'
  | 'RATE_LIMITED'
  | 'CONFIRMATION_REQUIRED'
  | 'ERROR';

/** AC-MCP-005 : une entrée par tentative de mutation, y compris celles qui sont refusées. */
export interface AuditEntry {
  actor: string;
  /** `null` : action humaine (par exemple l'approbation d'une confirmation). */
  credentialId: string | null;
  podcastId: string | null;
  tool: string;
  scope: Scope | null;
  target: string;
  result: AuditResult;
  detail: string;
  timestamp: number;
  correlationId: string;
}

export interface AuditSink {
  record(entry: AuditEntry): void;
}

export class InMemoryAuditSink implements AuditSink {
  readonly entries: AuditEntry[] = [];

  record(entry: AuditEntry): void {
    this.entries.push(entry);
  }
}

/**
 * Limiteur à seau de jetons, par credential. Une lecture coûte 1 jeton, une mutation davantage :
 * un agent emballé ne peut pas saturer la plateforme ni enchaîner des écritures.
 */
export class RateLimiter {
  private readonly buckets = new Map<string, { tokens: number; updatedAtMs: number }>();

  private readonly capacity: number;
  private readonly refillPerSecond: number;

  constructor(capacity: number, refillPerSecond: number) {
    this.capacity = capacity;
    this.refillPerSecond = refillPerSecond;
  }

  /** `null` si autorisé, sinon le délai conseillé avant de réessayer. */
  take(key: string, cost: number, nowMs: number): number | null {
    const bucket = this.buckets.get(key) ?? { tokens: this.capacity, updatedAtMs: nowMs };
    const refilled = Math.min(
      this.capacity,
      bucket.tokens + ((nowMs - bucket.updatedAtMs) / 1000) * this.refillPerSecond,
    );
    if (refilled < cost) {
      this.buckets.set(key, { tokens: refilled, updatedAtMs: nowMs });
      return Math.ceil(((cost - refilled) / this.refillPerSecond) * 1000);
    }
    this.buckets.set(key, { tokens: refilled - cost, updatedAtMs: nowMs });
    return null;
  }
}

export const sha256 = (text: string): string => createHash('sha256').update(text).digest('hex');
export const newCorrelationId = (): string => randomUUID();

export type ConfirmationStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'CONSUMED';

export interface Confirmation {
  id: string;
  credentialId: string;
  podcastId: string;
  episodeId: string;
  tool: string;
  /** Empreinte des arguments demandés : l'approbation ne vaut que pour cette demande exacte. */
  argsHash: string;
  /** Empreinte du contenu soumis à l'approbation : s'il change ensuite, l'approbation tombe. */
  contentHash: string;
  createdAtMs: number;
  expiresAtMs: number;
  status: ConfirmationStatus;
  decidedBy: string | null;
  /** Résultat de l'action approuvée (par exemple l'identifiant de version publiée), pour rejouer sans republier. */
  result: string | null;
}

export type ConsumeResult =
  | { ok: true }
  | {
      ok: false;
      reason: 'UNKNOWN' | 'PENDING' | 'REJECTED' | 'EXPIRED' | 'MISMATCH' | 'USED' | 'STALE';
    };

/**
 * Confirmations humaines des actions publiantes. Une IA ne peut pas approuver : l'approbation
 * n'est exposée par aucun tool MCP, elle passe par l'application (`approve`).
 * Une confirmation est à usage unique, expire, et est liée à la demande exacte et au contenu exact.
 */
export class ConfirmationService {
  private readonly items = new Map<string, Confirmation>();

  private readonly ttlMs: number;

  constructor(ttlMs: number) {
    this.ttlMs = ttlMs;
  }

  request(
    input: Pick<
      Confirmation,
      'credentialId' | 'podcastId' | 'episodeId' | 'tool' | 'argsHash' | 'contentHash'
    >,
    nowMs: number,
    id: string = randomUUID(),
  ): Confirmation {
    const confirmation: Confirmation = {
      ...input,
      id,
      createdAtMs: nowMs,
      expiresAtMs: nowMs + this.ttlMs,
      status: 'PENDING',
      decidedBy: null,
      result: null,
    };
    this.items.set(id, confirmation);
    return confirmation;
  }

  get(id: string): Confirmation | null {
    return this.items.get(id) ?? null;
  }

  decide(id: string, approverId: string, approve: boolean, nowMs: number): Confirmation | null {
    const item = this.items.get(id);
    if (item?.status !== 'PENDING' || nowMs >= item.expiresAtMs) return null;
    const decided: Confirmation = {
      ...item,
      status: approve ? 'APPROVED' : 'REJECTED',
      decidedBy: approverId,
    };
    this.items.set(id, decided);
    return decided;
  }

  /** Consomme une approbation. Une seule fois, par le credential qui l'a demandée, pour la même demande et le même contenu. */
  consume(
    id: string,
    expected: Pick<Confirmation, 'credentialId' | 'tool' | 'argsHash' | 'contentHash'>,
    nowMs: number,
  ): ConsumeResult {
    const item = this.items.get(id);
    if (item?.credentialId !== expected.credentialId) return { ok: false, reason: 'UNKNOWN' };
    if (item.status === 'CONSUMED') return { ok: false, reason: 'USED' };
    if (item.status === 'REJECTED') return { ok: false, reason: 'REJECTED' };
    if (nowMs >= item.expiresAtMs) return { ok: false, reason: 'EXPIRED' };
    if (item.status === 'PENDING') return { ok: false, reason: 'PENDING' };
    if (item.tool !== expected.tool || item.argsHash !== expected.argsHash)
      return { ok: false, reason: 'MISMATCH' };
    if (item.contentHash !== expected.contentHash) return { ok: false, reason: 'STALE' };
    this.items.set(id, { ...item, status: 'CONSUMED' });
    return { ok: true };
  }

  /** Enregistre le résultat d'une action approuvée et menée à terme. */
  complete(id: string, result: string): void {
    const item = this.items.get(id);
    if (item?.status === 'CONSUMED') this.items.set(id, { ...item, result });
  }

  /** L'action a échoué après la consommation : l'approbation redevient utilisable. */
  release(id: string): void {
    const item = this.items.get(id);
    if (item?.status === 'CONSUMED' && item.result === null)
      this.items.set(id, { ...item, status: 'APPROVED' });
  }

  /** Résultat déjà obtenu pour la même demande exacte (rejeu après une réponse perdue), sinon `null`. */
  replay(
    id: string,
    expected: Pick<Confirmation, 'credentialId' | 'tool' | 'argsHash'>,
  ): string | null {
    const item = this.items.get(id);
    if (
      item?.status !== 'CONSUMED' ||
      item.credentialId !== expected.credentialId ||
      item.tool !== expected.tool ||
      item.argsHash !== expected.argsHash
    )
      return null;
    return item.result;
  }
}
