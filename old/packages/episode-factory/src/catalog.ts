import type { AssetCatalog, TemplateCatalog, ThemeCatalog } from './model.ts';

/** Template par défaut : quatre séquences (INTRO, SÉQUENCE A, SÉQUENCE B, CONCLUSION). */
export function standardTemplate(version = 1): unknown {
  return {
    id: 'standard',
    version,
    name: 'Épisode standard',
    sequences: [
      {
        key: 'intro',
        title: 'INTRO',
        objective: "Présenter l'épisode et les invités",
        targetDurationSec: 180,
        jingle: 'jingle-intro',
      },
      {
        key: 'sequence-a',
        title: 'SÉQUENCE A',
        objective: 'Premier thème',
        targetDurationSec: 900,
      },
      { key: 'sequence-b', title: 'SÉQUENCE B', objective: 'Second thème', targetDurationSec: 900 },
      {
        key: 'conclusion',
        title: 'CONCLUSION',
        objective: 'Résumer et appeler à agir',
        targetDurationSec: 240,
        cta: "S'abonner et partager",
        jingle: 'jingle-outro',
      },
    ],
    scenes: [
      { key: 'groupe', name: 'Groupe', layout: 'GROUP' },
      { key: 'focus', name: 'Plan serré', layout: 'SPEAKER_FOCUS' },
      { key: 'duo', name: 'Duo', layout: 'DUO' },
      { key: 'presentation', name: 'Présentation', layout: 'PRESENTATION' },
      { key: 'ouverture', name: 'Ouverture', layout: 'INTRO', sequences: ['intro'] },
      { key: 'fermeture', name: 'Fermeture', layout: 'OUTRO', sequences: ['conclusion'] },
      { key: 'nom', name: 'Nom des intervenants', layout: 'LOWER_THIRD' },
    ],
    assets: [
      { category: 'BRAND', assetId: 'logo-principal', policy: 'FREEZE' },
      { category: 'INTROS', assetId: 'intro-video', policy: 'FREEZE' },
      { category: 'OUTROS', assetId: 'outro-video', policy: 'FREEZE' },
      { category: 'JINGLES', assetId: 'jingle-intro', policy: 'FREEZE' },
      { category: 'LOWER_THIRDS', assetId: 'bandeau-nom', policy: 'REFERENCE' },
    ],
    checklists: [
      {
        key: 'avant-live',
        title: 'Avant le live',
        items: ['Micros testés', 'Caméras cadrées', 'Présentations validées', 'Invités connectés'],
      },
      {
        key: 'apres-live',
        title: 'Après le live',
        items: ['Enregistrements vérifiés', 'Transcription lancée', 'Clips proposés'],
      },
    ],
    clipTemplates: ['clip-vertical', 'clip-carre'],
    exportPresets: [
      { key: 'youtube-1080p', presetVersion: 1 },
      { key: 'vertical-9x16', presetVersion: 1 },
    ],
    brandThemeId: 'marque',
    broadcastThemeId: 'diffusion',
  };
}

/**
 * Catalogue en mémoire des templates, assets et thèmes, avec leurs versions.
 * Un nouveau `publishTemplate` ajoute une version : les épisodes existants gardent la leur.
 */
export class InMemoryCatalog implements TemplateCatalog, AssetCatalog, ThemeCatalog {
  private readonly templates = new Map<string, Map<number, unknown>>();
  private readonly assets = new Map<string, number>();
  private readonly themes = new Map<string, number>();

  publishTemplate(templateId: string, version: number, template: unknown): void {
    const versions = this.templates.get(templateId) ?? new Map<number, unknown>();
    versions.set(version, template);
    this.templates.set(templateId, versions);
  }

  publishAsset(assetId: string, version: number): void {
    this.assets.set(assetId, version);
  }

  publishTheme(themeId: string, version: number): void {
    this.themes.set(themeId, version);
  }

  getTemplate(templateId: string, version?: number): unknown {
    const versions = this.templates.get(templateId);
    if (!versions) return undefined;
    if (version !== undefined) return versions.get(version);
    const latest = Math.max(...versions.keys());
    return versions.get(latest);
  }

  getAsset(assetId: string): { id: string; version: number } | null {
    const version = this.assets.get(assetId);
    return version === undefined ? null : { id: assetId, version };
  }

  getTheme(themeId: string): { id: string; version: number } | null {
    const version = this.themes.get(themeId);
    return version === undefined ? null : { id: themeId, version };
  }

  /** Catalogue prêt à l'emploi pour les tests et les démonstrations. */
  static withStandardContent(): InMemoryCatalog {
    const catalog = new InMemoryCatalog();
    catalog.publishTemplate('standard', 1, standardTemplate(1));
    for (const id of [
      'logo-principal',
      'intro-video',
      'outro-video',
      'jingle-intro',
      'bandeau-nom',
    ]) {
      catalog.publishAsset(id, 1);
    }
    catalog.publishTheme('marque', 1);
    catalog.publishTheme('diffusion', 1);
    return catalog;
  }
}
