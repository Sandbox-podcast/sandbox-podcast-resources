import type { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { RateLimiter, contentHash, readHtml } from '../src/index.ts';
import {
  GOOD_HTML,
  call,
  createEpisode,
  createEpisodeArgs,
  createHarness,
  expectError,
  expectOk,
  firstPresentation,
  until,
  type Harness,
} from './harness.ts';

let h: Harness;
let agent: Client;
let credentialId: string;

beforeEach(async () => {
  h = await createHarness();
  credentialId = h.issue().id;
  agent = await h.connect(credentialId);
});

afterEach(async () => {
  await h.close();
});

describe('création d’épisode (AC-MCP-001)', () => {
  it('un agent autorisé crée un épisode qu’on retrouve dans l’application', async () => {
    const { episodeId } = await createEpisode(agent);
    const stored = await h.episodes.get('podcast-a', episodeId);
    expect(stored?.title).toBe('Les agents IA');
    expect(stored?.segments).toHaveLength(4);
    expect(stored?.createdBy).toBe('lou');
    expect(stored?.podcastId).toBe('podcast-a');
  });

  it('le podcast vient du credential : un argument podcastId est refusé', async () => {
    const result = await agent.callTool({
      name: 'create_episode_from_template',
      arguments: createEpisodeArgs({ podcastId: 'podcast-b' }),
    });
    expect(result.isError).toBe(true);
    expect(await h.episodes.list('podcast-b')).toHaveLength(0);
    expect(await h.episodes.list('podcast-a')).toHaveLength(0);
  });

  it('expose le contrat de chaque tool : schémas, scopes, idempotence, effets, confirmation, audit, limite', async () => {
    const { tools } = await agent.listTools();
    const names = tools.map((t) => t.name).sort();
    expect(names).toEqual([
      'create_episode_from_template',
      'create_presentation',
      'get_episode',
      'get_presentation',
      'list_assets',
      'list_segments',
      'publish_presentation_version',
      'update_presentation',
      'update_segment',
    ]);
    for (const tool of tools) {
      expect(tool.inputSchema.type).toBe('object');
      expect(tool.outputSchema?.type).toBe('object');
      expect(tool.description).toMatch(/Scopes requis : /);
      expect(tool.description).toMatch(/Idempotence : /);
      expect(tool.description).toMatch(/Effets de bord : /);
    }
    for (const meta of h.platform.describeTools()) {
      expect(meta.requiredScopes.length).toBeGreaterThan(0);
      expect(meta.idempotencyBehavior.length).toBeGreaterThan(10);
      expect(meta.sideEffects.length).toBeGreaterThan(0);
      expect(meta.auditPolicy.length).toBeGreaterThan(10);
      expect(meta.rateLimit.cost).toBeGreaterThan(0);
    }
    const publish = h.platform
      .describeTools()
      .find((t) => t.name === 'publish_presentation_version');
    expect(publish?.confirmationPolicy).toBe('HUMAN_REQUIRED');
  });

  it('aucun tool ne permet à un agent d’approuver une confirmation', async () => {
    const { tools } = await agent.listTools();
    expect(tools.filter((t) => /approv|confirm|decide/i.test(t.name))).toEqual([]);
  });
});

describe('modification d’une présentation, propagée en direct (AC-MCP-002)', () => {
  it('l’agent écrit, l’humain connecté voit le contenu sans rafraîchir, puis la mise à jour', async () => {
    const { episodeId } = await createEpisode(agent);
    const { presentationId, documentId } = await firstPresentation(h, 'podcast-a', episodeId);
    const human = h.humanClient(documentId);
    human.connect();
    await human.whenSynced();

    const created = expectOk(
      await call(agent, 'create_presentation', {
        episodeId,
        presentationId,
        title: 'Accueil',
        html: GOOD_HTML,
      }),
    );
    expect(created.data).toMatchObject({ created: true, contentHash: contentHash(GOOD_HTML) });
    await until(() => human.doc.getText('html').toJSON() === GOOD_HTML);
    expect(human.doc.getMap('meta').get('title')).toBe('Accueil');

    const updated = '<h1>Nouveau titre</h1>';
    expectOk(
      await call(agent, 'update_presentation', {
        episodeId,
        presentationId,
        expectedHash: contentHash(GOOD_HTML),
        html: updated,
      }),
    );
    await until(() => human.doc.getText('html').toJSON() === updated);
  });

  it('un humain peut ensuite modifier ce que l’agent a écrit, et l’agent le relit', async () => {
    const { episodeId } = await createEpisode(agent);
    const { presentationId, documentId } = await firstPresentation(h, 'podcast-a', episodeId);
    expectOk(
      await call(agent, 'create_presentation', {
        episodeId,
        presentationId,
        title: 'T',
        html: GOOD_HTML,
      }),
    );
    const human = h.humanClient(documentId);
    human.connect();
    await human.whenSynced();
    human.doc.getText('html').insert(0, '<!-- relu par Lou -->');
    await until(async () => readHtml(await h.collab.document(documentId)).startsWith('<!-- relu'));
    const read = expectOk(await call(agent, 'get_presentation', { episodeId, presentationId }));
    expect((read.data as { html: string }).html).toBe(`<!-- relu par Lou -->${GOOD_HTML}`);
  });

  it('refuse d’écraser le travail d’un humain fait depuis la lecture (CONFLICT)', async () => {
    const { episodeId } = await createEpisode(agent);
    const { presentationId, documentId } = await firstPresentation(h, 'podcast-a', episodeId);
    expectOk(
      await call(agent, 'create_presentation', {
        episodeId,
        presentationId,
        title: 'T',
        html: GOOD_HTML,
      }),
    );
    const stale = contentHash(GOOD_HTML);
    const human = h.humanClient(documentId);
    human.connect();
    await human.whenSynced();
    human.doc.getText('html').insert(0, '<!-- travail humain -->');
    await until(async () =>
      readHtml(await h.collab.document(documentId)).startsWith('<!-- travail'),
    );

    const error = expectError(
      await call(agent, 'update_presentation', {
        episodeId,
        presentationId,
        expectedHash: stale,
        html: '<p>écrase</p>',
      }),
      'CONFLICT',
    );
    expect(error.details?.[0]).toMatch(/empreinte actuelle/);
    expect(readHtml(await h.collab.document(documentId))).toContain('travail humain');
  });

  it('rejouer create_presentation avec le même contenu ne change rien, un autre contenu est refusé', async () => {
    const { episodeId } = await createEpisode(agent);
    const { presentationId } = await firstPresentation(h, 'podcast-a', episodeId);
    const args = { episodeId, presentationId, title: 'T', html: GOOD_HTML };
    expectOk(await call(agent, 'create_presentation', args));
    const again = expectOk(await call(agent, 'create_presentation', args));
    expect(again.result).toBe('UNCHANGED');
    expectError(
      await call(agent, 'create_presentation', { ...args, html: '<p>autre</p>' }),
      'ALREADY_EXISTS',
    );
  });
});

describe('refus d’autorisation (AC-MCP-003)', () => {
  it.each([
    ['create_episode_from_template', () => createEpisodeArgs(), 'episode:write'],
    ['get_episode', () => ({ episodeId: 'x' }), 'episode:read'],
    ['list_segments', () => ({ episodeId: 'x' }), 'episode:read'],
    ['list_assets', () => ({ episodeId: 'x' }), 'asset:read'],
    ['get_presentation', () => ({ episodeId: 'x', presentationId: 'y' }), 'presentation:read'],
  ])('%s sans le scope %s retourne une erreur structurée', async (tool, args, scope) => {
    const limited = h.issue({ scopes: [] });
    const client = await h.connect(limited.id);
    const error = expectError(await call(client, tool, args()), 'FORBIDDEN');
    expect(error.requiredScopes).toEqual([scope]);
  });

  it('un agent en lecture seule ne modifie rien', async () => {
    const { episodeId, segmentId, revision } = await createEpisode(agent);
    const { presentationId } = await firstPresentation(h, 'podcast-a', episodeId);
    const reader = h.issue({ scopes: ['episode:read', 'asset:read', 'presentation:read'] });
    const client = await h.connect(reader.id);

    expectError(
      await call(
        client,
        'create_episode_from_template',
        createEpisodeArgs({ idempotencyKey: 'autre-cle-0002' }),
      ),
      'FORBIDDEN',
    );
    expectError(
      await call(client, 'update_segment', {
        episodeId,
        segmentId,
        expectedRevision: revision,
        patch: { title: 'Piraté' },
      }),
      'FORBIDDEN',
    );
    expectError(
      await call(client, 'create_presentation', {
        episodeId,
        presentationId,
        title: 'T',
        html: GOOD_HTML,
      }),
      'FORBIDDEN',
    );
    expectError(
      await call(client, 'publish_presentation_version', {
        episodeId,
        presentationId,
        label: 'v1',
      }),
      'FORBIDDEN',
    );

    const stored = await h.episodes.get('podcast-a', episodeId);
    expect(stored?.revision).toBe(revision);
    expect(stored?.segments[0]?.title).not.toBe('Piraté');
    expect(await h.episodes.list('podcast-a')).toHaveLength(1);
    expect(await h.collab.document(stored?.presentations[0]?.documentId ?? '').then(readHtml)).toBe(
      '',
    );
    expect(
      h.audit.entries.filter((e) => e.credentialId === reader.id && e.result === 'DENIED'),
    ).toHaveLength(4);
  });

  it('un credential révoqué est refusé aussitôt, même sur une session MCP déjà ouverte', async () => {
    expectOk(await call(agent, 'create_episode_from_template', createEpisodeArgs()));
    h.credentials.revoke(credentialId);
    expectError(
      await call(
        agent,
        'create_episode_from_template',
        createEpisodeArgs({ idempotencyKey: 'autre-cle-0002' }),
      ),
      'UNAUTHENTICATED',
    );
    expect(await h.episodes.list('podcast-a')).toHaveLength(1);
  });

  it('un credential expiré est refusé', async () => {
    const short = h.issue({ expiresAtMs: h.clock.now + 1000 });
    const client = await h.connect(short.id);
    expectError(await call(client, 'list_segments', { episodeId: 'x' }), 'NOT_FOUND');
    h.clock.now += 1001;
    expectError(await call(client, 'list_segments', { episodeId: 'x' }), 'UNAUTHENTICATED');
  });

  it('un retrait de scope s’applique immédiatement', async () => {
    expectOk(await call(agent, 'create_episode_from_template', createEpisodeArgs()));
    h.credentials.setScopes(credentialId, ['episode:read']);
    expectError(
      await call(
        agent,
        'create_episode_from_template',
        createEpisodeArgs({ idempotencyKey: 'autre-cle-0002' }),
      ),
      'FORBIDDEN',
    );
  });

  it('un credential inconnu est refusé', async () => {
    const client = await h.connect('inconnu');
    expectError(await call(client, 'get_episode', { episodeId: 'x' }), 'UNAUTHENTICATED');
  });
});

describe('isolation entre podcasts (AC-MCP-004)', () => {
  it('un credential du podcast B ne lit ni ne modifie rien du podcast A', async () => {
    const { episodeId, segmentId, revision } = await createEpisode(agent);
    const { presentationId, documentId } = await firstPresentation(h, 'podcast-a', episodeId);
    expectOk(
      await call(agent, 'create_presentation', {
        episodeId,
        presentationId,
        title: 'Secret',
        html: GOOD_HTML,
      }),
    );
    const before = JSON.stringify(await h.episodes.get('podcast-a', episodeId));

    const intruder = await h.connect(h.issue({ podcastId: 'podcast-b', actorId: 'mallory' }).id);
    expectError(await call(intruder, 'get_episode', { episodeId }), 'NOT_FOUND');
    expectError(await call(intruder, 'list_segments', { episodeId }), 'NOT_FOUND');
    expectError(await call(intruder, 'list_assets', { episodeId }), 'NOT_FOUND');
    expectError(
      await call(intruder, 'get_presentation', { episodeId, presentationId }),
      'NOT_FOUND',
    );
    expectError(
      await call(intruder, 'update_segment', {
        episodeId,
        segmentId,
        expectedRevision: revision,
        patch: { title: 'Piraté' },
      }),
      'NOT_FOUND',
    );
    expectError(
      await call(intruder, 'create_presentation', {
        episodeId,
        presentationId,
        title: 'T',
        html: '<p>pirate</p>',
      }),
      'NOT_FOUND',
    );
    expectError(
      await call(intruder, 'update_presentation', {
        episodeId,
        presentationId,
        expectedHash: contentHash(GOOD_HTML),
        html: '<p>pirate</p>',
      }),
      'NOT_FOUND',
    );
    expectError(
      await call(intruder, 'publish_presentation_version', {
        episodeId,
        presentationId,
        label: 'v',
      }),
      'NOT_FOUND',
    );

    expect(JSON.stringify(await h.episodes.get('podcast-a', episodeId))).toBe(before);
    expect(readHtml(await h.collab.document(documentId))).toBe(GOOD_HTML);
  });

  it('un podcast ne voit pas les templates privés d’un autre', async () => {
    h.catalogs.get('podcast-a')?.publishTemplate('prive-a', 1, {
      ...((await import('@podcast/episode-factory').then((m) => m.standardTemplate(1))) as object),
      id: 'prive-a',
    });
    expectOk(
      await call(
        agent,
        'create_episode_from_template',
        createEpisodeArgs({ templateId: 'prive-a' }),
      ),
    );
    const intruder = await h.connect(h.issue({ podcastId: 'podcast-b' }).id);
    expectError(
      await call(
        intruder,
        'create_episode_from_template',
        createEpisodeArgs({ templateId: 'prive-a' }),
      ),
      'NOT_FOUND',
    );
  });

  it('la même clé d’idempotence dans deux podcasts donne deux épisodes distincts', async () => {
    const other = await h.connect(h.issue({ podcastId: 'podcast-b' }).id);
    const a = await createEpisode(agent);
    const b = await createEpisode(other);
    expect(a.episodeId).not.toBe(b.episodeId);
    expect(await h.episodes.list('podcast-a')).toHaveLength(1);
    expect(await h.episodes.list('podcast-b')).toHaveLength(1);
  });

  it('un épisode du podcast A reste invisible même avec un identifiant de présentation valide du podcast B', async () => {
    const other = await h.connect(h.issue({ podcastId: 'podcast-b' }).id);
    const a = await createEpisode(agent);
    const b = await createEpisode(other);
    const bSlot = await firstPresentation(h, 'podcast-b', b.episodeId);
    expectError(
      await call(agent, 'get_presentation', {
        episodeId: a.episodeId,
        presentationId: bSlot.presentationId,
      }),
      'NOT_FOUND',
    );
  });
});

describe('audit des mutations (AC-MCP-005)', () => {
  it('journalise toutes les tentatives de mutation, réussies ou refusées, avec tous les champs', async () => {
    const { episodeId, segmentId, revision } = await createEpisode(agent);
    const { presentationId } = await firstPresentation(h, 'podcast-a', episodeId);
    const ok = await call(agent, 'update_segment', {
      episodeId,
      segmentId,
      expectedRevision: revision,
      patch: { notes: 'Parler du budget' },
    });
    expectError(
      await call(agent, 'update_segment', {
        episodeId,
        segmentId,
        expectedRevision: revision,
        patch: { notes: 'obsolète' },
      }),
      'CONFLICT',
    );
    expectError(
      await call(agent, 'create_presentation', {
        episodeId,
        presentationId,
        title: 'T',
        html: '<iframe src="x"></iframe>',
      }),
      'INVALID_INPUT',
    );
    expectError(
      await call(agent, 'update_segment', {
        episodeId: 'absent',
        segmentId,
        expectedRevision: 1,
        patch: { notes: 'x' },
      }),
      'NOT_FOUND',
    );

    const entries = h.audit.entries;
    expect(entries.map((e) => [e.tool, e.result])).toEqual([
      ['create_episode_from_template', 'OK'],
      ['update_segment', 'OK'],
      ['update_segment', 'CONFLICT'],
      ['create_presentation', 'INVALID'],
      ['update_segment', 'NOT_FOUND'],
    ]);
    const update = entries[1];
    expect(update).toMatchObject({
      actor: 'lou',
      credentialId,
      podcastId: 'podcast-a',
      tool: 'update_segment',
      scope: 'episode:write',
      target: `episode:${episodeId}/segment:${segmentId}`,
      result: 'OK',
      timestamp: h.clock.now,
      correlationId: ok.correlationId,
    });
    for (const entry of entries) {
      expect(entry.correlationId).toMatch(/^[0-9a-f-]{36}$/);
      expect(entry.target.length).toBeGreaterThan(0);
    }
    expect(new Set(entries.map((e) => e.correlationId)).size).toBe(entries.length);
  });

  it('ne journalise pas les lectures réussies, mais journalise les lectures refusées', async () => {
    const { episodeId } = await createEpisode(agent);
    h.audit.entries.length = 0;
    expectOk(await call(agent, 'get_episode', { episodeId }));
    expect(h.audit.entries).toEqual([]);
    const limited = await h.connect(h.issue({ scopes: [] }).id);
    expectError(await call(limited, 'get_episode', { episodeId }), 'FORBIDDEN');
    expect(h.audit.entries).toHaveLength(1);
    expect(h.audit.entries[0]?.result).toBe('DENIED');
  });
});

describe('idempotence (AC-MCP-006)', () => {
  it('rejouer create_episode_from_template retourne le même épisode', async () => {
    const first = expectOk(await call(agent, 'create_episode_from_template', createEpisodeArgs()));
    const second = expectOk(await call(agent, 'create_episode_from_template', createEpisodeArgs()));
    expect(first.result).toBe('OK');
    expect(second.result).toBe('UNCHANGED');
    expect((second.data as { episodeId: string }).episodeId).toBe(
      (first.data as { episodeId: string }).episodeId,
    );
    expect(await h.episodes.list('podcast-a')).toHaveLength(1);
  });

  it('la même clé avec une autre demande est refusée', async () => {
    expectOk(await call(agent, 'create_episode_from_template', createEpisodeArgs()));
    expectError(
      await call(agent, 'create_episode_from_template', createEpisodeArgs({ title: 'Autre' })),
      'CONFLICT',
    );
    expect(await h.episodes.list('podcast-a')).toHaveLength(1);
  });

  it('update_segment est protégé par la révision attendue', async () => {
    const { episodeId, segmentId, revision } = await createEpisode(agent);
    const args = { episodeId, segmentId, expectedRevision: revision, patch: { status: 'READY' } };
    expect(expectOk(await call(agent, 'update_segment', args)).data).toMatchObject({
      revision: revision + 1,
    });
    expectError(await call(agent, 'update_segment', args), 'CONFLICT');
    const same = expectOk(
      await call(agent, 'update_segment', { ...args, expectedRevision: revision + 1 }),
    );
    expect(same.result).toBe('UNCHANGED');
    expect((await h.episodes.get('podcast-a', episodeId))?.revision).toBe(revision + 1);
  });
});

describe('validation des sorties d’un modèle avant application (AC-MCP-007)', () => {
  it.each([
    ['champ inconnu', { surprise: 'x' }],
    ['statut hors liste', { status: 'FINISHED' }],
    ['titre vide', { title: '   ' }],
    ['durée négative', { targetDurationSec: -5 }],
    ['questions de mauvais type', { questions: 'une seule' }],
    ['patch vide', {}],
  ])('rejette un patch invalide (%s) sans rien modifier', async (_label, patch) => {
    const { episodeId, segmentId, revision } = await createEpisode(agent);
    const result = await agent.callTool({
      name: 'update_segment',
      arguments: { episodeId, segmentId, expectedRevision: revision, patch },
    });
    expect(result.isError).toBe(true);
    const stored = await h.episodes.get('podcast-a', episodeId);
    expect(stored?.revision).toBe(revision);
    expect(stored?.segments[0]?.status).toBe('TODO');
  });

  it.each([
    ['ressource externe', '<img src="https://evil.example/x.png">', 'EXTERNAL_RESOURCE'],
    ['iframe', '<iframe src="/x"></iframe>', 'IFRAME'],
    ['formulaire', '<form action="/x"></form>', 'FORM'],
    ['redirection', '<meta http-equiv="refresh" content="0;url=/x">', 'META_REFRESH'],
    ['eval', '<script>eval("1")</script>', 'EVAL'],
  ])('rejette un HTML dangereux (%s) et ne touche pas au document', async (_label, html, code) => {
    const { episodeId } = await createEpisode(agent);
    const { presentationId, documentId } = await firstPresentation(h, 'podcast-a', episodeId);
    const error = expectError(
      await call(agent, 'create_presentation', { episodeId, presentationId, title: 'T', html }),
      'INVALID_INPUT',
    );
    expect(error.details?.join(' ')).toContain(code);
    expect(readHtml(await h.collab.document(documentId))).toBe('');
  });

  it('refuse un HTML dangereux aussi à la mise à jour', async () => {
    const { episodeId } = await createEpisode(agent);
    const { presentationId, documentId } = await firstPresentation(h, 'podcast-a', episodeId);
    expectOk(
      await call(agent, 'create_presentation', {
        episodeId,
        presentationId,
        title: 'T',
        html: GOOD_HTML,
      }),
    );
    expectError(
      await call(agent, 'update_presentation', {
        episodeId,
        presentationId,
        expectedHash: contentHash(GOOD_HTML),
        html: '<script src="https://evil.example/a.js"></script>',
      }),
      'INVALID_INPUT',
    );
    expect(readHtml(await h.collab.document(documentId))).toBe(GOOD_HTML);
  });
});

describe('publication avec confirmation humaine', () => {
  async function ready() {
    const { episodeId } = await createEpisode(agent);
    const { presentationId, documentId } = await firstPresentation(h, 'podcast-a', episodeId);
    expectOk(
      await call(agent, 'create_presentation', {
        episodeId,
        presentationId,
        title: 'T',
        html: GOOD_HTML,
      }),
    );
    const args = { episodeId, presentationId, label: 'Version diffusée' };
    return { episodeId, presentationId, documentId, args };
  }

  const request = async (args: Record<string, unknown>): Promise<string> => {
    const error = expectError(
      await call(agent, 'publish_presentation_version', args),
      'CONFIRMATION_REQUIRED',
    );
    if (!error.confirmationId) throw new Error('pas de confirmationId');
    return error.confirmationId;
  };

  it('ne publie rien tant qu’un humain n’a pas approuvé', async () => {
    const { episodeId, presentationId, args } = await ready();
    const confirmationId = await request(args);
    const pending = expectError(
      await call(agent, 'publish_presentation_version', { ...args, confirmationId }),
      'CONFIRMATION_REQUIRED',
    );
    expect(pending.message).toMatch(/pas encore été approuvée/);
    const slot = (await h.episodes.get('podcast-a', episodeId))?.presentations.find(
      (p) => p.id === presentationId,
    );
    expect(slot?.status).toBe('DRAFT');
    expect(await h.store.versions(slot?.documentId ?? '')).toHaveLength(0);
  });

  it('publie la version approuvée par un producteur', async () => {
    const { episodeId, presentationId, documentId, args } = await ready();
    const confirmationId = await request(args);
    expect(await h.platform.decideConfirmation(confirmationId, 'lou', true)).toEqual({
      ok: true,
      status: 'APPROVED',
    });
    const published = expectOk(
      await call(agent, 'publish_presentation_version', { ...args, confirmationId }),
    );
    const versionId = (published.data as { versionId: string }).versionId;
    const versions = await h.store.versions(documentId);
    expect(versions.map((v) => [v.id, v.label, v.createdBy])).toEqual([
      [versionId, 'Version diffusée', 'lou'],
    ]);
    const slot = (await h.episodes.get('podcast-a', episodeId))?.presentations.find(
      (p) => p.id === presentationId,
    );
    expect(slot).toMatchObject({ status: 'PUBLISHED', publishedVersionId: versionId });
    const decision = h.audit.entries.find((e) => e.tool === 'decide_confirmation');
    expect(decision).toMatchObject({
      actor: 'lou',
      credentialId: null,
      result: 'OK',
      detail: 'approuvée',
    });
  });

  it('rejouer le même appel retourne la même version sans republier', async () => {
    const { documentId, args } = await ready();
    const confirmationId = await request(args);
    await h.platform.decideConfirmation(confirmationId, 'lou', true);
    const first = expectOk(
      await call(agent, 'publish_presentation_version', { ...args, confirmationId }),
    );
    const second = expectOk(
      await call(agent, 'publish_presentation_version', { ...args, confirmationId }),
    );
    expect(second.result).toBe('UNCHANGED');
    expect(second.data).toEqual(first.data);
    expect(await h.store.versions(documentId)).toHaveLength(1);
  });

  it('une approbation ne sert qu’une fois : une seconde publication demande une nouvelle approbation', async () => {
    const { args } = await ready();
    const confirmationId = await request(args);
    await h.platform.decideConfirmation(confirmationId, 'lou', true);
    expectOk(await call(agent, 'publish_presentation_version', { ...args, confirmationId }));
    const other = { ...args, label: 'Autre version' };
    const reuse = expectError(
      await call(agent, 'publish_presentation_version', { ...other, confirmationId }),
      'CONFIRMATION_REQUIRED',
    );
    expect(reuse.message).toMatch(/autre demande|déjà servi/);
  });

  it('deux publications simultanées avec la même approbation ne créent qu’une version', async () => {
    const { documentId, args } = await ready();
    const confirmationId = await request(args);
    await h.platform.decideConfirmation(confirmationId, 'lou', true);
    const results = await Promise.all([
      call(agent, 'publish_presentation_version', { ...args, confirmationId }),
      call(agent, 'publish_presentation_version', { ...args, confirmationId }),
    ]);
    expect(results.some((r) => r.ok)).toBe(true);
    expect(results.every((r) => r.ok || r.error.code === 'CONFIRMATION_REQUIRED')).toBe(true);
    expect(await h.store.versions(documentId)).toHaveLength(1);
  });

  it('une décision humaine est définitive : un refus ne peut pas être suivi d’une approbation', async () => {
    const { documentId, args } = await ready();
    const confirmationId = await request(args);
    expect(await h.platform.decideConfirmation(confirmationId, 'lou', false)).toEqual({
      ok: true,
      status: 'REJECTED',
    });
    expect(await h.platform.decideConfirmation(confirmationId, 'lou', true)).toEqual({
      ok: false,
      reason: 'NOT_PENDING',
    });
    expectError(
      await call(agent, 'publish_presentation_version', { ...args, confirmationId }),
      'CONFIRMATION_REQUIRED',
    );
    expect(await h.store.versions(documentId)).toHaveLength(0);
  });

  it('on ne peut plus approuver une confirmation expirée', async () => {
    const { args } = await ready();
    const confirmationId = await request(args);
    h.clock.now += 10 * 60_000 + 1;
    expect(await h.platform.decideConfirmation(confirmationId, 'lou', true)).toEqual({
      ok: false,
      reason: 'NOT_PENDING',
    });
  });

  it('une confirmation inconnue ne peut pas être approuvée', async () => {
    expect(await h.platform.decideConfirmation('inconnue', 'lou', true)).toEqual({
      ok: false,
      reason: 'NOT_FOUND',
    });
  });

  it('refuse l’approbation par quelqu’un qui n’est pas producteur de l’épisode', async () => {
    const { args } = await ready();
    const confirmationId = await request(args);
    expect(await h.platform.decideConfirmation(confirmationId, 'mallory', true)).toEqual({
      ok: false,
      reason: 'FORBIDDEN',
    });
    expectError(
      await call(agent, 'publish_presentation_version', { ...args, confirmationId }),
      'CONFIRMATION_REQUIRED',
    );
    expect(h.audit.entries.find((e) => e.tool === 'decide_confirmation')).toMatchObject({
      actor: 'mallory',
      result: 'DENIED',
    });
  });

  it('une confirmation refusée par l’humain ne publie pas', async () => {
    const { documentId, args } = await ready();
    const confirmationId = await request(args);
    await h.platform.decideConfirmation(confirmationId, 'lou', false);
    const refused = expectError(
      await call(agent, 'publish_presentation_version', { ...args, confirmationId }),
      'CONFIRMATION_REQUIRED',
    );
    expect(refused.message).toMatch(/refusée/);
    expect(await h.store.versions(documentId)).toHaveLength(0);
  });

  it('refuse une confirmation accordée pour un autre libellé', async () => {
    const { documentId, args } = await ready();
    const confirmationId = await request(args);
    await h.platform.decideConfirmation(confirmationId, 'lou', true);
    expectError(
      await call(agent, 'publish_presentation_version', {
        ...args,
        label: 'Libellé détourné',
        confirmationId,
      }),
      'CONFIRMATION_REQUIRED',
    );
    expect(await h.store.versions(documentId)).toHaveLength(0);
  });

  it('l’approbation tombe si le contenu change après l’approbation', async () => {
    const { episodeId, presentationId, documentId, args } = await ready();
    const confirmationId = await request(args);
    await h.platform.decideConfirmation(confirmationId, 'lou', true);
    expectOk(
      await call(agent, 'update_presentation', {
        episodeId,
        presentationId,
        expectedHash: contentHash(GOOD_HTML),
        html: '<h1>Contenu jamais relu par un humain</h1>',
      }),
    );
    const stale = expectError(
      await call(agent, 'publish_presentation_version', { ...args, confirmationId }),
      'CONFIRMATION_REQUIRED',
    );
    expect(stale.message).toMatch(/contenu a changé/);
    expect(await h.store.versions(documentId)).toHaveLength(0);
  });

  it('une confirmation expire', async () => {
    const { args } = await ready();
    const confirmationId = await request(args);
    await h.platform.decideConfirmation(confirmationId, 'lou', true);
    h.clock.now += 10 * 60_000 + 1;
    const expired = expectError(
      await call(agent, 'publish_presentation_version', { ...args, confirmationId }),
      'CONFIRMATION_REQUIRED',
    );
    expect(expired.message).toMatch(/expiré/);
  });

  it('une confirmation d’un autre credential est inutilisable', async () => {
    const { args } = await ready();
    const confirmationId = await request(args);
    await h.platform.decideConfirmation(confirmationId, 'lou', true);
    const other = await h.connect(h.issue({ actorId: 'lou' }).id);
    expectError(
      await call(other, 'publish_presentation_version', { ...args, confirmationId }),
      'NOT_FOUND',
    );
  });

  it('refuse de publier une présentation vide', async () => {
    const { episodeId } = await createEpisode(agent);
    const { presentationId } = await firstPresentation(h, 'podcast-a', episodeId);
    expectError(
      await call(agent, 'publish_presentation_version', { episodeId, presentationId, label: 'v1' }),
      'INVALID_INPUT',
    );
  });
});

describe('limite de débit', () => {
  it('refuse au-delà du seau et reprend avec le temps', async () => {
    await h.close();
    h = await createHarness({ limiter: new RateLimiter(12, 1) });
    credentialId = h.issue().id;
    agent = await h.connect(credentialId);
    const { episodeId } = await createEpisode(agent); // mutation : 5 jetons
    let refused = 0;
    let retryAfterMs = 0;
    for (let i = 0; i < 12; i += 1) {
      const envelope = await call(agent, 'get_episode', { episodeId });
      if (!envelope.ok && envelope.error.code === 'RATE_LIMITED') {
        refused += 1;
        retryAfterMs = envelope.error.retryAfterMs ?? 0;
      }
    }
    expect(refused).toBe(5);
    expect(retryAfterMs).toBe(1000);
    h.clock.now += 3000;
    expectOk(await call(agent, 'get_episode', { episodeId }));
  });

  it('un dépassement sur une mutation est journalisé et n’applique rien', async () => {
    await h.close();
    h = await createHarness({ limiter: new RateLimiter(5, 0.001) });
    credentialId = h.issue().id;
    agent = await h.connect(credentialId);
    await createEpisode(agent);
    expectError(
      await call(
        agent,
        'create_episode_from_template',
        createEpisodeArgs({ idempotencyKey: 'autre-cle-0002' }),
      ),
      'RATE_LIMITED',
    );
    expect(await h.episodes.list('podcast-a')).toHaveLength(1);
    expect(h.audit.entries.at(-1)).toMatchObject({
      result: 'RATE_LIMITED',
      tool: 'create_episode_from_template',
    });
  });

  it('les limites sont indépendantes par credential', async () => {
    await h.close();
    h = await createHarness({ limiter: new RateLimiter(5, 0.001) });
    const first = await h.connect(h.issue().id);
    const second = await h.connect(h.issue().id);
    await createEpisode(first);
    expectError(await call(first, 'get_episode', { episodeId: 'x' }), 'RATE_LIMITED');
    expectError(await call(second, 'get_episode', { episodeId: 'x' }), 'NOT_FOUND');
  });
});

describe('robustesse', () => {
  it('une erreur interne ne divulgue pas ses détails à l’agent mais reste dans l’audit', async () => {
    const { episodeId } = await createEpisode(agent);
    const original = h.episodes.get.bind(h.episodes);
    h.episodes.get = () =>
      Promise.reject(new Error('connexion à postgres://secret@interne refusée'));
    const envelope = await call(agent, 'get_episode', { episodeId });
    h.episodes.get = original;
    const error = expectError(envelope, 'INTERNAL');
    expect(JSON.stringify(error)).not.toContain('postgres');
    expect(error.message).toContain(envelope.correlationId);
  });

  it('une mutation en échec interne est journalisée avec le détail', async () => {
    const { episodeId, segmentId, revision } = await createEpisode(agent);
    const original = h.episodes.replace.bind(h.episodes);
    h.episodes.replace = () => Promise.reject(new Error('disque plein'));
    expectError(
      await call(agent, 'update_segment', {
        episodeId,
        segmentId,
        expectedRevision: revision,
        patch: { notes: 'x' },
      }),
      'INTERNAL',
    );
    h.episodes.replace = original;
    expect(h.audit.entries.at(-1)).toMatchObject({ result: 'ERROR', detail: 'disque plein' });
  });

  it('list_segments retourne les séquences dans l’ordre du conducteur', async () => {
    const { episodeId } = await createEpisode(agent);
    const envelope = expectOk(await call(agent, 'list_segments', { episodeId }));
    const titles = (envelope.data as { segments: { title: string }[] }).segments.map(
      (s) => s.title,
    );
    expect(titles).toEqual(['INTRO', 'SÉQUENCE A', 'SÉQUENCE B', 'CONCLUSION']);
  });

  it('retourne la même enveloppe pour une réussite et une erreur, avec corrélation', async () => {
    const ok = await call(agent, 'create_episode_from_template', createEpisodeArgs());
    const ko = await call(agent, 'get_episode', { episodeId: 'absent' });
    expect(ok.correlationId).toMatch(/^[0-9a-f-]{36}$/);
    expect(ko.correlationId).toMatch(/^[0-9a-f-]{36}$/);
    expect(ok.correlationId).not.toBe(ko.correlationId);
  });
});
