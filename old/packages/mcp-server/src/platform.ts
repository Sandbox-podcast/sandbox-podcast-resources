import {
  createEpisodeFromTemplate,
  type AssetCatalog,
  type EpisodeRepository,
  type EpisodeWorkspace,
  type FactoryErrorCode,
  type TemplateCatalog,
  type ThemeCatalog,
} from '@podcast/episode-factory';
import type { CollabServer } from '@podcast/collab';
import { validatePresentationHtml } from '@podcast/presentation-sandbox';
import { z } from 'zod';
import {
  PRESENTATION_SCHEMA,
  contentHash,
  readHtml,
  readTitle,
  writePresentation,
} from './presentations.ts';
import {
  newCorrelationId,
  sha256,
  type AuditResult,
  type AuditSink,
  type ConfirmationService,
  type Credential,
  type CredentialStore,
  type RateLimiter,
  type Scope,
} from './security.ts';

export type ErrorCode =
  | 'UNKNOWN_TOOL'
  | 'UNAUTHENTICATED'
  | 'FORBIDDEN'
  | 'RATE_LIMITED'
  | 'INVALID_INPUT'
  | 'NOT_FOUND'
  | 'CONFLICT'
  | 'ALREADY_EXISTS'
  | 'CONFIRMATION_REQUIRED'
  | 'INTERNAL';

export interface ToolError {
  code: ErrorCode;
  message: string;
  details?: string[];
  requiredScopes?: Scope[];
  retryAfterMs?: number;
  confirmationId?: string;
}

export type Envelope =
  | {
      ok: true;
      correlationId: string;
      /** `UNCHANGED` : la demande était déjà satisfaite (rejeu idempotent, contenu identique). */
      result: 'OK' | 'UNCHANGED';
      data: Record<string, unknown>;
    }
  | { ok: false; correlationId: string; error: ToolError };

export type Outcome =
  | { ok: true; result?: 'OK' | 'UNCHANGED'; data: Record<string, unknown> }
  | { ok: false; error: ToolError };

export interface PodcastCatalogs {
  templates: TemplateCatalog;
  assets: AssetCatalog;
  themes: ThemeCatalog;
}

export interface PlatformDeps {
  credentials: CredentialStore;
  episodes: EpisodeRepository;
  /** Les catalogues d'un podcast : un credential ne voit jamais ceux d'un autre. */
  catalogs: (podcastId: string) => PodcastCatalogs;
  collab: CollabServer;
  audit: AuditSink;
  limiter: RateLimiter;
  confirmations: ConfirmationService;
  now?: () => number;
}

interface Ctx {
  credential: Credential;
  correlationId: string;
  deps: PlatformDeps;
  now: () => number;
}

export interface ToolMetadata {
  name: string;
  description: string;
  kind: 'read' | 'mutation';
  requiredScopes: readonly Scope[];
  idempotencyBehavior: string;
  sideEffects: string;
  confirmationPolicy: 'NONE' | 'HUMAN_REQUIRED';
  auditPolicy: string;
  rateLimit: { cost: number };
}

export interface Tool extends ToolMetadata {
  input: z.ZodType;
  /** Forme des données retournées (dans `data`), pour l'`outputSchema` MCP. */
  data: z.ZodType;
  prepare(
    raw: unknown,
  ):
    | { ok: true; target: string; run: (ctx: Ctx) => Promise<Outcome> }
    | { ok: false; issues: string[] };
}

const READ_COST = 1;
const MUTATION_COST = 5;
const MAX_CAS_ATTEMPTS = 3;

const fail = (code: ErrorCode, message: string, extra: Partial<ToolError> = {}): Outcome => ({
  ok: false,
  error: { code, message, ...extra },
});

const AUDIT_RESULT: Record<ErrorCode, AuditResult> = {
  UNKNOWN_TOOL: 'INVALID',
  UNAUTHENTICATED: 'DENIED',
  FORBIDDEN: 'DENIED',
  RATE_LIMITED: 'RATE_LIMITED',
  INVALID_INPUT: 'INVALID',
  NOT_FOUND: 'NOT_FOUND',
  CONFLICT: 'CONFLICT',
  ALREADY_EXISTS: 'CONFLICT',
  CONFIRMATION_REQUIRED: 'CONFIRMATION_REQUIRED',
  INTERNAL: 'ERROR',
};

