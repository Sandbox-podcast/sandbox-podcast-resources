import { standardTemplate } from '@podcast/episode-factory';
import { writeAudit } from '../audit.ts';
import { withTransaction, type Pool, type Queryable } from '../db/db.ts';
import type { Role } from '../rbac.ts';
import { isRole } from '../rbac.ts';

export interface Podcast {
  id: string;
  name: string;
  role: Role;
}

/** Les assets et thèmes que référence le template standard : leur première version est créée avec le podcast. */
const STANDARD_ASSETS = [
  'logo-principal',
  'intro-video',
  'outro-video',
  'jingle-intro',
  'bandeau-nom',
];
const STANDARD_THEMES = ['marque', 'diffusion'];

/**
 * Crée un podcast, fait de son créateur l'ADMIN, et amorce son catalogue (template standard v1, assets et
 * thèmes v1). Tout dans une transaction, avec l'entrée d'audit.
 */
export async function createPodcast(
  pool: Pool,
  actor: { userId: string; correlationId: string },
  name: string,
): Promise<Podcast> {
  return withTransaction(pool, async (client) => {
    const { rows } = await client.query<{ id: string }>(
      'insert into podcasts (name, created_by) values ($1, $2) returning id',
      [name.trim(), actor.userId],
    );
    const id = rows[0]?.id;
    if (!id) throw new Error('création du podcast sans identifiant');
    await client.query(
      "insert into memberships (podcast_id, user_id, role) values ($1, $2, 'ADMIN')",
      [id, actor.userId],
    );
    await client.query(
      'insert into templates (podcast_id, id, version, body) values ($1, $2, 1, $3)',
      [id, 'standard', JSON.stringify(standardTemplate(1))],
    );
    for (const asset of STANDARD_ASSETS)
      await client.query('insert into assets (podcast_id, id, version) values ($1, $2, 1)', [
        id,
        asset,
      ]);
    for (const theme of STANDARD_THEMES)
      await client.query('insert into themes (podcast_id, id, version) values ($1, $2, 1)', [
        id,
        theme,
      ]);
    await writeAudit(client, {
      actorUserId: actor.userId,
      actorKind: 'USER',
      podcastId: id,
      action: 'podcast.create',
      target: `podcast:${id}`,
      result: 'OK',
      correlationId: actor.correlationId,
    });
    return { id, name: name.trim(), role: 'ADMIN' };
  });
}

export async function listPodcasts(db: Queryable, userId: string): Promise<Podcast[]> {
  const { rows } = await db.query<{ id: string; name: string; role: string }>(
    `select p.id, p.name, m.role from podcasts p join memberships m on m.podcast_id = p.id
     where m.user_id = $1 order by p.created_at`,
    [userId],
  );
  return rows.flatMap((r) => (isRole(r.role) ? [{ id: r.id, name: r.name, role: r.role }] : []));
}

/** Rôle d'un utilisateur dans un podcast, `null` s'il n'en est pas membre (ou si le podcast n'existe pas). */
export async function membershipRole(
  db: Queryable,
  podcastId: string,
  userId: string,
): Promise<Role | null> {
  const { rows } = await db.query<{ role: string }>(
    'select role from memberships where podcast_id = $1 and user_id = $2',
    [podcastId, userId],
  );
  const role = rows[0]?.role;
  return isRole(role) ? role : null;
}

export type AddMemberResult = { ok: true } | { ok: false; reason: 'USER_NOT_FOUND' };

export async function addMember(
  pool: Pool,
  actor: { userId: string; correlationId: string },
  podcastId: string,
  email: string,
  role: Role,
): Promise<AddMemberResult> {
  return withTransaction(pool, async (client) => {
    const { rows } = await client.query<{ id: string }>(
      'select id from users where email = $1 and not disabled',
      [email.trim().toLowerCase()],
    );
    const userId = rows[0]?.id;
    if (!userId) return { ok: false, reason: 'USER_NOT_FOUND' } as const;
    await client.query(
      `insert into memberships (podcast_id, user_id, role) values ($1, $2, $3)
       on conflict (podcast_id, user_id) do update set role = excluded.role`,
      [podcastId, userId, role],
    );
    await writeAudit(client, {
      actorUserId: actor.userId,
      actorKind: 'USER',
      podcastId,
      action: 'member.set-role',
      target: `user:${userId}`,
      result: 'OK',
      correlationId: actor.correlationId,
      detail: { role },
    });
    return { ok: true } as const;
  });
}
