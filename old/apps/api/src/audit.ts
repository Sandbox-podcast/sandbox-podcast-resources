import type { Queryable } from './db/db.ts';

export interface AuditEntry {
  actorUserId: string | null;
  actorKind: 'USER' | 'GUEST' | 'SYSTEM' | 'ANONYMOUS';
  podcastId: string | null;
  action: string;
  target: string;
  result: 'OK' | 'DENIED' | 'INVALID' | 'ERROR';
  correlationId: string;
  detail?: Record<string, unknown>;
}

/**
 * Inscrit une entrée dans le journal d'audit. Appelé avec le client de la transaction de l'action : l'entrée
 * et la modification réussissent ou échouent ensemble. Ne jamais y mettre de secret (mot de passe, jeton).
 */
export async function writeAudit(db: Queryable, entry: AuditEntry): Promise<void> {
  await db.query(
    `insert into audit_log (actor_user_id, actor_kind, podcast_id, action, target, result, correlation_id, detail)
     values ($1, $2, $3, $4, $5, $6, $7, $8)`,
    [
      entry.actorUserId,
      entry.actorKind,
      entry.podcastId,
      entry.action,
      entry.target,
      entry.result,
      entry.correlationId,
      JSON.stringify(entry.detail ?? {}),
    ],
  );
}