const FACTORY_ERRORS: Record<FactoryErrorCode, ErrorCode> = {
  VALIDATION: 'INVALID_INPUT',
  TEMPLATE_INVALID: 'INVALID_INPUT',
  TEMPLATE_NOT_FOUND: 'NOT_FOUND',
  ASSET_NOT_FOUND: 'NOT_FOUND',
  THEME_NOT_FOUND: 'NOT_FOUND',
  IDEMPOTENCY_KEY_CONFLICT: 'CONFLICT',
};

const id = z.string().min(1).max(128);
const episodeIdArg = { episodeId: id };

function tool<S extends z.ZodType>(definition: {
  name: string;
  description: string;
  kind: 'read' | 'mutation';
  scopes: readonly Scope[];
  idempotency: string;
  sideEffects: string;
  confirmation?: 'NONE' | 'HUMAN_REQUIRED';
  input: S;
  data: z.ZodType;
  target: (args: z.infer<S>) => string;
  run: (ctx: Ctx, args: z.infer<S>) => Promise<Outcome>;
}): Tool {
  const confirmationPolicy = definition.confirmation ?? 'NONE';
  const auditPolicy =
    definition.kind === 'mutation'
      ? 'Chaque tentative est journalisée (réussie ou refusée) : acteur, credential, tool, scope, cible, résultat, horodatage, corrélation.'
      : 'Les lectures réussies ne sont pas journalisées ; les refus et dépassements de limite le sont.';
  const description = [
    definition.description,
    `Scopes requis : ${definition.scopes.join(', ')}.`,
    `Idempotence : ${definition.idempotency}`,
    `Effets de bord : ${definition.sideEffects}`,
    confirmationPolicy === 'HUMAN_REQUIRED'
      ? 'Confirmation humaine obligatoire avant exécution.'
      : 'Aucune confirmation humaine.',
  ].join(' ');
  return {
    name: definition.name,
    description,
    kind: definition.kind,
    requiredScopes: definition.scopes,
    idempotencyBehavior: definition.idempotency,
    sideEffects: definition.sideEffects,
    confirmationPolicy,
    auditPolicy,
    rateLimit: { cost: definition.kind === 'mutation' ? MUTATION_COST : READ_COST },
    input: definition.input,
    data: definition.data,
    prepare(raw) {
      const parsed = definition.input.safeParse(raw);
      if (!parsed.success) {
        return {
          ok: false,
          issues: parsed.error.issues.map(
            (i) => `${i.path.join('.') || '(racine)'} : ${i.message}`,
          ),
        };
      }
      const args = parsed.data;
      return {
        ok: true,
        target: definition.target(args),
        run: (ctx) => definition.run(ctx, args),
      };
    },
  };
}

async function loadEpisode(ctx: Ctx, episodeId: string): Promise<EpisodeWorkspace | null> {
  // Le podcast vient du credential, jamais de l'appel : un identifiant d'un autre podcast n'existe pas.
  return ctx.deps.episodes.get(ctx.credential.podcastId, episodeId);
}

const notFound = (what: string): Outcome => fail('NOT_FOUND', `${what} introuvable`);

const episodeSummary = z.looseObject({
  id: z.string(),
  podcastId: z.string(),
  title: z.string(),
  revision: z.number(),
});

const segmentPatch = z
  .strictObject({
    title: z.string().trim().min(1).max(120).optional(),
    objective: z.string().max(500).optional(),
    notes: z.string().max(20_000).optional(),
    questions: z.array(z.string().max(300)).max(50).optional(),
    targetDurationSec: z
      .number()
      .int()
      .min(10)
      .max(4 * 3600)
      .optional(),
    status: z.enum(['TODO', 'IN_PROGRESS', 'READY']).optional(),
  })
  .refine((patch) => Object.keys(patch).length > 0, 'au moins un champ à modifier');

const presentationArgs = { ...episodeIdArg, presentationId: id };
const presentationTarget = (a: { episodeId: string; presentationId: string }): string =>
  `episode:${a.episodeId}/presentation:${a.presentationId}`;

/** Document de la présentation d'un épisode du podcast du credential, ou une erreur NOT_FOUND. */
async function loadPresentation(
  ctx: Ctx,
  args: { episodeId: string; presentationId: string },
): Promise<
  | { ok: true; episode: EpisodeWorkspace; documentId: string; slotIndex: number }
  | { ok: false; outcome: Outcome }
