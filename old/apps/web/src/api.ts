export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly correlationId: string | null;
  readonly details: unknown;

  constructor(
    status: number,
    code: string,
    message: string,
    correlationId: string | null,
    details?: unknown,
  ) {
    super(message);
    this.status = status;
    this.code = code;
    this.correlationId = correlationId;
    this.details = details;
  }
}

export interface User {
  id: string;
  email: string;
  displayName: string;
}
export interface PodcastSummary {
  id: string;
  name: string;
  role: string;
}
export interface EpisodeSummary {
  id: string;
  title: string;
  date: string;
  status: string;
  revision: number;
}
export interface Segment {
  id: string;
  key: string;
  title: string;
  objective: string;
  notes: string;
  questions: string[];
  targetDurationSec: number;
  status: 'TODO' | 'IN_PROGRESS' | 'READY';
}
export interface Episode {
  id: string;
  podcastId: string;
  title: string;
  date: string;
  revision: number;
  segments: Segment[];
  scenes: { id: string; key: string; name: string; layout: string }[];
  rundown: { order: number; segmentId: string }[];
}
export interface StudioState {
  version: number;
  program: { kind: string; id: string } | null;
  preview: { kind: string; id: string } | null;
  overlays: string[];
  recording: { status: 'IDLE' } | { status: 'RECORDING'; sessionId: string };
  consents: Record<string, boolean>;
}
export interface RoomAccess {
  url: string;
  room: string;
  token: string;
}
export interface InvitationInfo {
  podcastName: string;
  episodeTitle: string;
  role: 'GUEST' | 'HOST';
  displayName: string | null;
  expiresAt: string;
}

export interface ClientDeps {
  fetch: typeof fetch;
  /** Identifiant aléatoire (clé d'idempotence, identifiant de commande). */
  newId: () => string;
}

type Body = Record<string, unknown> | undefined;

/**
 * Client de l'API. Même origine : le cookie de session part avec chaque requête (`credentials: 'same-origin'`),
 * aucun jeton n'est lu ni stocké par le JavaScript de la page.
 */
export class ApiClient {
  private readonly deps: ClientDeps;

  constructor(deps: ClientDeps) {
    this.deps = deps;
  }

  newId(): string {
    return this.deps.newId();
  }

  private async request<T>(method: string, path: string, body?: Body): Promise<T> {
    const response = await this.deps.fetch(path, {
      method,
      credentials: 'same-origin',
      headers: body === undefined ? {} : { 'content-type': 'application/json' },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });
    const text = await response.text();
    let payload: unknown;
    try {
      payload = text.length > 0 ? JSON.parse(text) : null;
    } catch {
      payload = null;
    }
    if (!response.ok) {
      const error = (
        payload as { error?: { code?: string; message?: string; details?: unknown } } | null
      )?.error;
      const correlationId =
        (payload as { correlationId?: string } | null)?.correlationId ??
        response.headers.get('x-correlation-id');
      throw new ApiError(
        response.status,
        error?.code ?? 'UNKNOWN',
        error?.message ?? `Erreur ${String(response.status)}`,
        correlationId,
        error?.details,
      );
    }
    return payload as T;
  }

  login(email: string, password: string): Promise<{ user: User }> {
    return this.request('POST', '/api/auth/login', { email, password });
  }
  logout(): Promise<unknown> {
    return this.request('POST', '/api/auth/logout');
  }
  me(): Promise<{ user: User; podcasts: PodcastSummary[] }> {
    return this.request('GET', '/api/me');
  }
  createPodcast(name: string): Promise<{ podcast: PodcastSummary }> {
    return this.request('POST', '/api/podcasts', { name });
  }
  listEpisodes(podcastId: string): Promise<{ episodes: EpisodeSummary[] }> {
    return this.request('GET', `/api/podcasts/${podcastId}/episodes`);
  }
  /** La clé d'idempotence est fournie par l'appelant : un double clic ou un rejeu réseau ne crée qu'un épisode. */
  createEpisode(
    podcastId: string,
    input: { title: string; date: string },
    idempotencyKey: string,
  ): Promise<{ episode: Episode; created: boolean }> {
    return this.request('POST', `/api/podcasts/${podcastId}/episodes`, {
      templateId: 'standard',
      title: input.title,
      date: input.date,
      idempotencyKey,
    });
  }
  getEpisode(podcastId: string, episodeId: string): Promise<{ episode: Episode }> {
    return this.request('GET', `/api/podcasts/${podcastId}/episodes/${episodeId}`);
  }
  patchSegment(
    podcastId: string,
    episodeId: string,
    segmentId: string,
    expectedRevision: number,
    patch: { notes?: string; status?: Segment['status'] },
  ): Promise<{ episode: Episode }> {
    return this.request(
      'PATCH',
      `/api/podcasts/${podcastId}/episodes/${episodeId}/segments/${segmentId}`,
      {
        expectedRevision,
        patch,
      },
    );
  }
  createInvitation(
    podcastId: string,
    episodeId: string,
    input: { displayName?: string },
  ): Promise<{ token: string; expiresAt: string }> {
    return this.request('POST', `/api/podcasts/${podcastId}/episodes/${episodeId}/invitations`, {
      role: 'GUEST',
      ...(input.displayName ? { displayName: input.displayName } : {}),
    });
  }
  studioState(podcastId: string, episodeId: string): Promise<{ state: StudioState }> {
    return this.request('GET', `/api/podcasts/${podcastId}/episodes/${episodeId}/studio`);
  }
  studioToken(
    podcastId: string,
    episodeId: string,
  ): Promise<{ participantId: string; livekit: RoomAccess }> {
    return this.request('POST', `/api/podcasts/${podcastId}/episodes/${episodeId}/studio/token`);
  }
  studioConsent(podcastId: string, episodeId: string): Promise<{ ok: boolean }> {
    return this.request('POST', `/api/podcasts/${podcastId}/episodes/${episodeId}/studio/consent`);
  }
  studioCommand(
    podcastId: string,
    episodeId: string,
    command: Record<string, unknown>,
    expectedVersion?: number,
  ): Promise<{ ok: boolean; state?: StudioState; error?: { code: string; message: string } }> {
    return this.request(
      'POST',
      `/api/podcasts/${podcastId}/episodes/${episodeId}/studio/commands`,
      {
        commandId: this.deps.newId(),
        command,
        ...(expectedVersion === undefined ? {} : { expectedVersion }),
      },
    );
  }
  invitationInfo(token: string): Promise<{ invitation: InvitationInfo }> {
    return this.request('GET', `/api/invitations/${token}`);
  }
  invitationJoin(
    token: string,
    displayName?: string,
  ): Promise<{ participant: { id: string; displayName: string }; livekit: RoomAccess }> {
    return this.request(
      'POST',
      `/api/invitations/${token}/join`,
      displayName ? { displayName } : {},
    );
  }
  invitationConsent(token: string): Promise<{ ok: boolean }> {
    return this.request('POST', `/api/invitations/${token}/consent`, {});
  }
}
