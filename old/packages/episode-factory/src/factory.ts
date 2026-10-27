import { createHash, randomUUID } from 'node:crypto';
import type {
  AssetCatalog,
  AssetReference,
  EpisodeWorkspace,
  PresentationSlot,
  SceneInstance,
  Segment,
  TemplateCatalog,
  ThemeCatalog,
} from './model.ts';
import type { EpisodeRepository } from './repository.ts';
import {
  createEpisodeInputSchema,
  episodeTemplateSchema,
  type CreateEpisodeInput,
} from './schemas.ts';

export type FactoryErrorCode =
  | 'VALIDATION'
  | 'TEMPLATE_NOT_FOUND'
  | 'TEMPLATE_INVALID'
  | 'ASSET_NOT_FOUND'
  | 'THEME_NOT_FOUND'
  | 'IDEMPOTENCY_KEY_CONFLICT';

export interface FactoryError {
  code: FactoryErrorCode;
  message: string;
  /** Un détail par problème trouvé : on les rapporte tous, pas seulement le premier. */
  details: string[];
}

export type FactoryResult =
  { ok: true; episode: EpisodeWorkspace; created: boolean } | { ok: false; error: FactoryError };

export interface FactoryDeps {
  templates: TemplateCatalog;
  assets: AssetCatalog;
  themes: ThemeCatalog;
  repository: EpisodeRepository;
  now?: () => number;
  newId?: () => string;
}

const fail = (code: FactoryErrorCode, message: string, details: string[] = []): FactoryResult => ({
  ok: false,
  error: { code, message, details },
});

/** Empreinte de la demande : même clé d'idempotence avec une autre demande est un conflit. */
export function fingerprint(input: CreateEpisodeInput): string {
  const request = [
    input.podcastId,
    input.templateId,
    input.templateVersion ?? null,
    input.title,
    input.date,
    input.actorId,
  ];
  return createHash('sha256').update(JSON.stringify(request)).digest('hex');
}

/**
 * Crée l'espace de travail complet d'un épisode à partir d'une version de template.
 * Tout ou rien : la demande, le template, les assets et les thèmes sont validés avant d'écrire,
 * et l'écriture est une seule opération atomique. Aucun épisode partiel n'est jamais enregistré.
 */
