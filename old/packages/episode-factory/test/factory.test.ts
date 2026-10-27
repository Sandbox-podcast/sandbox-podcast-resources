import { describe, expect, it } from 'vitest';
import {
  InMemoryCatalog,
  InMemoryEpisodeRepository,
  createEpisodeFromTemplate,
  standardTemplate,
  type FactoryDeps,
  type FactoryResult,
} from '../src/index.ts';

function setup(overrides: Partial<FactoryDeps> = {}) {
  const catalog = InMemoryCatalog.withStandardContent();
  const repository = new InMemoryEpisodeRepository();
  let n = 0;
  const deps: FactoryDeps = {
    templates: catalog,
    assets: catalog,
    themes: catalog,
    repository,
    now: () => 1_700_000_000_000,
    newId: () => `id-${String((n += 1))}`,
    ...overrides,
  };
  return { catalog, repository, deps };
}

const request = (extra: Record<string, unknown> = {}) => ({
  podcastId: 'podcast-a',
  templateId: 'standard',
  title: 'Les agents IA',
  date: '2026-10-05',
  idempotencyKey: 'cle-demande-0001',
  actorId: 'lou',
  ...extra,
});

const episodeOf = (result: FactoryResult) => {
  if (!result.ok) throw new Error(`création refusée : ${result.error.message}`);
  return result.episode;
};

describe('création complète (AC-FACTORY-001, AC-RUNDOWN-001, AC-RUNDOWN-002)', () => {
  it('génère toute la structure d’un épisode', async () => {
    const { deps } = setup();
    const episode = episodeOf(await createEpisodeFromTemplate(request(), deps));
    expect(episode.status).toBe('DRAFT');
    expect(episode.brief).toEqual({ summary: '', objectives: [] });
    expect(episode.segments.map((s) => s.title)).toEqual([
      'INTRO',
      'SÉQUENCE A',
      'SÉQUENCE B',
      'CONCLUSION',
    ]);
    expect(episode.rundown.map((r) => r.order)).toEqual([0, 1, 2, 3]);
    expect(episode.rundown.map((r) => r.segmentId)).toEqual(episode.segments.map((s) => s.id));
    expect(episode.scenes).toHaveLength(7);
    expect(episode.assets).toHaveLength(5);
    expect(episode.presentations).toHaveLength(4);
    expect(episode.recording).toEqual({ status: 'EMPTY', sessionIds: [] });
    expect(episode.clips).toEqual({
      status: 'EMPTY',
      templates: ['clip-vertical', 'clip-carre'],
      clipIds: [],
    });
    expect(episode.exports.presets.map((p) => p.key)).toEqual(['youtube-1080p', 'vertical-9x16']);
    expect(episode.checklists.map((c) => c.key)).toEqual(['avant-live', 'apres-live']);
    expect(episode.permissions).toEqual([{ userId: 'lou', roles: ['PRODUCER'] }]);
  });

  it('chaque séquence référence ses notes, questions, scènes, assets et présentation', async () => {
    const { deps } = setup();
    const episode = episodeOf(await createEpisodeFromTemplate(request(), deps));
    for (const segment of episode.segments) {
      expect(segment.notes).toBe('');
      expect(segment.questions).toEqual([]);
      expect(segment.sceneIds.length).toBeGreaterThan(0);
      expect(segment.assetIds).toHaveLength(5);
      expect(segment.presentationId).not.toBeNull();
      expect(episode.presentations.some((p) => p.id === segment.presentationId)).toBe(true);
    }
    const intro = episode.segments[0];
    const ouverture = episode.scenes.find((s) => s.key === 'ouverture');
    expect(intro?.sceneIds).toContain(ouverture?.id);
    expect(episode.segments[1]?.sceneIds).not.toContain(ouverture?.id);
    expect(intro?.jingle).toBe('jingle-intro');
    expect(episode.segments[3]?.cta).toBe("S'abonner et partager");
  });
});