> {
  const episode = await loadEpisode(ctx, args.episodeId);
  if (!episode) return { ok: false, outcome: notFound('Épisode') };
  const slotIndex = episode.presentations.findIndex((p) => p.id === args.presentationId);
  const slot = episode.presentations[slotIndex];
  if (!slot) return { ok: false, outcome: notFound('Présentation') };
  return { ok: true, episode, documentId: slot.documentId, slotIndex };
}

const htmlIssues = (html: string): string[] =>
  validatePresentationHtml(html).map((issue) => `${issue.code} : ${issue.message}`);

export function buildTools(): Tool[] {
  return [
    tool({
      name: 'create_episode_from_template',
      description:
        "Crée un épisode complet (séquences, scènes, assets, présentations, checklists) à partir d'une version de template du podcast du credential.",
      kind: 'mutation',
      scopes: ['episode:write'],
      idempotency:
        '`idempotencyKey` obligatoire (8 à 128 caractères) : rejouer la même demande retourne le même épisode sans en créer un second ; la même clé avec une autre demande est refusée (CONFLICT).',
      sideEffects: 'Crée un épisode en brouillon et ses espaces de travail vides.',
      input: z.strictObject({
        templateId: id,
        templateVersion: z.number().int().min(1).optional(),
        title: z.string().trim().min(1).max(200),
        date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'date AAAA-MM-JJ'),
        idempotencyKey: z.string().min(8).max(128),
      }),
      data: z.looseObject({ episodeId: z.string(), created: z.boolean(), revision: z.number() }),
      target: (a) => `template:${a.templateId}`,
      async run(ctx, args) {
        const catalogs = ctx.deps.catalogs(ctx.credential.podcastId);
        const result = await createEpisodeFromTemplate(
          {
            podcastId: ctx.credential.podcastId,
            actorId: ctx.credential.actorId,
            templateId: args.templateId,
            ...(args.templateVersion === undefined
              ? {}
              : { templateVersion: args.templateVersion }),
            title: args.title,
            date: args.date,
            idempotencyKey: args.idempotencyKey,
          },
          { ...catalogs, repository: ctx.deps.episodes, now: ctx.now },
        );
        if (!result.ok) {
          return fail(FACTORY_ERRORS[result.error.code], result.error.message, {
            details: result.error.details,
          });
        }
        return {
          ok: true,
          result: result.created ? 'OK' : 'UNCHANGED',
          data: {
            episodeId: result.episode.id,
            created: result.created,
            revision: result.episode.revision,
            segments: result.episode.segments.map((s) => ({ id: s.id, title: s.title })),
          },
        };
      },
    }),

    tool({
      name: 'get_episode',
      description: "Lit l'espace de travail d'un épisode du podcast du credential.",
      kind: 'read',
      scopes: ['episode:read'],
      idempotency: 'Lecture seule.',
      sideEffects: 'Aucun.',
      input: z.strictObject(episodeIdArg),
      data: z.looseObject({ episode: episodeSummary }),
      target: (a) => `episode:${a.episodeId}`,
      async run(ctx, args) {
        const episode = await loadEpisode(ctx, args.episodeId);
        return episode ? { ok: true, data: { episode } } : notFound('Épisode');
      },
    }),

    tool({
      name: 'list_segments',
      description: "Liste les séquences d'un épisode, dans l'ordre du conducteur.",
      kind: 'read',
      scopes: ['episode:read'],
      idempotency: 'Lecture seule.',
      sideEffects: 'Aucun.',
      input: z.strictObject(episodeIdArg),
      data: z.looseObject({
        revision: z.number(),
        segments: z.array(z.looseObject({ id: z.string() })),
      }),
      target: (a) => `episode:${a.episodeId}`,
      async run(ctx, args) {
        const episode = await loadEpisode(ctx, args.episodeId);
        if (!episode) return notFound('Épisode');
        const byId = new Map(episode.segments.map((s) => [s.id, s]));
        const ordered = episode.rundown.flatMap((r) => {
          const segment = byId.get(r.segmentId);
          return segment ? [segment] : [];
        });
        return { ok: true, data: { revision: episode.revision, segments: ordered } };
      },
    }),

    tool({
      name: 'update_segment',
      description:
        "Modifie des champs d'une séquence (titre, objectif, notes, questions, durée cible, statut). La sortie d'un modèle est validée contre ce schéma avant d'être appliquée.",
      kind: 'mutation',
      scopes: ['episode:write'],
      idempotency:
        'Concurrence optimiste : `expectedRevision` doit être la révision lue. Rejouer la même modification donne CONFLICT (la révision a avancé) ; relire puis réessayer.',
      sideEffects: "Modifie l'épisode et incrémente sa révision.",
      input: z.strictObject({
        ...episodeIdArg,
        segmentId: id,
        expectedRevision: z.number().int().min(1),
        patch: segmentPatch,
      }),
      data: z.looseObject({ revision: z.number(), segment: z.looseObject({ id: z.string() }) }),
      target: (a) => `episode:${a.episodeId}/segment:${a.segmentId}`,
      async run(ctx, args) {
        const episode = await loadEpisode(ctx, args.episodeId);
        if (!episode) return notFound('Épisode');
        const index = episode.segments.findIndex((s) => s.id === args.segmentId);
        const current = episode.segments[index];
        if (!current) return notFound('Séquence');
        if (episode.revision !== args.expectedRevision) {
          return fail('CONFLICT', "L'épisode a changé depuis votre lecture", {
            details: [`révision actuelle : ${String(episode.revision)}`],
          });
        }
        const updated = {
          ...current,
          ...Object.fromEntries(
            Object.entries(args.patch).filter(([, value]) => value !== undefined),
          ),
        };
        if (JSON.stringify(updated) === JSON.stringify(current))
          return {
            ok: true,
            result: 'UNCHANGED',
            data: { revision: episode.revision, segment: current },
          };
        const segments = episode.segments.map((s, i) => (i === index ? updated : s));
        const saved = await ctx.deps.episodes.replace({ ...episode, segments }, episode.revision);
        if (!saved) return fail('CONFLICT', "L'épisode a changé pendant la modification");
        return { ok: true, data: { revision: episode.revision + 1, segment: updated } };
      },
    }),

    tool({
      name: 'list_assets',
      description:
        'Liste les assets référencés par un épisode (version figée ou dernière version).',
      kind: 'read',
      scopes: ['asset:read'],
      idempotency: 'Lecture seule.',
      sideEffects: 'Aucun.',
      input: z.strictObject(episodeIdArg),
      data: z.looseObject({ assets: z.array(z.looseObject({ assetId: z.string() })) }),
      target: (a) => `episode:${a.episodeId}`,
      async run(ctx, args) {
        const episode = await loadEpisode(ctx, args.episodeId);
        return episode ? { ok: true, data: { assets: episode.assets } } : notFound('Épisode');
      },
    }),

    tool({
      name: 'get_presentation',
      description:
        "Lit une présentation (HTML, titre, empreinte du contenu, statut). L'empreinte sert de précondition à `update_presentation`.",
      kind: 'read',
      scopes: ['presentation:read'],
      idempotency: 'Lecture seule.',
      sideEffects: 'Aucun.',
      input: z.strictObject(presentationArgs),
      data: z.looseObject({ html: z.string(), contentHash: z.string(), title: z.string() }),
      target: presentationTarget,
      async run(ctx, args) {
        const found = await loadPresentation(ctx, args);
        if (!found.ok) return found.outcome;
        const doc = await ctx.deps.collab.document(found.documentId);
        const html = readHtml(doc);
        const slot = found.episode.presentations[found.slotIndex];
        return {
          ok: true,
          data: {
            html,
            title: readTitle(doc),
            contentHash: contentHash(html),
            status: slot?.status ?? 'DRAFT',
            publishedVersionId: slot?.publishedVersionId ?? null,
          },
        };
      },
    }),

    tool({
      name: 'create_presentation',
      description:
        "Écrit le contenu initial d'une présentation de l'épisode. Le HTML est validé (ressources externes, iframes, formulaires interdits) avant d'être enregistré, puis propagé en direct aux collaborateurs connectés.",
      kind: 'mutation',
      scopes: ['presentation:write'],
      idempotency:
        'Rejouer avec le même contenu ne change rien (UNCHANGED). Si la présentation a déjà un contenu différent : ALREADY_EXISTS, utiliser `update_presentation`.',
      sideEffects: 'Modifie le document collaboratif de la présentation.',
      input: z.strictObject({
        ...presentationArgs,
        title: z.string().trim().min(1).max(200),
        html: z.string().min(1),
      }),
      data: z.looseObject({ contentHash: z.string(), created: z.boolean() }),
      target: presentationTarget,
      async run(ctx, args) {
        const found = await loadPresentation(ctx, args);
        if (!found.ok) return found.outcome;
        const issues = htmlIssues(args.html);
        if (issues.length > 0)
          return fail('INVALID_INPUT', 'Présentation invalide', { details: issues });
        const doc = await ctx.deps.collab.document(found.documentId);
        const existing = readHtml(doc);
        if (existing.length > 0) {
          if (existing === args.html)
            return {
              ok: true,
              result: 'UNCHANGED',
              data: { contentHash: contentHash(existing), created: false },
            };
          return fail(
            'ALREADY_EXISTS',
            'La présentation a déjà un contenu : utiliser update_presentation',
          );
        }
        writePresentation(doc, { html: args.html, title: args.title }, `mcp:${ctx.credential.id}`);
        return { ok: true, data: { contentHash: contentHash(args.html), created: true } };
      },
    }),

    tool({
      name: 'update_presentation',
      description:
        "Remplace le HTML d'une présentation. `expectedHash` est l'empreinte lue avec `get_presentation` : si un humain a modifié le document entre-temps, la mise à jour est refusée (CONFLICT) au lieu d'écraser son travail.",
      kind: 'mutation',
      scopes: ['presentation:write'],
      idempotency:
        'Précondition `expectedHash`. Rejouer avec le même contenu ne change rien (UNCHANGED).',
      sideEffects: 'Modifie le document collaboratif ; propagé en direct aux collaborateurs.',
      input: z.strictObject({
        ...presentationArgs,
        expectedHash: z.string().length(64),
        html: z.string().min(1),
      }),
      data: z.looseObject({ contentHash: z.string() }),
      target: presentationTarget,
      async run(ctx, args) {
        const found = await loadPresentation(ctx, args);
        if (!found.ok) return found.outcome;
        const issues = htmlIssues(args.html);
        if (issues.length > 0)
          return fail('INVALID_INPUT', 'Présentation invalide', { details: issues });
        const doc = await ctx.deps.collab.document(found.documentId);
        const current = readHtml(doc);
        if (contentHash(current) !== args.expectedHash) {
          return fail('CONFLICT', 'La présentation a changé depuis votre lecture', {
            details: [`empreinte actuelle : ${contentHash(current)}`],
          });
        }
        if (current === args.html)
          return { ok: true, result: 'UNCHANGED', data: { contentHash: contentHash(current) } };
        writePresentation(doc, { html: args.html }, `mcp:${ctx.credential.id}`);
        return { ok: true, data: { contentHash: contentHash(args.html) } };
      },
    }),

    tool({
      name: 'publish_presentation_version',
      description:
        "Publie une version nommée de la présentation. Action publiante : le premier appel crée une demande de confirmation (CONFIRMATION_REQUIRED) qu'un humain doit approuver dans l'application ; le second appel, avec `confirmationId`, publie la version exacte qui a été approuvée.",
      kind: 'mutation',
      scopes: ['presentation:write'],
      confirmation: 'HUMAN_REQUIRED',
      idempotency:
        'Portée par `confirmationId` : à usage unique, valable pour cette demande et ce contenu exacts, expire. Rejouer le même appel après une réponse perdue retourne la même version (UNCHANGED).',
      sideEffects:
        'Enregistre un instantané nommé du document et marque la présentation comme publiée.',
      input: z.strictObject({
        ...presentationArgs,
        label: z.string().trim().min(1).max(120),
        confirmationId: id.optional(),
      }),
      data: z.looseObject({ versionId: z.string() }),
      target: presentationTarget,
      async run(ctx, args) {
        const found = await loadPresentation(ctx, args);
        if (!found.ok) return found.outcome;
        const doc = await ctx.deps.collab.document(found.documentId);
        const html = readHtml(doc);
        if (html.length === 0) return fail('INVALID_INPUT', 'La présentation est vide');
        const hash = contentHash(html);
        const request = {
          credentialId: ctx.credential.id,
          tool: 'publish_presentation_version',
          argsHash: sha256(JSON.stringify([args.episodeId, args.presentationId, args.label])),
        };
        const { confirmations } = ctx.deps;

        if (args.confirmationId === undefined) {
          const pending = confirmations.request(
            {
              ...request,
              podcastId: ctx.credential.podcastId,
              episodeId: args.episodeId,
              contentHash: hash,
            },
            ctx.now(),
          );
          return fail(
            'CONFIRMATION_REQUIRED',
            'Une approbation humaine est requise avant publication',
            {
              confirmationId: pending.id,
              details: [`contenu soumis : ${hash}`, `expire à : ${String(pending.expiresAtMs)}`],
            },
          );
        }

        const replayed = confirmations.replay(args.confirmationId, request);
        if (replayed !== null)
          return { ok: true, result: 'UNCHANGED', data: { versionId: replayed } };
        const consumed = confirmations.consume(
          args.confirmationId,
          { ...request, contentHash: hash },
          ctx.now(),
        );
        if (!consumed.ok) {
          const messages = {
            UNKNOWN: 'Confirmation inconnue',
            PENDING: "La confirmation n'a pas encore été approuvée par un humain",
            REJECTED: 'La confirmation a été refusée par un humain',
            EXPIRED: 'La confirmation a expiré',
            MISMATCH: 'La confirmation a été accordée pour une autre demande',
            USED: 'La confirmation a déjà servi',
            STALE: 'Le contenu a changé depuis l’approbation : redemander une confirmation',
          } as const;
          return fail(
            consumed.reason === 'UNKNOWN' ? 'NOT_FOUND' : 'CONFIRMATION_REQUIRED',
            messages[consumed.reason],
            consumed.reason === 'PENDING' ? { confirmationId: args.confirmationId } : {},
          );
        }

        try {
          const versionId = await ctx.deps.collab.createVersion(
            found.documentId,
            args.label,
            ctx.credential.actorId,
          );
          for (let attempt = 0; attempt < MAX_CAS_ATTEMPTS; attempt += 1) {
            const episode = await loadEpisode(ctx, args.episodeId);
            const slot = episode?.presentations.find((p) => p.id === args.presentationId);
            if (!episode || !slot) throw new Error('épisode disparu pendant la publication');
            const presentations = episode.presentations.map((p) =>
              p.id === args.presentationId
                ? { ...p, status: 'PUBLISHED' as const, publishedVersionId: versionId }
                : p,
            );
            if (await ctx.deps.episodes.replace({ ...episode, presentations }, episode.revision)) {
              confirmations.complete(args.confirmationId, versionId);
              return { ok: true, data: { versionId } };
            }
          }
          confirmations.release(args.confirmationId);
          return fail('CONFLICT', "L'épisode change trop vite, réessayer");
        } catch (error) {
          confirmations.release(args.confirmationId);
          throw error;
        }
      },
    }),
  ];
}

