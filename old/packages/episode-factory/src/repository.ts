import type { EpisodeWorkspace } from './model.ts';

export type CreateIfAbsentResult =
  | { kind: 'CREATED'; episode: EpisodeWorkspace }
  | { kind: 'EXISTING'; episode: EpisodeWorkspace }
  | { kind: 'KEY_CONFLICT' };

/**
 * Stockage des épisodes. Toutes les opérations sont limitées à un podcast : un identifiant d'un
 * autre podcast n'existe pas, même s'il est valide (isolation entre locataires).
 * En production : PostgreSQL, contrainte d'unicité sur (podcast, clé d'idempotence), écriture en une transaction.
 */
export interface EpisodeRepository {
  /**
   * Crée l'épisode seulement si la clé d'idempotence n'existe pas pour ce podcast.
   * Même clé et même empreinte de demande : retourne l'épisode déjà créé. Même clé et empreinte
   * différente : conflit.
   */
  createIfAbsent(
    podcastId: string,
    idempotencyKey: string,
    requestFingerprint: string,
    episode: EpisodeWorkspace,
  ): Promise<CreateIfAbsentResult>;
  get(podcastId: string, episodeId: string): Promise<EpisodeWorkspace | null>;
  list(podcastId: string): Promise<EpisodeWorkspace[]>;
  /** Remplace l'épisode si la révision attendue est la révision actuelle. */
  replace(episode: EpisodeWorkspace, expectedRevision: number): Promise<boolean>;
}

export class InMemoryEpisodeRepository implements EpisodeRepository {
  private readonly episodes = new Map<string, EpisodeWorkspace>();
  private readonly keys = new Map<string, { fingerprint: string; episodeId: string }>();

  createIfAbsent(
    podcastId: string,
    idempotencyKey: string,
    requestFingerprint: string,
    episode: EpisodeWorkspace,
  ): Promise<CreateIfAbsentResult> {
    const keyId = `${podcastId}:${idempotencyKey}`;
    const known = this.keys.get(keyId);
    if (known) {
      if (known.fingerprint !== requestFingerprint)
        return Promise.resolve({ kind: 'KEY_CONFLICT' });
      const existing = this.episodes.get(`${podcastId}:${known.episodeId}`);
      if (existing) return Promise.resolve({ kind: 'EXISTING', episode: existing });
    }
    this.episodes.set(`${podcastId}:${episode.id}`, episode);
    this.keys.set(keyId, { fingerprint: requestFingerprint, episodeId: episode.id });
    return Promise.resolve({ kind: 'CREATED', episode });
  }

  get(podcastId: string, episodeId: string): Promise<EpisodeWorkspace | null> {
    return Promise.resolve(this.episodes.get(`${podcastId}:${episodeId}`) ?? null);
  }

  list(podcastId: string): Promise<EpisodeWorkspace[]> {
    return Promise.resolve(
      [...this.episodes.values()]
        .filter((e) => e.podcastId === podcastId)
        .sort((a, b) => a.createdAtMs - b.createdAtMs),
    );
  }

  replace(episode: EpisodeWorkspace, expectedRevision: number): Promise<boolean> {
    const key = `${episode.podcastId}:${episode.id}`;
    const current = this.episodes.get(key);
    if (current?.revision !== expectedRevision) return Promise.resolve(false);
    this.episodes.set(key, { ...episode, revision: expectedRevision + 1 });
    return Promise.resolve(true);
  }
}