describe('versions figées (AC-FACTORY-002, AC-FACTORY-003, AC-ASSET-005)', () => {
  it('fige la version des assets à figer et suit la dernière pour les autres', async () => {
    const { catalog, deps } = setup();
    catalog.publishAsset('logo-principal', 4);
    catalog.publishAsset('bandeau-nom', 7);
    const episode = episodeOf(await createEpisodeFromTemplate(request(), deps));
    const logo = episode.assets.find((a) => a.assetId === 'logo-principal');
    const bandeau = episode.assets.find((a) => a.assetId === 'bandeau-nom');
    expect(logo).toEqual({
      assetId: 'logo-principal',
      category: 'BRAND',
      frozenVersion: 4,
      mode: 'FROZEN',
    });
    expect(bandeau).toEqual({
      assetId: 'bandeau-nom',
      category: 'LOWER_THIRDS',
      frozenVersion: null,
      mode: 'REFERENCE',
    });
  });

  it('une nouvelle version du template ne change pas un épisode existant', async () => {
    const { catalog, deps, repository } = setup();
    const first = episodeOf(await createEpisodeFromTemplate(request(), deps));
    const snapshot = JSON.stringify(first);

    const v2 = standardTemplate(2) as { sequences: unknown[]; name: string };
    v2.name = 'Épisode standard v2';
    v2.sequences = [...v2.sequences, { key: 'bonus', title: 'BONUS', targetDurationSec: 300 }];
    catalog.publishTemplate('standard', 2, v2);
    catalog.publishAsset('logo-principal', 9);

    expect(JSON.stringify(await repository.get('podcast-a', first.id))).toBe(snapshot);
    const second = episodeOf(
      await createEpisodeFromTemplate(request({ idempotencyKey: 'cle-demande-0002' }), deps),
    );
    expect(second.origin.templateVersion).toBe(2);
    expect(second.segments).toHaveLength(5);
    expect(first.origin.templateVersion).toBe(1);
    expect(first.segments).toHaveLength(4);
  });

  it('permet de demander explicitement une ancienne version', async () => {
    const { catalog, deps } = setup();
    catalog.publishTemplate('standard', 2, { ...(standardTemplate(2) as object), name: 'v2' });
    const episode = episodeOf(
      await createEpisodeFromTemplate(request({ templateVersion: 1 }), deps),
    );
    expect(episode.origin.templateVersion).toBe(1);
  });
});

describe('traçabilité (AC-FACTORY-004)', () => {
  it('conserve la version du template, des thèmes et des presets', async () => {
    const { catalog, deps } = setup();
    catalog.publishTheme('marque', 3);
    catalog.publishTheme('diffusion', 2);
    const episode = episodeOf(await createEpisodeFromTemplate(request(), deps));
    expect(episode.origin).toEqual({
      templateId: 'standard',
      templateVersion: 1,
      brandThemeId: 'marque',
      brandThemeVersion: 3,
      broadcastThemeId: 'diffusion',
      broadcastThemeVersion: 2,
      exportPresetVersions: { 'youtube-1080p': 1, 'vertical-9x16': 1 },
      idempotencyKey: 'cle-demande-0001',
    });
    expect(episode.createdBy).toBe('lou');
  });
});

describe('idempotence (AC-FACTORY-005)', () => {
  it('la même demande avec la même clé ne crée pas deux épisodes', async () => {
    const { deps, repository } = setup();
    const first = await createEpisodeFromTemplate(request(), deps);
    const second = await createEpisodeFromTemplate(request(), deps);
    expect(first.ok && first.created).toBe(true);
    expect(second.ok && second.created).toBe(false);
    expect(episodeOf(second).id).toBe(episodeOf(first).id);
    expect(await repository.list('podcast-a')).toHaveLength(1);
  });

  it('refuse une autre demande avec la même clé', async () => {
    const { deps } = setup();
    await createEpisodeFromTemplate(request(), deps);
    const conflict = await createEpisodeFromTemplate(request({ title: 'Un autre titre' }), deps);
    expect(conflict.ok).toBe(false);
    expect(!conflict.ok && conflict.error.code).toBe('IDEMPOTENCY_KEY_CONFLICT');
  });

  it('deux demandes concurrentes avec la même clé ne créent qu’un épisode', async () => {
    const { deps, repository } = setup();
    const results = await Promise.all([
      createEpisodeFromTemplate(request(), deps),
      createEpisodeFromTemplate(request(), deps),
    ]);
    expect(results.every((r) => r.ok)).toBe(true);
    expect(await repository.list('podcast-a')).toHaveLength(1);
  });

  it('la même clé dans deux podcasts donne deux épisodes distincts', async () => {
    const { deps, repository } = setup();
    await createEpisodeFromTemplate(request(), deps);
    await createEpisodeFromTemplate(request({ podcastId: 'podcast-b' }), deps);
    expect(await repository.list('podcast-a')).toHaveLength(1);
    expect(await repository.list('podcast-b')).toHaveLength(1);
  });
});