export async function createEpisodeFromTemplate(
  rawInput: unknown,
  deps: FactoryDeps,
): Promise<FactoryResult> {
  const parsedInput = createEpisodeInputSchema.safeParse(rawInput);
  if (!parsedInput.success) {
    return fail(
      'VALIDATION',
      'Demande invalide',
      parsedInput.error.issues.map((i) => `${i.path.join('.')} : ${i.message}`),
    );
  }
  const input = parsedInput.data;

  const rawTemplate = deps.templates.getTemplate(input.templateId, input.templateVersion);
  if (rawTemplate === undefined || rawTemplate === null) {
    return fail(
      'TEMPLATE_NOT_FOUND',
      `Template introuvable : ${input.templateId}${input.templateVersion ? ` v${String(input.templateVersion)}` : ''}`,
    );
  }
  const parsedTemplate = episodeTemplateSchema.safeParse(rawTemplate);
  if (!parsedTemplate.success) {
    return fail(
      'TEMPLATE_INVALID',
      'Le template est invalide',
      parsedTemplate.error.issues.map((i) => `${i.path.join('.')} : ${i.message}`),
    );
  }
  const template = parsedTemplate.data;

  // Cohérence interne : les scènes ne désignent que des séquences qui existent.
  const sequenceKeys = new Set(template.sequences.map((s) => s.key));
  const unknownSequences = template.scenes.flatMap((scene) =>
    scene.sequences
      .filter((key) => !sequenceKeys.has(key))
      .map((key) => `la scène ${scene.key} désigne la séquence inconnue ${key}`),
  );
  if (unknownSequences.length > 0)
    return fail('TEMPLATE_INVALID', 'Le template est incohérent', unknownSequences);

  const brandTheme = deps.themes.getTheme(template.brandThemeId);
  const broadcastTheme = deps.themes.getTheme(template.broadcastThemeId);
  const themeProblems = [
    ...(brandTheme ? [] : [`thème de marque introuvable : ${template.brandThemeId}`]),
    ...(broadcastTheme ? [] : [`thème de diffusion introuvable : ${template.broadcastThemeId}`]),
  ];
  if (!brandTheme || !broadcastTheme)
    return fail('THEME_NOT_FOUND', 'Thème introuvable', themeProblems);

  const missingAssets: string[] = [];
  const assets: AssetReference[] = [];
  for (const ref of template.assets) {
    const asset = deps.assets.getAsset(ref.assetId);
    if (!asset) {
      missingAssets.push(`asset introuvable ou non publié : ${ref.assetId}`);
      continue;
    }
    assets.push({
      assetId: ref.assetId,
      category: ref.category,
      frozenVersion: ref.policy === 'FREEZE' ? asset.version : null,
      mode: ref.policy === 'FREEZE' ? 'FROZEN' : 'REFERENCE',
    });
  }
  if (missingAssets.length > 0)
    return fail('ASSET_NOT_FOUND', 'Assets introuvables', missingAssets);

  const newId = deps.newId ?? randomUUID;
  const scenes: SceneInstance[] = template.scenes.map((scene) => ({
    id: newId(),
    key: scene.key,
    name: scene.name,
    layout: scene.layout,
    templateVersion: template.version,
  }));
  const segments: Segment[] = template.sequences.map((sequence) => ({
    id: newId(),
    key: sequence.key,
    title: sequence.title,
    objective: sequence.objective,
    targetDurationSec: sequence.targetDurationSec,
    questions: [...sequence.questions],
    notes: '',
    speakers: [],
    sceneIds: template.scenes
      .map((scene, index) => ({ scene, id: scenes[index]?.id }))
      .filter(({ scene }) => scene.sequences.length === 0 || scene.sequences.includes(sequence.key))
      .flatMap(({ id }) => (id ? [id] : [])),
    assetIds: assets.map((a) => a.assetId),
    presentationId: null,
    transition: null,
    jingle: sequence.jingle,
    cta: sequence.cta,
    status: 'TODO',
  }));
  const episodeId = newId();
  const presentations: PresentationSlot[] = segments.map((segment) => {
    const id = newId();
    segment.presentationId = id;
    return {
      id,
      segmentKey: segment.key,
      status: 'DRAFT',
      publishedVersionId: null,
      documentId: `presentation:${episodeId}:${id}`,
    };
  });

  const episode: EpisodeWorkspace = {
    id: episodeId,
    podcastId: input.podcastId,
    title: input.title,
    date: input.date,
    status: 'DRAFT',
    revision: 1,
    createdAtMs: (deps.now ?? Date.now)(),
    createdBy: input.actorId,
    origin: {
      templateId: template.id,
      templateVersion: template.version,
      brandThemeId: brandTheme.id,
      brandThemeVersion: brandTheme.version,
      broadcastThemeId: broadcastTheme.id,
      broadcastThemeVersion: broadcastTheme.version,
      exportPresetVersions: Object.fromEntries(
        template.exportPresets.map((p) => [p.key, p.presetVersion]),
      ),
      idempotencyKey: input.idempotencyKey,
    },
    brief: { summary: '', objectives: [] },
    rundown: segments.map((segment, order) => ({ order, segmentId: segment.id })),
    segments,
    scenes,
    assets,
    presentations,
    checklists: template.checklists.map((c) => ({
      key: c.key,
      title: c.title,
      items: c.items.map((text) => ({ text, done: false })),
    })),
    recording: { status: 'EMPTY', sessionIds: [] },
    clips: { status: 'EMPTY', templates: [...template.clipTemplates], clipIds: [] },
    exports: {
      status: 'EMPTY',
      presets: template.exportPresets.map((p) => ({ ...p })),
      exportIds: [],
    },
    permissions: [{ userId: input.actorId, roles: ['PRODUCER'] }],
  };

  const written = await deps.repository.createIfAbsent(
    input.podcastId,
    input.idempotencyKey,
    fingerprint(input),
    episode,
  );
  if (written.kind === 'KEY_CONFLICT') {
    return fail(
      'IDEMPOTENCY_KEY_CONFLICT',
      'Cette clé d’idempotence a déjà servi pour une autre demande',
    );
  }
  return { ok: true, episode: written.episode, created: written.kind === 'CREATED' };
}
