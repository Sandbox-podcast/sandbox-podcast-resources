import { randomUUID } from 'node:crypto';
import Fastify, { type FastifyInstance, type FastifyReply, type FastifyRequest } from 'fastify';
import {
  DEFAULT_POLICY,
  StudioService,
  type Command,
  type CommandBody,
  type Role as StudioRole,
} from '@podcast/studio-control';
import { z } from 'zod';
import { writeAudit } from './audit.ts';
import { PAGE_CSP, readStatic } from './static.ts';
import { isTokenShape } from './auth/tokens.ts';
import type { Config } from './config.ts';
import { withTransaction, type Pool } from './db/db.ts';
import { issueRoomToken, roomName } from './livekit.ts';
import { can, type Action, type Role } from './rbac.ts';
import {
  DEFAULT_AUTH,
  authenticate,
  createUser,
  login,
  logout,
  type AuthOptions,
  type User,
} from './services/auth-service.ts';
import {
  createEpisode,
  PgEpisodeRepository,
  segmentPatchSchema,
  updateSegment,
} from './services/episodes.ts';
import {
  createInvitation,
  describeInvitation,
  joinWithInvitation,
  revokeInvitations,
} from './services/invitations.ts';
import { PgStudioStore } from './services/pg-studio-store.ts';
import { addMember, createPodcast, listPodcasts, membershipRole } from './services/podcasts.ts';

declare module 'fastify' {
  interface FastifyRequest {
    correlationId: string;
    /** Utilisateur authentifié, et d'où vient son jeton (le cookie exige un contrôle d'origine). */
    auth: { user: User; token: string; viaCookie: boolean } | null;
  }
}

export interface AppOptions {
  config: Config;
  pool: Pool;
  now?: () => Date;
  auth?: AuthOptions;
  /** Exiger le consentement de tous les participants connus avant de démarrer l'enregistrement. */
  requireRecordingConsent?: boolean;
}

const CORRELATION = /^[A-Za-z0-9._-]{8,64}$/;
const SESSION_COOKIE = 'session';

/** Limiteur à fenêtre glissante, en mémoire : protège les points d'entrée sans compte (connexion, invitations). */
class WindowLimiter {
  private readonly hits = new Map<string, number[]>();
  private readonly limit: number;
  private readonly windowMs: number;

  constructor(limit: number, windowMs: number) {
    this.limit = limit;
    this.windowMs = windowMs;
  }

  /** Vrai si la requête est autorisée. */
  allow(key: string, nowMs: number): boolean {
    const recent = (this.hits.get(key) ?? []).filter((t) => nowMs - t < this.windowMs);
    if (recent.length >= this.limit) {
      this.hits.set(key, recent);
      return false;
    }
    recent.push(nowMs);
    this.hits.set(key, recent);
    return true;
  }
}

const uuid = z.uuid();
const sourceSchema = z.strictObject({
  kind: z.enum([
    'scene',
    'image',
    'video',
    'presentation',
    'document',
    'webpage',
    'screenshare',
    'graphic',
  ]),
  id: z.string().min(1).max(100),
  assetId: z.string().min(1).max(100).optional(),
});
const commandBodySchema = z.discriminatedUnion('type', [
  z.strictObject({ type: z.literal('SET_PREVIEW'), source: sourceSchema }),
  z.strictObject({
    type: z.literal('TAKE'),
    expectPreviewId: z.string().min(1).max(100),
    transition: z.enum(['CUT', 'MIX']).optional(),
  }),
  z.strictObject({ type: z.literal('CUT'), source: sourceSchema }),
  z.strictObject({ type: z.literal('SHOW_OVERLAY'), overlayId: z.string().min(1).max(100) }),
  z.strictObject({ type: z.literal('HIDE_OVERLAY'), overlayId: z.string().min(1).max(100) }),
  z.strictObject({ type: z.literal('START_RECORDING'), sessionId: z.string().min(1).max(100) }),
  z.strictObject({ type: z.literal('STOP_RECORDING') }),
  z.strictObject({ type: z.literal('SET_AUTO_DIRECTOR'), on: z.boolean() }),
  z.strictObject({ type: z.literal('SET_SEQUENCE'), sequenceId: z.string().min(1).max(100) }),
]);