const requiresPodcastRole = (episode: EpisodeWorkspace, userId: string): boolean =>
  episode.permissions.some((p) => p.userId === userId && p.roles.includes('PRODUCER'));

export type ApprovalResult =
  | { ok: true; status: 'APPROVED' | 'REJECTED' }
  | { ok: false; reason: 'NOT_FOUND' | 'FORBIDDEN' | 'NOT_PENDING' };

/** Cœur du serveur, indépendant du transport : un même code sert MCP, les tests et une future API HTTP. */
export class Platform {
  readonly tools: readonly Tool[] = buildTools();
  private readonly now: () => number;
  private readonly deps: PlatformDeps;

  constructor(deps: PlatformDeps) {
    this.deps = deps;
    this.now = deps.now ?? Date.now;
  }

  describeTools(): ToolMetadata[] {
    return this.tools.map(
      ({
        name,
        description,
        kind,
        requiredScopes,
        idempotencyBehavior,
        sideEffects,
        confirmationPolicy,
        auditPolicy,
        rateLimit,
      }) => ({
        name,
        description,
        kind,
        requiredScopes,
        idempotencyBehavior,
        sideEffects,
        confirmationPolicy,
        auditPolicy,
        rateLimit,
      }),
    );
  }

  async execute(
    credentialId: string,
    toolName: string,
    rawArgs: unknown,
    correlationId: string = newCorrelationId(),
  ): Promise<Envelope> {
    const tool = this.tools.find((t) => t.name === toolName);
    const credential = this.deps.credentials.get(credentialId);
    const startedAt = this.now();
    let target = '(inconnue)';
    const record = (outcome: Outcome, detail: string): Envelope => {
      const result: AuditResult = outcome.ok
        ? (outcome.result ?? 'OK')
        : AUDIT_RESULT[outcome.error.code];
      // Les mutations sont toujours journalisées ; les lectures seulement si elles sont refusées.
      const mustAudit =
        tool?.kind !== 'read' || (!outcome.ok && result !== 'NOT_FOUND' && result !== 'INVALID');
      if (mustAudit) {
        this.deps.audit.record({
          actor: credential?.actorId ?? '(inconnu)',
          credentialId,
          podcastId: credential?.podcastId ?? null,
          tool: toolName,
          scope: tool?.requiredScopes[0] ?? null,
          target,
          result,
          detail,
          timestamp: startedAt,
          correlationId,
        });
      }
      return outcome.ok
        ? { ok: true, correlationId, result: outcome.result ?? 'OK', data: outcome.data }
        : { ok: false, correlationId, error: outcome.error };
    };

    if (!tool) return record(fail('UNKNOWN_TOOL', `Tool inconnu : ${toolName}`), '');
    if (
      !credential ||
      credential.revoked ||
      (credential.expiresAtMs !== null && startedAt >= credential.expiresAtMs)
    ) {
      return record(
        fail('UNAUTHENTICATED', 'Credential invalide, expiré ou révoqué'),
        'credential refusé',
      );
    }

    const retryAfterMs = this.deps.limiter.take(credential.id, tool.rateLimit.cost, startedAt);
    if (retryAfterMs !== null) {
      return record(fail('RATE_LIMITED', 'Trop de requêtes', { retryAfterMs }), 'limite dépassée');
    }

    const missing = tool.requiredScopes.filter((scope) => !credential.scopes.includes(scope));
    if (missing.length > 0) {
      return record(
        fail('FORBIDDEN', 'Scope insuffisant pour ce tool', { requiredScopes: [...missing] }),
        `scopes manquants : ${missing.join(', ')}`,
      );
    }

    const prepared = tool.prepare(rawArgs);
    if (!prepared.ok) {
      return record(
        fail('INVALID_INPUT', 'Arguments invalides', { details: prepared.issues }),
        'arguments invalides',
      );
    }
    target = prepared.target;

    try {
      const outcome = await prepared.run({
        credential,
        correlationId,
        deps: this.deps,
        now: this.now,
      });
      return record(outcome, outcome.ok ? '' : outcome.error.message);
    } catch (error) {
      const detail = error instanceof Error ? error.message : String(error);
      return record(fail('INTERNAL', `Erreur interne (corrélation ${correlationId})`), detail);
    }
  }

