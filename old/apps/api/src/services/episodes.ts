import {
  InMemoryCatalog,
  createEpisodeFromTemplate,
  type CreateIfAbsentResult,
  type EpisodeRepository,
  type EpisodeWorkspace,
  type FactoryResult,
} from '@podcast/episode-factory';
import { z } from 'zod';
import { writeAudit } from '../audit.ts';
import { withTransaction, type Pool, type PoolClient, type Queryable } from '../db/db.ts';

interface Row {
  workspace: EpisodeWorkspace;
  revision: number;
}

/**
 * Dépôt des épisodes dans PostgreSQL. Toutes les opérations sont limitées à un podcast. La création est
 * atomique : l'épisode, sa clé d'idempotence et l'entrée d'audit sont écrits dans la même transaction.
 */
export class PgEpisodeRepository implements EpisodeRepository {
  private readonly pool: Pool;
  private readonly onCreated:
    ((client: PoolClient, episode: EpisodeWorkspace) => Promise<void>) | undefined;

  constructor(
    pool: Pool,
    onCreated?: (client: PoolClient, episode: EpisodeWorkspace) => Promise<void>,
  ) {
    this.pool = pool;
    this.onCreated = onCreated;
  }

  async createIfAbsent(
    podcastId: string,
    idempotencyKey: string,
    requestFingerprint: string,
    episode: EpisodeWorkspace,
  ): Promise<CreateIfAbsentResult> {
    return withTransaction(this.pool, async (client): Promise<CreateIfAbsentResult> => {
      // Verrou consultatif sur (podcast, clé) : deux demandes simultanées avec la même clé se sérialisent.
      await client.query('select pg_advisory_xact_lock(hashtext($1))', [
        `${podcastId}:${idempotencyKey}`,
      ]);
      const known = await client.query<{ fingerprint: string; episode_id: string }>(
        'select fingerprint, episode_id from episode_idempotency where podcast_id = $1 and idempotency_key = $2',
        [podcastId, idempotencyKey],
      );
      const existing = known.rows[0];
      if (existing) {
        if (existing.fingerprint !== requestFingerprint) return { kind: 'KEY_CONFLICT' };
        const row = await client.query<Row>(
          'select workspace, revision from episodes where id = $1 and podcast_id = $2',
          [existing.episode_id, podcastId],
        );
        const found = row.rows[0];
        if (found)
          return { kind: 'EXISTING', episode: { ...found.workspace, revision: found.revision } };
      }
      await client.query(
        `insert into episodes (id, podcast_id, title, episode_date, workspace, revision)
         values ($1, $2, $3, $4, $5, $6)`,
        [
          episode.id,
          podcastId,
          episode.title,
          episode.date,
          JSON.stringify(episode),
          episode.revision,
        ],
      );
      await client.query(
        'insert into episode_idempotency (podcast_id, idempotency_key, fingerprint, episode_id) values ($1, $2, $3, $4)',
        [podcastId, idempotencyKey, requestFingerprint, episode.id],
      );
      await this.onCreated?.(client, episode);
      return { kind: 'CREATED', episode };
    });
  }

  async get(podcastId: string, episodeId: string): Promise<EpisodeWorkspace | null> {
    const { rows } = await this.pool.query<Row>(
      'select workspace, revision from episodes where id = $1 and podcast_id = $2',
      [episodeId, podcastId],
    );
    const row = rows[0];
    return row ? { ...row.workspace, revision: row.revision } : null;
  }

  async list(podcastId: string): Promise<EpisodeWorkspace[]> {
    const { rows } = await this.pool.query<Row>(
      'select workspace, revision from episodes where podcast_id = $1 order by created_at',
      [podcastId],
    );
    return rows.map((r) => ({ ...r.workspace, revision: r.revision }));
  }

  async replace(episode: EpisodeWorkspace, expectedRevision: number): Promise<boolean> {
    const next = expectedRevision + 1;
    const result = await this.pool.query(
      `update episodes set workspace = $1, revision = $2, title = $3
       where id = $4 and podcast_id = $5 and revision = $6`,
      [
        JSON.stringify({ ...episode, revision: next }),
        next,
        episode.title,
        episode.id,
        episode.podcastId,
        expectedRevision,
      ],
    );
    return result.rowCount === 1;
  }
}

