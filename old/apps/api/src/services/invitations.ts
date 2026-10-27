import { writeAudit } from '../audit.ts';
import { withTransaction, type Pool, type Queryable } from '../db/db.ts';
import { cleanDisplayName } from '../livekit.ts';
import { hashToken, newToken } from '../auth/tokens.ts';

export interface InvitationInfo {
  podcastName: string;
  episodeTitle: string;
  role: 'GUEST' | 'HOST';
  displayName: string | null;
  expiresAt: Date;
}

export async function createInvitation(
  pool: Pool,
  actor: { userId: string; correlationId: string },
  podcastId: string,
  episodeId: string,
  input: { role: 'GUEST' | 'HOST'; displayName?: string; ttlHours: number },
  now: Date,
): Promise<{ token: string; expiresAt: Date } | null> {
  return withTransaction(pool, async (client) => {
    const episode = await client.query('select 1 from episodes where id = $1 and podcast_id = $2', [
      episodeId,
      podcastId,
    ]);
    if (episode.rowCount === 0) return null;
    const token = newToken();
    const expiresAt = new Date(now.getTime() + input.ttlHours * 3_600_000);
    await client.query(
      `insert into invitations (podcast_id, episode_id, role, token_hash, display_name, created_by, expires_at)
       values ($1, $2, $3, $4, $5, $6, $7)`,
      [
        podcastId,
        episodeId,
        input.role,
        hashToken(token),
        input.displayName ? cleanDisplayName(input.displayName) || null : null,
        actor.userId,
        expiresAt,
      ],
    );
    await writeAudit(client, {
      actorUserId: actor.userId,
      actorKind: 'USER',
      podcastId,
      action: 'invitation.create',
      target: `episode:${episodeId}`,
      result: 'OK',
      correlationId: actor.correlationId,
      detail: { role: input.role },
    });
    return { token, expiresAt };
  });
}

interface InvitationRow {
  id: string;
  podcast_id: string;
  episode_id: string;
  role: 'GUEST' | 'HOST';
  display_name: string | null;
  expires_at: Date;
  revoked_at: Date | null;
}

const lookup = async (db: Queryable, token: string): Promise<InvitationRow | undefined> => {
  const { rows } = await db.query<InvitationRow>(
    'select id, podcast_id, episode_id, role, display_name, expires_at, revoked_at from invitations where token_hash = $1',
    [hashToken(token)],
  );
  return rows[0];
};

const usable = (row: InvitationRow | undefined, now: Date): row is InvitationRow =>
  row?.revoked_at === null && row.expires_at > now;

/** Informations publiques d'une invitation (page d'accueil de l'invité). `null` si elle est inconnue, expirée ou révoquée. */
export async function describeInvitation(
  db: Queryable,
  token: string,
  now: Date,
): Promise<InvitationInfo | null> {
  const row = await lookup(db, token);
  if (!usable(row, now)) return null;
  const { rows } = await db.query<{ podcast_name: string; title: string }>(
    'select p.name as podcast_name, e.title from episodes e join podcasts p on p.id = e.podcast_id where e.id = $1',
    [row.episode_id],
  );
  const info = rows[0];
  if (!info) return null;
  return {
    podcastName: info.podcast_name,
    episodeTitle: info.title,
    role: row.role,
    displayName: row.display_name,
    expiresAt: row.expires_at,
  };
}

export interface JoinedParticipant {
  participantId: string;
  episodeId: string;
  podcastId: string;
  displayName: string;
  role: 'GUEST' | 'HOST';
}

/**
 * Entrée d'un invité. Idempotente : le même jeton redonne le même participant (reconnexion après une panne),
 * donc la même identité LiveKit et les mêmes fichiers d'enregistrement. Le nom est celui de l'invitation, sinon celui
 * fourni à la première entrée, nettoyé.
 */
export async function joinWithInvitation(
  pool: Pool,
  token: string,
  displayName: string | undefined,
  correlationId: string,
  now: Date,
): Promise<JoinedParticipant | null> {
  return withTransaction(pool, async (client) => {
    const { rows } = await client.query<InvitationRow>(
      `select id, podcast_id, episode_id, role, display_name, expires_at, revoked_at
       from invitations where token_hash = $1 for update`,
      [hashToken(token)],
    );
    const invitation = rows[0];
    if (!usable(invitation, now)) return null;

    const existing = await client.query<{ id: string; display_name: string }>(
      'select id, display_name from participants where invitation_id = $1',
      [invitation.id],
    );
    const found = existing.rows[0];
    if (found) {
      return {
        participantId: found.id,
        episodeId: invitation.episode_id,
        podcastId: invitation.podcast_id,
        displayName: found.display_name,
        role: invitation.role,
      };
    }
    const name = cleanDisplayName(invitation.display_name ?? displayName ?? '');
    if (name.length === 0) return null;
    const created = await client.query<{ id: string }>(
      `insert into participants (episode_id, invitation_id, display_name, role) values ($1, $2, $3, $4) returning id`,
      [invitation.episode_id, invitation.id, name, invitation.role],
    );
    const participantId = created.rows[0]?.id;
    if (!participantId) throw new Error('participant sans identifiant');
    await client.query('update invitations set used_at = $2 where id = $1 and used_at is null', [
      invitation.id,
      now,
    ]);
    await writeAudit(client, {
      actorUserId: null,
      actorKind: 'GUEST',
      podcastId: invitation.podcast_id,
      action: 'invitation.join',
      target: `participant:${participantId}`,
      result: 'OK',
      correlationId,
      detail: { role: invitation.role },
    });
    return {
      participantId,
      episodeId: invitation.episode_id,
      podcastId: invitation.podcast_id,
      displayName: name,
      role: invitation.role,
    };
  });
}

export async function revokeInvitations(
  pool: Pool,
  podcastId: string,
  episodeId: string,
  now: Date,
): Promise<number> {
  const result = await pool.query(
    'update invitations set revoked_at = $3 where podcast_id = $1 and episode_id = $2 and revoked_at is null',
    [podcastId, episodeId, now],
  );
  return result.rowCount ?? 0;
}