export function buildApp(options: AppOptions): FastifyInstance {
  const { config, pool } = options;
  const now = options.now ?? ((): Date => new Date());
  const authOptions = options.auth ?? {
    ...DEFAULT_AUTH,
    sessionTtlHours: config.SESSION_TTL_HOURS,
  };
  const requireConsent = options.requireRecordingConsent ?? true;
  const app = Fastify({ logger: false, bodyLimit: 256 * 1024 });
  const authLimiter = new WindowLimiter(20, 60_000);
  const publicLimiter = new WindowLimiter(60, 60_000);

  app.decorateRequest('correlationId', '');
  app.decorateRequest('auth', null);

  const fail = (
    request: FastifyRequest,
    reply: FastifyReply,
    status: number,
    code: string,
    message: string,
    details?: unknown,
  ): FastifyReply =>
    reply.status(status).send({
      error: { code, message, ...(details === undefined ? {} : { details }) },
      correlationId: request.correlationId,
    });

  app.addHook('onRequest', (request, reply, done) => {
    const given = request.headers['x-correlation-id'];
    request.correlationId =
      typeof given === 'string' && CORRELATION.test(given) ? given : randomUUID();
    void reply.header('x-correlation-id', request.correlationId);
    void reply.header('x-content-type-options', 'nosniff');
    void reply.header('referrer-policy', 'no-referrer');
    void reply.header('cache-control', 'no-store');
    void reply.header('content-security-policy', "default-src 'none'; frame-ancestors 'none'");
    done();
  });

  const cookieToken = (request: FastifyRequest): string | undefined => {
    const header = request.headers.cookie;
    if (!header) return undefined;
    for (const part of header.split(';')) {
      const [name, ...rest] = part.trim().split('=');
      if (name === SESSION_COOKIE) return rest.join('=');
    }
    return undefined;
  };

  /** Résout l'utilisateur (cookie ou jeton porteur). Les requêtes qui modifient l'état par cookie doivent venir d'une origine autorisée. */
  const resolveAuth = async (request: FastifyRequest): Promise<void> => {
    const bearer = /^Bearer (\S+)$/.exec(request.headers.authorization ?? '')?.[1];
    const cookie = cookieToken(request);
    const token = bearer ?? cookie;
    if (!isTokenShape(token)) return;
    const user = await authenticate(pool, token, now());
    if (user) request.auth = { user, token, viaCookie: bearer === undefined };
  };

  const originOk = (request: FastifyRequest): boolean => {
    const origin = request.headers.origin;
    return typeof origin === 'string' && config.ALLOWED_ORIGINS.includes(origin);
  };

  const requireUser = async (
    request: FastifyRequest,
    reply: FastifyReply,
  ): Promise<User | null> => {
    await resolveAuth(request);
    const auth = request.auth;
    if (!auth) {
      fail(request, reply, 401, 'UNAUTHENTICATED', 'Authentification requise');
      return null;
    }
    const mutating = !['GET', 'HEAD', 'OPTIONS'].includes(request.method);
    if (mutating && auth.viaCookie && !originOk(request)) {
      fail(request, reply, 403, 'BAD_ORIGIN', 'Origine non autorisée');
      return null;
    }
    return auth.user;
  };

  /** Utilisateur et rôle dans le podcast ; un podcast dont on n'est pas membre est « introuvable ». */
  const requireRole = async (
    request: FastifyRequest,
    reply: FastifyReply,
    podcastId: string,
    action: Action,
  ): Promise<{ user: User; role: Role } | null> => {
    const user = await requireUser(request, reply);
    if (!user) return null;
    const role = uuid.safeParse(podcastId).success
      ? await membershipRole(pool, podcastId, user.id)
      : null;
    if (!role) {
      fail(request, reply, 404, 'NOT_FOUND', 'Introuvable');
      return null;
    }
    if (!can(role, action)) {
      await writeAudit(pool, {
        actorUserId: user.id,
        actorKind: 'USER',
        podcastId,
        action: `denied:${action}`,
        target: request.url.split('?')[0] ?? '',
        result: 'DENIED',
        correlationId: request.correlationId,
      });
      fail(request, reply, 403, 'FORBIDDEN', 'Droits insuffisants');
      return null;
    }
    return { user, role };
  };

  const parse = <S extends z.ZodType>(
    request: FastifyRequest,
    reply: FastifyReply,
    schema: S,
    data: unknown,
  ): z.infer<S> | null => {
    const result = schema.safeParse(data);
    if (result.success) return result.data;
    fail(
      request,
      reply,
      400,
      'INVALID_INPUT',
      'Requête invalide',
      result.error.issues.map((i) => `${i.path.join('.')} : ${i.message}`),
    );
    return null;
  };

  const setCookie = (reply: FastifyReply, token: string, expiresAt: Date): void => {
    void reply.header(
      'set-cookie',
      `${SESSION_COOKIE}=${token}; Path=/; HttpOnly; SameSite=Strict; Expires=${expiresAt.toUTCString()}${config.COOKIE_SECURE ? '; Secure' : ''}`,
    );
  };

  // --- Santé ---
  app.get('/healthz', () => ({ status: 'ok' }));
  app.get('/readyz', async (request, reply) => {
    try {
      await pool.query('select 1');
      return { status: 'ready' };
    } catch {
      return fail(request, reply, 503, 'NOT_READY', 'Base de données indisponible');
    }
  });

  // --- Authentification ---
  const credentials = z.strictObject({
    email: z.string().min(3).max(254),
    password: z.string().min(1).max(256),
  });

  app.post('/api/auth/register', async (request, reply) => {
    if (!config.ALLOW_REGISTRATION)
      return fail(request, reply, 403, 'REGISTRATION_CLOSED', "L'inscription est fermée");
    if (!authLimiter.allow(`register:${request.ip}`, now().getTime()))
      return fail(request, reply, 429, 'RATE_LIMITED', 'Trop de requêtes');
    if (!originOk(request)) return fail(request, reply, 403, 'BAD_ORIGIN', 'Origine non autorisée');
    const body = parse(
      request,
      reply,
      credentials.extend({ displayName: z.string().trim().min(1).max(120) }),
      request.body,
    );
    if (!body) return reply;
    const created = await createUser(pool, body, authOptions);
    if (!created.ok) {
      if (created.reason === 'WEAK_PASSWORD')
        return fail(
          request,
          reply,
          400,
          'WEAK_PASSWORD',
          'Mot de passe trop faible',
          created.problems,
        );
      return fail(
        request,
        reply,
        400,
        created.reason,
        created.reason === 'EMAIL_TAKEN' ? 'Adresse déjà utilisée' : 'Adresse invalide',
      );
    }
    await writeAudit(pool, {
      actorUserId: created.user.id,
      actorKind: 'USER',
      podcastId: null,
      action: 'user.register',
      target: `user:${created.user.id}`,
      result: 'OK',
      correlationId: request.correlationId,
    });
    return reply.status(201).send({ user: created.user });
  });

  app.post('/api/auth/login', async (request, reply) => {
    if (!authLimiter.allow(`login:${request.ip}`, now().getTime()))
      return fail(request, reply, 429, 'RATE_LIMITED', 'Trop de requêtes');
    // Si un navigateur annonce son origine, elle doit être autorisée (protège contre la connexion forcée).
    if (request.headers.origin !== undefined && !originOk(request))
      return fail(request, reply, 403, 'BAD_ORIGIN', 'Origine non autorisée');
    const body = parse(request, reply, credentials, request.body);
    if (!body) return reply;
    const result = await login(pool, body, now(), authOptions);
    if (!result.ok) {
      await writeAudit(pool, {
        actorUserId: null,
        actorKind: 'ANONYMOUS',
        podcastId: null,
        action: 'auth.login',
        target: 'session',
        result: 'DENIED',
        correlationId: request.correlationId,
        detail: { reason: result.reason },
      });
      if (result.reason === 'LOCKED')
        return fail(
          request,
          reply,
          429,
          'ACCOUNT_LOCKED',
          'Trop de tentatives, réessayez plus tard',
        );
      return fail(request, reply, 401, 'INVALID_CREDENTIALS', 'Adresse ou mot de passe incorrect');
    }
    await writeAudit(pool, {
      actorUserId: result.user.id,
      actorKind: 'USER',
      podcastId: null,
      action: 'auth.login',
      target: 'session',
      result: 'OK',
      correlationId: request.correlationId,
    });
    setCookie(reply, result.token, result.expiresAt);
    return { user: result.user, token: result.token, expiresAt: result.expiresAt };
  });

  app.post('/api/auth/logout', async (request, reply) => {
    const user = await requireUser(request, reply);
    if (!user || !request.auth) return reply;
    await logout(pool, request.auth.token, now());
    void reply.header(
      'set-cookie',
      `${SESSION_COOKIE}=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0`,
    );
    return { ok: true };
  });

  app.get('/api/me', async (request, reply) => {
    const user = await requireUser(request, reply);
    if (!user) return reply;
    return { user, podcasts: await listPodcasts(pool, user.id) };
  });

  // --- Podcasts ---
  app.post('/api/podcasts', async (request, reply) => {
    const user = await requireUser(request, reply);
    if (!user) return reply;
    const body = parse(
      request,
      reply,
      z.strictObject({ name: z.string().trim().min(1).max(200) }),
      request.body,
    );
    if (!body) return reply;
    const podcast = await createPodcast(
      pool,
      { userId: user.id, correlationId: request.correlationId },
      body.name,
    );
    return reply.status(201).send({ podcast });
  });

  app.post<{ Params: { podcastId: string } }>(
    '/api/podcasts/:podcastId/members',
    async (request, reply) => {
      const ctx = await requireRole(
        request,
        reply,
        request.params.podcastId,
        'podcast:manage-members',
      );
      if (!ctx) return reply;
      const body = parse(
        request,
        reply,
        z.strictObject({
          email: z.string().min(3).max(254),
          role: z.enum(['ADMIN', 'PRODUCER', 'HOST', 'EDITOR', 'VIEWER']),
        }),
        request.body,
      );
      if (!body) return reply;
      const result = await addMember(
        pool,
        { userId: ctx.user.id, correlationId: request.correlationId },
        request.params.podcastId,
        body.email,
        body.role,
      );
      if (!result.ok) return fail(request, reply, 404, 'USER_NOT_FOUND', 'Utilisateur introuvable');
      return reply.status(204).send();
    },
  );

  // --- Épisodes ---
  app.get<{ Params: { podcastId: string } }>(
    '/api/podcasts/:podcastId/episodes',
    async (request, reply) => {
      const ctx = await requireRole(request, reply, request.params.podcastId, 'episode:read');
      if (!ctx) return reply;
      const episodes = await new PgEpisodeRepository(pool).list(request.params.podcastId);
      return {
        episodes: episodes.map((e) => ({
          id: e.id,
          title: e.title,
          date: e.date,
          status: e.status,
          revision: e.revision,
        })),
      };
    },
  );

  app.post<{ Params: { podcastId: string } }>(
    '/api/podcasts/:podcastId/episodes',
    async (request, reply) => {
      const ctx = await requireRole(request, reply, request.params.podcastId, 'episode:create');
      if (!ctx) return reply;
      const body = parse(
        request,
        reply,
        z.strictObject({
          templateId: z.string().min(1).max(100),
          templateVersion: z.number().int().min(1).optional(),
          title: z.string().trim().min(1).max(200),
          date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
          idempotencyKey: z.string().min(8).max(128),
        }),
        request.body,
      );
      if (!body) return reply;
      const result = await createEpisode(
        pool,
        { userId: ctx.user.id, correlationId: request.correlationId },
        request.params.podcastId,
        {
          templateId: body.templateId,
          ...(body.templateVersion === undefined ? {} : { templateVersion: body.templateVersion }),
          title: body.title,
          date: body.date,
          idempotencyKey: body.idempotencyKey,
        },
      );
      if (!result.ok) {
        const status =
          result.error.code === 'IDEMPOTENCY_KEY_CONFLICT'
            ? 409
            : result.error.code.endsWith('NOT_FOUND')
              ? 404
              : 400;
        return fail(
          request,
          reply,
          status,
          result.error.code,
          result.error.message,
          result.error.details,
        );
      }
      return reply
        .status(result.created ? 201 : 200)
        .send({ episode: result.episode, created: result.created });
    },
  );

  app.get<{ Params: { podcastId: string; episodeId: string } }>(
    '/api/podcasts/:podcastId/episodes/:episodeId',
    async (request, reply) => {
      const ctx = await requireRole(request, reply, request.params.podcastId, 'episode:read');
      if (!ctx) return reply;
      const episode = uuid.safeParse(request.params.episodeId).success
        ? await new PgEpisodeRepository(pool).get(
            request.params.podcastId,
            request.params.episodeId,
          )
        : null;
      if (!episode) return fail(request, reply, 404, 'NOT_FOUND', 'Introuvable');
      return { episode };
    },
  );

  app.patch<{ Params: { podcastId: string; episodeId: string; segmentId: string } }>(
    '/api/podcasts/:podcastId/episodes/:episodeId/segments/:segmentId',
    async (request, reply) => {
      const ctx = await requireRole(
        request,
        reply,
        request.params.podcastId,
        'episode:edit-rundown',
      );
      if (!ctx) return reply;
      const body = parse(
        request,
        reply,
        z.strictObject({ expectedRevision: z.number().int().min(1), patch: segmentPatchSchema }),
        request.body,
      );
      if (!body || !uuid.safeParse(request.params.episodeId).success)
        return body ? fail(request, reply, 404, 'NOT_FOUND', 'Introuvable') : reply;
      const result = await updateSegment(
        pool,
        { userId: ctx.user.id, correlationId: request.correlationId },
        request.params.podcastId,
        request.params.episodeId,
        request.params.segmentId,
        body.expectedRevision,
        body.patch,
      );
      if (result.ok) return { episode: result.episode };
      if (result.reason === 'CONFLICT')
        return fail(request, reply, 409, 'CONFLICT', "L'épisode a changé depuis votre lecture", {
          currentRevision: result.currentRevision,
        });
      return fail(request, reply, 404, 'NOT_FOUND', 'Introuvable');
    },
  );

  // --- Invitations (côté producteur) ---
  app.post<{ Params: { podcastId: string; episodeId: string } }>(
    '/api/podcasts/:podcastId/episodes/:episodeId/invitations',
    async (request, reply) => {
      const ctx = await requireRole(request, reply, request.params.podcastId, 'episode:invite');
      if (!ctx) return reply;
      const body = parse(
        request,
        reply,
        z.strictObject({
          role: z.enum(['GUEST', 'HOST']).default('GUEST'),
          displayName: z.string().trim().min(1).max(120).optional(),
          ttlHours: z
            .number()
            .int()
            .min(1)
            .max(24 * 14)
            .default(72),
        }),
        request.body ?? {},
      );
      if (!body || !uuid.safeParse(request.params.episodeId).success)
        return body ? fail(request, reply, 404, 'NOT_FOUND', 'Introuvable') : reply;
      const created = await createInvitation(
        pool,
        { userId: ctx.user.id, correlationId: request.correlationId },
        request.params.podcastId,
        request.params.episodeId,
        {
          role: body.role,
          ttlHours: body.ttlHours,
          ...(body.displayName === undefined ? {} : { displayName: body.displayName }),
        },
        now(),
      );
      if (!created) return fail(request, reply, 404, 'NOT_FOUND', 'Introuvable');
      return reply.status(201).send({ token: created.token, expiresAt: created.expiresAt });
    },
  );

  app.delete<{ Params: { podcastId: string; episodeId: string } }>(
    '/api/podcasts/:podcastId/episodes/:episodeId/invitations',
    async (request, reply) => {
      const ctx = await requireRole(request, reply, request.params.podcastId, 'episode:invite');
      if (!ctx) return reply;
      if (!uuid.safeParse(request.params.episodeId).success)
        return fail(request, reply, 404, 'NOT_FOUND', 'Introuvable');
      const revoked = await revokeInvitations(
        pool,
        request.params.podcastId,
        request.params.episodeId,
        now(),
      );
      await writeAudit(pool, {
        actorUserId: ctx.user.id,
        actorKind: 'USER',
        podcastId: request.params.podcastId,
        action: 'invitation.revoke-all',
        target: `episode:${request.params.episodeId}`,
        result: 'OK',
        correlationId: request.correlationId,
        detail: { revoked },
      });
      return { revoked };
    },
  );

  // --- Invités (sans compte) ---
  const guestRoute = (
    request: FastifyRequest<{ Params: { token: string } }>,
    reply: FastifyReply,
    run: (token: string) => Promise<object | null>,
  ): Promise<unknown> => {
    if (!publicLimiter.allow(`guest:${request.ip}`, now().getTime()))
      return Promise.resolve(fail(request, reply, 429, 'RATE_LIMITED', 'Trop de requêtes'));
    // Un jeton mal formé n'atteint jamais la base.
    if (!isTokenShape(request.params.token))
      return Promise.resolve(
        fail(request, reply, 404, 'NOT_FOUND', 'Invitation introuvable ou expirée'),
      );
    return run(request.params.token).then(
      (result) =>
        result ?? fail(request, reply, 404, 'NOT_FOUND', 'Invitation introuvable ou expirée'),
    );
  };

  app.get<{ Params: { token: string } }>('/api/invitations/:token', (request, reply) =>
    guestRoute(request, reply, async (token) => {
      const info = await describeInvitation(pool, token, now());
      return info ? { invitation: info } : null;
    }),
  );

  app.post<{ Params: { token: string } }>('/api/invitations/:token/join', (request, reply) =>
    guestRoute(request, reply, async (token) => {
      const body = z
        .strictObject({ displayName: z.string().trim().min(1).max(120).optional() })
        .safeParse(request.body ?? {});
      if (!body.success) return null;
      const joined = await joinWithInvitation(
        pool,
        token,
        body.data.displayName,
        request.correlationId,
        now(),
      );
      if (!joined) return null;
      const livekitToken = await issueRoomToken(config, {
        episodeId: joined.episodeId,
        participantId: joined.participantId,
        displayName: joined.displayName,
        role: joined.role,
      });
      return {
        participant: {
          id: joined.participantId,
          displayName: joined.displayName,
          role: joined.role,
        },
        livekit: { url: config.LIVEKIT_URL, room: roomName(joined.episodeId), token: livekitToken },
      };
    }),
  );

  // --- Studio (membres) ---
  const studioFor = async (
    episodeId: string,
  ): Promise<{ service: StudioService; store: PgStudioStore }> => {
    // Le consentement de tous les participants connus de l'épisode est requis avant d'enregistrer.
    const participants = requireConsent
      ? (
          await pool.query<{ id: string }>('select id from participants where episode_id = $1', [
            episodeId,
          ])
        ).rows.map((r) => r.id)
      : [];
    const store = new PgStudioStore(pool);
    return {
      service: new StudioService(store, { ...DEFAULT_POLICY, requiredConsentFrom: participants }),
      store,
    };
  };

  const episodeExists = async (podcastId: string, episodeId: string): Promise<boolean> =>
    uuid.safeParse(episodeId).success &&
    (await new PgEpisodeRepository(pool).get(podcastId, episodeId)) !== null;

  app.post<{ Params: { podcastId: string; episodeId: string } }>(
    '/api/podcasts/:podcastId/episodes/:episodeId/studio/token',
    async (request, reply) => {
      const ctx = await requireRole(request, reply, request.params.podcastId, 'studio:join');
      if (!ctx) return reply;
      const { podcastId, episodeId } = request.params;
      if (!(await episodeExists(podcastId, episodeId)))
        return fail(request, reply, 404, 'NOT_FOUND', 'Introuvable');
      const participantId = await withTransaction(pool, async (client) => {
        const existing = await client.query<{ id: string }>(
          'select id from participants where episode_id = $1 and user_id = $2',
          [episodeId, ctx.user.id],
        );
        const found = existing.rows[0];
        if (found) return found.id;
        const role =
          ctx.role === 'ADMIN' || ctx.role === 'PRODUCER' || ctx.role === 'HOST'
            ? ctx.role
            : 'HOST';
        const created = await client.query<{ id: string }>(
          'insert into participants (episode_id, user_id, display_name, role) values ($1, $2, $3, $4) returning id',
          [episodeId, ctx.user.id, ctx.user.displayName, role],
        );
        const id = created.rows[0]?.id;
        if (!id) throw new Error('participant sans identifiant');
        await writeAudit(client, {
          actorUserId: ctx.user.id,
          actorKind: 'USER',
          podcastId,
          action: 'studio.join',
          target: `participant:${id}`,
          result: 'OK',
          correlationId: request.correlationId,
          detail: { role },
        });
        return id;
      });
      const token = await issueRoomToken(config, {
        episodeId,
        participantId,
        displayName: ctx.user.displayName,
        role: ctx.role === 'ADMIN' || ctx.role === 'PRODUCER' ? ctx.role : 'HOST',
      });
      return {
        participantId,
        livekit: { url: config.LIVEKIT_URL, room: roomName(episodeId), token },
      };
    },
  );

  // Consentement d'un membre : il doit d'abord avoir rejoint le studio (ligne `participants`).
  app.post<{ Params: { podcastId: string; episodeId: string } }>(
    '/api/podcasts/:podcastId/episodes/:episodeId/studio/consent',
    async (request, reply) => {
      const ctx = await requireRole(request, reply, request.params.podcastId, 'studio:join');
      if (!ctx) return reply;
      const { podcastId, episodeId } = request.params;
      if (!(await episodeExists(podcastId, episodeId)))
        return fail(request, reply, 404, 'NOT_FOUND', 'Introuvable');
      const found = await pool.query<{ id: string }>(
        'select id from participants where episode_id = $1 and user_id = $2',
        [episodeId, ctx.user.id],
      );
      const participantId = found.rows[0]?.id;
      if (!participantId)
        return fail(request, reply, 409, 'NOT_IN_STUDIO', "Rejoignez d'abord le studio");
      const { service } = await studioFor(episodeId);
      const executed = await service.execute(episodeId, {
        type: 'GRANT_CONSENT',
        participantId,
        commandId: `consent-${participantId}`,
        actor: { id: participantId, kind: 'USER', roles: ['GUEST'] },
        atMs: now().getTime(),
        correlationId: request.correlationId,
      });
      await writeAudit(pool, {
        actorUserId: ctx.user.id,
        actorKind: 'USER',
        podcastId,
        action: 'studio.GRANT_CONSENT',
        target: `participant:${participantId}`,
        result: executed.result.ok ? 'OK' : 'DENIED',
        correlationId: request.correlationId,
      });
      return { ok: executed.result.ok };
    },
  );

  app.get<{ Params: { podcastId: string; episodeId: string } }>(
    '/api/podcasts/:podcastId/episodes/:episodeId/studio',
    async (request, reply) => {
      const ctx = await requireRole(request, reply, request.params.podcastId, 'episode:read');
      if (!ctx) return reply;
      const { podcastId, episodeId } = request.params;
      if (!(await episodeExists(podcastId, episodeId)))
        return fail(request, reply, 404, 'NOT_FOUND', 'Introuvable');
      const { store } = await studioFor(episodeId);
      return { state: await store.load(episodeId), events: await store.events(episodeId) };
    },
  );

  app.post<{ Params: { podcastId: string; episodeId: string } }>(
    '/api/podcasts/:podcastId/episodes/:episodeId/studio/commands',
    async (request, reply) => {
      const ctx = await requireRole(request, reply, request.params.podcastId, 'studio:control');
      if (!ctx) return reply;
      const body = parse(
        request,
        reply,
        z.strictObject({
          commandId: z.string().min(8).max(128),
          expectedVersion: z.number().int().min(0).optional(),
          command: commandBodySchema,
        }),
        request.body,
      );
      if (!body) return reply;
      const { podcastId, episodeId } = request.params;
      if (!(await episodeExists(podcastId, episodeId)))
        return fail(request, reply, 404, 'NOT_FOUND', 'Introuvable');
      const { service } = await studioFor(episodeId);
      const studioRole: StudioRole = ctx.role === 'VIEWER' ? 'EDITOR' : ctx.role;
      const command = {
        ...(body.command as CommandBody),
        commandId: body.commandId,
        actor: { id: ctx.user.id, kind: 'USER', roles: [studioRole] },
        atMs: now().getTime(),
        correlationId: request.correlationId,
        ...(body.expectedVersion === undefined ? {} : { expectedVersion: body.expectedVersion }),
      } as Command;
      const executed = await service.execute(episodeId, command);
      await writeAudit(pool, {
        actorUserId: ctx.user.id,
        actorKind: 'USER',
        podcastId,
        action: `studio.${body.command.type}`,
        target: `episode:${episodeId}`,
        result: executed.result.ok ? 'OK' : 'DENIED',
        correlationId: request.correlationId,
        detail: executed.result.ok
          ? { replayed: executed.replayed }
          : { code: executed.result.error.code },
      });
      return reply.status(executed.result.ok ? 200 : 409).send({
        ok: executed.result.ok,
        ...(executed.result.ok
          ? { state: executed.result.state }
          : { error: executed.result.error }),
        events: executed.events,
        replayed: executed.replayed,
      });
    },
  );

  // Consentement : seule la personne concernée peut le donner, en tant que participant de l'épisode.
  app.post<{ Params: { token: string } }>('/api/invitations/:token/consent', (request, reply) =>
    guestRoute(request, reply, async (token) => {
      const joined = await joinWithInvitation(pool, token, undefined, request.correlationId, now());
      if (!joined) return null;
      const { service } = await studioFor(joined.episodeId);
      const commandId = `consent-${joined.participantId}`;
      const executed = await service.execute(joined.episodeId, {
        type: 'GRANT_CONSENT',
        participantId: joined.participantId,
        commandId,
        actor: { id: joined.participantId, kind: 'USER', roles: ['GUEST'] },
        atMs: now().getTime(),
        correlationId: request.correlationId,
      });
      return { ok: executed.result.ok };
    }),
  );

  // --- Pages de l'application web (même origine : le cookie de session ne quitte jamais le site) ---
  app.get('/*', async (request, reply) => {
    const path = request.url.split('?')[0] ?? '/';
    if (!config.WEB_DIR || path.startsWith('/api/'))
      return fail(request, reply, 404, 'NOT_FOUND', 'Introuvable');
    const file = await readStatic(config.WEB_DIR, path);
    if (!file) return fail(request, reply, 404, 'NOT_FOUND', 'Introuvable');
    void reply.header('content-security-policy', PAGE_CSP);
    void reply.header('cache-control', 'no-cache');
    return reply.type(file.type).send(file.body);
  });

  app.setErrorHandler((error, request, reply) => {
    if (typeof error === 'object' && error !== null && 'validation' in error)
      return fail(request, reply, 400, 'INVALID_INPUT', 'Requête invalide');
    const status =
      typeof error === 'object' &&
      error !== null &&
      'statusCode' in error &&
      typeof error.statusCode === 'number' &&
      error.statusCode < 500
        ? error.statusCode
        : 500;
    if (status >= 500) {
      // Le détail reste côté serveur ; l'appelant reçoit seulement l'identifiant de corrélation.
      request.log.error(error);
      console.error(`[${request.correlationId}]`, error);
      return fail(
        request,
        reply,
        500,
        'INTERNAL',
        `Erreur interne (corrélation ${request.correlationId})`,
      );
    }
    return fail(request, reply, status, 'BAD_REQUEST', 'Requête incorrecte');
  });

  return app;
}