/** Charge les catalogues d'un podcast (petits : quelques lignes) dans un catalogue en mémoire pour la fabrique. */
export async function loadCatalog(db: Queryable, podcastId: string): Promise<InMemoryCatalog> {
  const catalog = new InMemoryCatalog();
  const templates = await db.query<{ id: string; version: number; body: unknown }>(
    'select id, version, body from templates where podcast_id = $1',
    [podcastId],
  );
  for (const t of templates.rows) catalog.publishTemplate(t.id, t.version, t.body);
  const assets = await db.query<{ id: string; version: number }>(
    'select id, version from assets where podcast_id = $1',
    [podcastId],
  );
  for (const a of assets.rows) catalog.publishAsset(a.id, a.version);
  const themes = await db.query<{ id: string; version: number }>(
    'select id, version from themes where podcast_id = $1',
    [podcastId],
  );
  for (const t of themes.rows) catalog.publishTheme(t.id, t.version);
  return catalog;
}

export async function createEpisode(
  pool: Pool,
  actor: { userId: string; correlationId: string },
  podcastId: string,
  input: {
    templateId: string;
    templateVersion?: number;
    title: string;
    date: string;
    idempotencyKey: string;
  },
): Promise<FactoryResult> {
  const catalog = await loadCatalog(pool, podcastId);
  const repository = new PgEpisodeRepository(pool, async (client, episode) => {
    await writeAudit(client, {
      actorUserId: actor.userId,
      actorKind: 'USER',
      podcastId,
      action: 'episode.create',
      target: `episode:${episode.id}`,
      result: 'OK',
      correlationId: actor.correlationId,
      detail: {
        templateId: episode.origin.templateId,
        templateVersion: episode.origin.templateVersion,
      },
    });
  });
  return createEpisodeFromTemplate(
    { ...input, podcastId, actorId: actor.userId },
    { templates: catalog, assets: catalog, themes: catalog, repository },
  );
}

export const segmentPatchSchema = z
  .strictObject({
    title: z.string().trim().min(1).max(120).optional(),
    objective: z.string().max(500).optional(),
    notes: z.string().max(20_000).optional(),
    questions: z.array(z.string().max(300)).max(50).optional(),
    targetDurationSec: z.number().int().min(10).max(14_400).optional(),
    status: z.enum(['TODO', 'IN_PROGRESS', 'READY']).optional(),
  })
  .refine((patch) => Object.keys(patch).length > 0, 'au moins un champ à modifier');

export type SegmentPatch = z.infer<typeof segmentPatchSchema>;

export type UpdateSegmentResult =
  | { ok: true; episode: EpisodeWorkspace }
  | { ok: false; reason: 'NOT_FOUND' | 'SEGMENT_NOT_FOUND' }
  | { ok: false; reason: 'CONFLICT'; currentRevision: number };

/** Modifie une séquence avec contrôle de révision : un conflit est signalé, jamais écrasé en silence. */
export async function updateSegment(
  pool: Pool,
  actor: { userId: string; correlationId: string },
  podcastId: string,
  episodeId: string,
  segmentId: string,
  expectedRevision: number,
  patch: SegmentPatch,
): Promise<UpdateSegmentResult> {
  return withTransaction(pool, async (client): Promise<UpdateSegmentResult> => {
    const { rows } = await client.query<Row>(
      'select workspace, revision from episodes where id = $1 and podcast_id = $2 for update',
      [episodeId, podcastId],
    );
    const row = rows[0];
    if (!row) return { ok: false, reason: 'NOT_FOUND' };
    const episode: EpisodeWorkspace = { ...row.workspace, revision: row.revision };
    if (row.revision !== expectedRevision)
      return { ok: false, reason: 'CONFLICT', currentRevision: row.revision };
    const index = episode.segments.findIndex((s) => s.id === segmentId);
    const current = episode.segments[index];
    if (!current) return { ok: false, reason: 'SEGMENT_NOT_FOUND' };
    const defined = Object.fromEntries(Object.entries(patch).filter(([, v]) => v !== undefined));
    const updated = {
      ...episode,
      segments: episode.segments.map((s, i) => (i === index ? { ...s, ...defined } : s)),
    };
    const next = row.revision + 1;
    await client.query(
      'update episodes set workspace = $1, revision = $2 where id = $3 and podcast_id = $4',
      [JSON.stringify({ ...updated, revision: next }), next, episodeId, podcastId],
    );
    await writeAudit(client, {
      actorUserId: actor.userId,
      actorKind: 'USER',
      podcastId,
      action: 'segment.update',
      target: `episode:${episodeId}/segment:${segmentId}`,
      result: 'OK',
      correlationId: actor.correlationId,
      detail: { fields: Object.keys(defined) },
    });
    return { ok: true, episode: { ...updated, revision: next } };
  });
}
