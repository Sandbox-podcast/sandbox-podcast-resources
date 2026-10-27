import type { AssetCategory, EpisodeTemplate } from './schemas.ts';

export interface AssetReference {
  assetId: string;
  category: AssetCategory;
  /** Version figée à la création, ou `null` si l'épisode suit la dernière version. */
  frozenVersion: number | null;
  mode: 'FROZEN' | 'REFERENCE';
}

export interface Segment {
  id: string;
  key: string;
  title: string;
  objective: string;
  targetDurationSec: number;
  questions: string[];
  notes: string;
  speakers: string[];
  sceneIds: string[];
  assetIds: string[];
  presentationId: string | null;
  transition: string | null;
  jingle: string | null;
  cta: string | null;
  status: 'TODO' | 'IN_PROGRESS' | 'READY';
}

export interface SceneInstance {
  id: string;
  key: string;
  name: string;
  layout: string;
  /** Version du template de scène d'origine : celle du template d'épisode. */
  templateVersion: number;
}

export interface PresentationSlot {
  id: string;
  segmentKey: string;
  status: 'DRAFT' | 'PUBLISHED';
  /** Version publiée (identifiant de version du document), `null` tant que rien n'est publié. */
  publishedVersionId: string | null;
  /** Document collaboratif associé (voir @podcast/collab), créé à la première édition. */
  documentId: string;
}

/** Traçabilité : tout ce qui a servi à créer l'épisode (AC-FACTORY-004). */
export interface EpisodeOrigin {
  templateId: string;
  templateVersion: number;
  brandThemeId: string;
  brandThemeVersion: number;
  broadcastThemeId: string;
  broadcastThemeVersion: number;
  exportPresetVersions: Readonly<Record<string, number>>;
  idempotencyKey: string;
}

export interface EpisodeWorkspace {
  id: string;
  podcastId: string;
  title: string;
  date: string;
  status: 'DRAFT';
  /** Augmente à chaque modification : concurrence optimiste. */
  revision: number;
  createdAtMs: number;
  createdBy: string;
  origin: EpisodeOrigin;
  brief: { summary: string; objectives: string[] };
  rundown: { order: number; segmentId: string }[];
  segments: Segment[];
  scenes: SceneInstance[];
  assets: AssetReference[];
  presentations: PresentationSlot[];
  checklists: { key: string; title: string; items: { text: string; done: boolean }[] }[];
  /** Espaces de travail vides, remplis plus tard par l'enregistrement, les clips et l'export. */
  recording: { status: 'EMPTY'; sessionIds: string[] };
  clips: { status: 'EMPTY'; templates: string[]; clipIds: string[] };
  exports: {
    status: 'EMPTY';
    presets: { key: string; presetVersion: number }[];
    exportIds: string[];
  };
  /** Droits initiaux : qui peut faire quoi sur cet épisode. */
  permissions: { userId: string; roles: string[] }[];
}

/** Un template ainsi que sa version, tels que les catalogues les fournissent. */
export interface TemplateCatalog {
  /** Sans version : la dernière. */
  getTemplate(templateId: string, version?: number): unknown;
}

export interface AssetCatalog {
  /** `null` si l'asset n'existe pas ou n'est pas publié. */
  getAsset(assetId: string): { id: string; version: number } | null;
}

export interface ThemeCatalog {
  getTheme(themeId: string): { id: string; version: number } | null;
}

export type { EpisodeTemplate };