  /**
   * Chemin humain : l'approbation d'une confirmation passe par l'application, jamais par un tool MCP.
   * L'approbateur doit avoir le rôle PRODUCER sur l'épisode concerné.
   */
  async decideConfirmation(
    confirmationId: string,
    approverId: string,
    approve: boolean,
    correlationId: string = newCorrelationId(),
  ): Promise<ApprovalResult> {
    const confirmation = this.deps.confirmations.get(confirmationId);
    const base = {
      actor: approverId,
      credentialId: null,
      podcastId: confirmation?.podcastId ?? null,
      tool: 'decide_confirmation',
      scope: null,
      target: confirmation ? `episode:${confirmation.episodeId}` : `confirmation:${confirmationId}`,
      timestamp: this.now(),
      correlationId,
    };
    const finish = (
      result: AuditResult,
      detail: string,
      outcome: ApprovalResult,
    ): ApprovalResult => {
      this.deps.audit.record({ ...base, result, detail });
      return outcome;
    };
    if (!confirmation)
      return finish('NOT_FOUND', 'confirmation inconnue', { ok: false, reason: 'NOT_FOUND' });
    const episode = await this.deps.episodes.get(confirmation.podcastId, confirmation.episodeId);
    if (!episode || !requiresPodcastRole(episode, approverId))
      return finish('DENIED', "l'approbateur n'a pas le rôle PRODUCER", {
        ok: false,
        reason: 'FORBIDDEN',
      });
    const decided = this.deps.confirmations.decide(confirmationId, approverId, approve, this.now());
    if (!decided)
      return finish('CONFLICT', 'confirmation non en attente', {
        ok: false,
        reason: 'NOT_PENDING',
      });
    return finish('OK', approve ? 'approuvée' : 'refusée', {
      ok: true,
      status: approve ? 'APPROVED' : 'REJECTED',
    });
  }
}

export { PRESENTATION_SCHEMA };
