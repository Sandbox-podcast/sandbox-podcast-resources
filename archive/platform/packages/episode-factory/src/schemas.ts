import { z } from 'zod';

export const ASSET_CATEGORIES = [
  'BRAND',
  'BACKGROUNDS',
  'OVERLAYS',
  'LOWER_THIRDS',
  'TRANSITIONS',
  'INTROS',
  'OUTROS',
  'JINGLES',
  'MUSIC',
  'ICONS',
  'ILLUSTRATIONS',
  'PRESENTATIONS',
  'THUMBNAILS',
  'CLIP_TEMPLATES',
  'SUBTITLE_STYLES',
] as const;

export const SCENE_LAYOUTS = [
  'GROUP',
  'SPEAKER_FOCUS',
  'DUO',
  'PRESENTATION',
  'INTRO',
  'OUTRO',
  'LOWER_THIRD',
] as const;

const key = z.string().regex(/^[a-z][a-z0-9-]{0,39}$/, 'clé en minuscules, chiffres et tirets');

export const sequenceTemplateSchema = z.strictObject({
  key,
  title: z.string().min(1).max(120),
  objective: z.string().max(500).default(''),
  targetDurationSec: z
    .number()
    .int()
    .min(10)
    .max(4 * 3600),
  questions: z.array(z.string().max(300)).default([]),
  jingle: z.string().nullable().default(null),
  cta: z.string().max(300).nullable().default(null),
});

export const sceneTemplateSchema = z.strictObject({
  key,
  name: z.string().min(1).max(120),
  layout: z.enum(SCENE_LAYOUTS),
  /** Séquences où la scène sert (clés de séquence). Vide : disponible partout. */
  sequences: z.array(key).default([]),
});

/**
 * Politique d'un asset récurrent dans un épisode :
 * - `FREEZE` : la version actuelle est figée dans l'épisode, une évolution ultérieure ne le change pas ;
 * - `REFERENCE` : l'épisode suit la dernière version.
 */
export const assetRefTemplateSchema = z.strictObject({
  category: z.enum(ASSET_CATEGORIES),
  assetId: z.string().min(1),
  policy: z.enum(['FREEZE', 'REFERENCE']).default('FREEZE'),
});

export const episodeTemplateSchema = z.strictObject({
  id: key,
  version: z.number().int().min(1),
  name: z.string().min(1).max(120),
  sequences: z.array(sequenceTemplateSchema).min(1).max(20),
  scenes: z.array(sceneTemplateSchema).min(1).max(60),
  assets: z.array(assetRefTemplateSchema).max(200).default([]),
  checklists: z
    .array(
      z.strictObject({ key, title: z.string().min(1), items: z.array(z.string().min(1)).min(1) }),
    )
    .default([]),
  clipTemplates: z.array(z.string().min(1)).default([]),
  exportPresets: z
    .array(z.strictObject({ key, presetVersion: z.number().int().min(1) }))
    .default([]),
  brandThemeId: z.string().min(1),
  broadcastThemeId: z.string().min(1),
});

export type EpisodeTemplate = z.infer<typeof episodeTemplateSchema>;
export type AssetCategory = (typeof ASSET_CATEGORIES)[number];

export const createEpisodeInputSchema = z.strictObject({
  podcastId: z.string().min(1),
  templateId: z.string().min(1),
  templateVersion: z.number().int().min(1).optional(),
  title: z.string().trim().min(1).max(200),
  /** Date d'enregistrement prévue, AAAA-MM-JJ. */
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'date AAAA-MM-JJ'),
  idempotencyKey: z.string().min(8).max(128),
  actorId: z.string().min(1),
});

export type CreateEpisodeInput = z.infer<typeof createEpisodeInputSchema>;