describe('validation, tout ou rien (AC-FACTORY-006)', () => {
  it.each([
    ['titre vide', { title: '  ' }],
    ['date mal formée', { date: '05/10/2026' }],
    ['clé d’idempotence trop courte', { idempotencyKey: 'abc' }],
    ['champ inconnu', { surprise: true }],
    ['podcast absent', { podcastId: '' }],
  ])('rejette une demande invalide : %s', async (_label, extra) => {
    const { deps, repository } = setup();
    const result = await createEpisodeFromTemplate(request(extra), deps);
    expect(!result.ok && result.error.code).toBe('VALIDATION');
    expect(await repository.list('podcast-a')).toHaveLength(0);
  });

  it('rejette un template introuvable', async () => {
    const { deps } = setup();
    const result = await createEpisodeFromTemplate(request({ templateId: 'inconnu' }), deps);
    expect(!result.ok && result.error.code).toBe('TEMPLATE_NOT_FOUND');
  });

  it('rejette un template invalide sans créer d’épisode partiel', async () => {
    const { catalog, deps, repository } = setup();
    catalog.publishTemplate('casse', 1, {
      ...(standardTemplate(1) as object),
      id: 'casse',
      sequences: [],
    });
    const result = await createEpisodeFromTemplate(request({ templateId: 'casse' }), deps);
    expect(!result.ok && result.error.code).toBe('TEMPLATE_INVALID');
    expect(!result.ok && result.error.details.length).toBeGreaterThan(0);
    expect(await repository.list('podcast-a')).toHaveLength(0);
  });

  it('rejette un template dont une scène désigne une séquence inconnue', async () => {
    const { catalog, deps } = setup();
    const template = standardTemplate(1) as {
      id: string;
      scenes: { key: string; name: string; layout: string; sequences?: string[] }[];
    };
    template.id = 'incoherent';
    template.scenes.push({ key: 'x', name: 'x', layout: 'GROUP', sequences: ['fantome'] });
    catalog.publishTemplate('incoherent', 1, template);
    const result = await createEpisodeFromTemplate(request({ templateId: 'incoherent' }), deps);
    expect(!result.ok && result.error.code).toBe('TEMPLATE_INVALID');
    expect(!result.ok && result.error.details).toEqual([
      'la scène x désigne la séquence inconnue fantome',
    ]);
  });

  it('rapporte tous les assets manquants, et n’écrit rien', async () => {
    const empty = new InMemoryCatalog();
    empty.publishTemplate('standard', 1, standardTemplate(1));
    empty.publishTheme('marque', 1);
    empty.publishTheme('diffusion', 1);
    empty.publishAsset('logo-principal', 1);
    const { repository } = setup();
    const result = await createEpisodeFromTemplate(request(), {
      templates: empty,
      assets: empty,
      themes: empty,
      repository,
    });
    expect(!result.ok && result.error.code).toBe('ASSET_NOT_FOUND');
    expect(!result.ok && result.error.details).toHaveLength(4);
    expect(await repository.list('podcast-a')).toHaveLength(0);
  });

  it('rejette un thème introuvable', async () => {
    const { catalog, deps } = setup();
    catalog.publishTemplate('sans-theme', 1, {
      ...(standardTemplate(1) as object),
      id: 'sans-theme',
      brandThemeId: 'absent',
    });
    const result = await createEpisodeFromTemplate(request({ templateId: 'sans-theme' }), deps);
    expect(!result.ok && result.error.code).toBe('THEME_NOT_FOUND');
  });
});

describe('isolation entre podcasts', () => {
  it('un épisode d’un podcast est introuvable depuis un autre', async () => {
    const { deps, repository } = setup();
    const episode = episodeOf(await createEpisodeFromTemplate(request(), deps));
    expect(await repository.get('podcast-a', episode.id)).not.toBeNull();
    expect(await repository.get('podcast-b', episode.id)).toBeNull();
    expect(await repository.list('podcast-b')).toEqual([]);
  });

  it('refuse une mise à jour sur une révision périmée', async () => {
    const { deps, repository } = setup();
    const episode = episodeOf(await createEpisodeFromTemplate(request(), deps));
    expect(await repository.replace({ ...episode, title: 'Nouveau titre' }, 1)).toBe(true);
    expect(await repository.replace({ ...episode, title: 'Autre titre' }, 1)).toBe(false);
    expect((await repository.get('podcast-a', episode.id))?.title).toBe('Nouveau titre');
    expect((await repository.get('podcast-a', episode.id))?.revision).toBe(2);
  });
});
