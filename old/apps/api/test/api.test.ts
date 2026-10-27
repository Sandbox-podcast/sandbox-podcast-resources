import { cp, mkdir, mkdtemp, readFile, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { afterAll, beforeAll, describe, expect, it } from 'vitest';
import { PgEpisodeRepository } from '../src/services/episodes.ts';
import { PgStudioStore } from '../src/services/pg-studio-store.ts';
import { MIGRATIONS_DIR, MigrationTamperedError, migrate } from '../src/db/migrate.ts';
import { ORIGIN, PASSWORD, createEnv, findDatabase, type Env } from './harness.ts';

const database = await findDatabase();
if (database === null)
  console.warn(
    'PostgreSQL injoignable : les tests d’intégration sont SAUTÉS (pnpm env:init && pnpm db:up).',
  );
const suite = describe.skipIf(database === null);

const claims = (jwt: string): Record<string, any> =>
  JSON.parse(Buffer.from(jwt.split('.')[1] ?? '', 'base64url').toString('utf8')) as Record<
    string,
    any
  >;

suite('migrations et journal d’audit', () => {
  let env: Env;
  beforeAll(async () => {
    env = await createEnv(database ?? '');
  });
  afterAll(async () => {
    await env.close();
  });

  it('sont idempotentes', async () => {
    const report = await migrate(env.pool);
    expect(report.applied).toEqual([]);
    expect(report.alreadyApplied).toEqual(['0001_init.sql']);
  });

  it('refusent qu’un fichier déjà appliqué ait changé', async () => {
    const dir = await mkdtemp(join(tmpdir(), 'migrations-'));
    await cp(MIGRATIONS_DIR, dir, { recursive: true });
    const file = join(dir, '0001_init.sql');
    await writeFile(file, `${await readFile(file, 'utf8')}\n-- modification\n`);
    await expect(migrate(env.pool, dir)).rejects.toBeInstanceOf(MigrationTamperedError);
  });

  it('appliquent une nouvelle migration sans toucher aux anciennes, dans une transaction', async () => {
    const dir = await mkdtemp(join(tmpdir(), 'migrations-'));
    await cp(MIGRATIONS_DIR, dir, { recursive: true });
    await writeFile(join(dir, '0002_test.sql'), 'create table essai (id int primary key);');
    expect((await migrate(env.pool, dir)).applied).toEqual(['0002_test.sql']);
    await writeFile(
      join(dir, '0003_cassee.sql'),
      'create table autre (id int); select erreur_volontaire();',
    );
    await expect(migrate(env.pool, dir)).rejects.toThrow();
    const tables = await env.pool.query("select to_regclass('autre') as t");
    expect(tables.rows[0].t).toBeNull();
  });

  it('l’audit est en ajout seul : ni modification, ni suppression, ni vidage', async () => {
    await env.pool.query(
      "insert into audit_log (actor_kind, action, target, result, correlation_id) values ('SYSTEM', 'essai', 'x', 'OK', 'corr-0001')",
    );
    await expect(env.pool.query("update audit_log set result = 'DENIED'")).rejects.toThrow(
      /ajout seul/,
    );
    await expect(env.pool.query('delete from audit_log')).rejects.toThrow(/ajout seul/);
    await expect(env.pool.query('truncate audit_log')).rejects.toThrow(/ajout seul/);
    expect((await env.pool.query('select count(*)::int as n from audit_log')).rows[0].n).toBe(1);
  });
});

suite('authentification (AC-SEC)', () => {
  let env: Env;
  beforeAll(async () => {
    env = await createEnv(database ?? '');
  });
  afterAll(async () => {
    await env.close();
  });

  it('ne stocke ni mot de passe ni jeton en clair', async () => {
    const u = await env.user('stockage@example.org');
    const user = (await env.pool.query('select password_hash from users where id = $1', [u.id]))
      .rows[0];
    expect(user.password_hash).toMatch(/^scrypt\$/);
    expect(user.password_hash).not.toContain(PASSWORD);
    const sessions = (
      await env.pool.query('select token_hash from sessions where user_id = $1', [u.id])
    ).rows;
    expect(sessions).toHaveLength(1);
    expect(sessions[0].token_hash).toMatch(/^[0-9a-f]{64}$/);
    expect(sessions[0].token_hash).not.toBe(u.token);
  });

  it('une connexion réussie pose un cookie HttpOnly SameSite=Strict et renvoie la corrélation', async () => {
    await env.user('cookie@example.org');
    const response = await env.call('POST', '/api/auth/login', {
      body: { email: 'COOKIE@example.org', password: PASSWORD },
      origin: ORIGIN,
      headers: { 'x-correlation-id': 'corr-abcdef12' },
    });
    expect(response.status).toBe(200);
    const cookie = String(response.headers['set-cookie']);
    expect(cookie).toMatch(
      /^session=[A-Za-z0-9_-]{43}; Path=\/; HttpOnly; SameSite=Strict; Expires=/,
    );
    expect(response.headers['x-correlation-id']).toBe('corr-abcdef12');
    expect(response.headers['x-content-type-options']).toBe('nosniff');
    expect(response.headers['cache-control']).toBe('no-store');
  });

  it('un compte inconnu et un mauvais mot de passe donnent la même réponse', async () => {
    await env.user('connu@example.org');
    const wrong = await env.call('POST', '/api/auth/login', {
      body: { email: 'connu@example.org', password: 'faux-faux-faux-faux' },
    });
    const unknown = await env.call('POST', '/api/auth/login', {
      body: { email: 'inconnu@example.org', password: 'faux-faux-faux-faux' },
    });
    expect(wrong.status).toBe(401);
    expect(unknown.status).toBe(401);
    expect(wrong.body.error).toEqual(unknown.body.error);
  });

  it('verrouille après trois échecs, même avec le bon mot de passe, puis rouvre après le délai', async () => {
    await env.user('verrou@example.org');
    for (let i = 0; i < 3; i += 1)
      expect(
        (
          await env.call('POST', '/api/auth/login', {
            body: { email: 'verrou@example.org', password: 'faux-faux-faux-faux' },
          })
        ).status,
      ).toBe(401);
    const locked = await env.call('POST', '/api/auth/login', {
      body: { email: 'verrou@example.org', password: PASSWORD },
    });
    expect(locked.status).toBe(429);
    expect(locked.body.error.code).toBe('ACCOUNT_LOCKED');
    env.clock.t += 16 * 60_000;
    expect(
      (
        await env.call('POST', '/api/auth/login', {
          body: { email: 'verrou@example.org', password: PASSWORD },
        })
      ).status,
    ).toBe(200);
  });

  it('compte aussi les échecs d’une adresse inconnue (rien n’est révélé)', async () => {
    for (let i = 0; i < 3; i += 1)
      await env.call('POST', '/api/auth/login', {
        body: { email: 'fantome@example.org', password: 'faux-faux-faux-faux' },
      });
    const result = await env.call('POST', '/api/auth/login', {
      body: { email: 'fantome@example.org', password: 'faux-faux-faux-faux' },
    });
    expect(result.status).toBe(429);
  });

  it('le bon jeton ouvre /api/me, un jeton forgé, malformé ou absent non', async () => {
    const u = await env.user('moi@example.org');
    expect((await env.call('GET', '/api/me', { token: u.token })).body.user.email).toBe(
      'moi@example.org',
    );
    expect((await env.call('GET', '/api/me')).status).toBe(401);
    expect((await env.call('GET', '/api/me', { token: 'a'.repeat(43) })).status).toBe(401);
    expect((await env.call('GET', '/api/me', { token: "' or 1=1 --" })).status).toBe(401);
  });

  it('expire, et se révoque à la déconnexion', async () => {
    const u = await env.user('session@example.org');
    expect((await env.call('GET', '/api/me', { token: u.token })).status).toBe(200);
    expect((await env.call('POST', '/api/auth/logout', { token: u.token })).status).toBe(200);
    expect((await env.call('GET', '/api/me', { token: u.token })).status).toBe(401);
    const v = await env.user('expire@example.org');
    env.clock.t += 25 * 3_600_000;
    expect((await env.call('GET', '/api/me', { token: v.token })).status).toBe(401);
  });

  it('un compte désactivé perd ses sessions', async () => {
    const u = await env.user('desactive@example.org');
    await env.pool.query('update users set disabled = true where id = $1', [u.id]);
    expect((await env.call('GET', '/api/me', { token: u.token })).status).toBe(401);
    expect(
      (
        await env.call('POST', '/api/auth/login', {
          body: { email: 'desactive@example.org', password: PASSWORD },
        })
      ).status,
    ).toBe(401);
  });

  it('protège contre le CSRF : une requête qui modifie l’état par cookie exige une origine autorisée', async () => {
    const u = await env.user('csrf@example.org');
    const cookie = `session=${u.token}`;
    const noOrigin = await env.call('POST', '/api/podcasts', { cookie, body: { name: 'X' } });
    expect(noOrigin.status).toBe(403);
    expect(noOrigin.body.error.code).toBe('BAD_ORIGIN');
    expect(
      (
        await env.call('POST', '/api/podcasts', {
          cookie,
          body: { name: 'X' },
          origin: 'https://evil.example',
        })
      ).status,
    ).toBe(403);
    expect(
      (await env.call('POST', '/api/podcasts', { cookie, body: { name: 'X' }, origin: ORIGIN }))
        .status,
    ).toBe(201);
    // La lecture par cookie n'a pas besoin d'origine ; le jeton porteur n'est pas concerné (il n'est pas envoyé automatiquement).
    expect((await env.call('GET', '/api/me', { cookie })).status).toBe(200);
    expect(
      (await env.call('POST', '/api/podcasts', { token: u.token, body: { name: 'Y' } })).status,
    ).toBe(201);
  });

  it('refuse une connexion annonçant une origine non autorisée', async () => {
    await env.user('origine@example.org');
    const response = await env.call('POST', '/api/auth/login', {
      body: { email: 'origine@example.org', password: PASSWORD },
      origin: 'https://evil.example',
    });
    expect(response.status).toBe(403);
  });

  it('limite le débit des connexions', async () => {
    let last = 0;
    for (let i = 0; i < 25; i += 1)
      last = (
        await env.call('POST', '/api/auth/login', {
          body: { email: `inconnu${String(i)}@example.org`, password: 'faux-faux-faux-faux' },
        })
      ).status;
    expect(last).toBe(429);
  });

  it('l’inscription est fermée par défaut et exige une origine, un mot de passe solide', async () => {
    const closed = await createEnv(database ?? '', { ALLOW_REGISTRATION: 'false' });
    try {
      expect(
        (
          await closed.call('POST', '/api/auth/register', {
            origin: ORIGIN,
            body: { email: 'a@b.fr', password: PASSWORD, displayName: 'A' },
          })
        ).status,
      ).toBe(403);
    } finally {
      await closed.close();
    }
    const weak = await env.call('POST', '/api/auth/register', {
      origin: ORIGIN,
      body: { email: 'faible@example.org', password: 'court', displayName: 'F' },
    });
    expect(weak.status).toBe(400);
    expect(weak.body.error.code).toBe('WEAK_PASSWORD');
    const noOrigin = await env.call('POST', '/api/auth/register', {
      body: { email: 'ok@example.org', password: PASSWORD, displayName: 'O' },
    });
    expect(noOrigin.status).toBe(403);
    const ok = await env.call('POST', '/api/auth/register', {
      origin: ORIGIN,
      body: { email: 'nouveau@example.org', password: PASSWORD, displayName: 'N' },
    });
    expect(ok.status).toBe(201);
    expect(
      (
        await env.call('POST', '/api/auth/register', {
          origin: ORIGIN,
          body: { email: 'nouveau@example.org', password: PASSWORD, displayName: 'N' },
        })
      ).body.error.code,
    ).toBe('EMAIL_TAKEN');
  });

  it('refuse un corps avec des champs inattendus', async () => {
    env.clock.t += 120_000; // la fenêtre du limiteur de connexions est passée
    const response = await env.call('POST', '/api/auth/login', {
      body: { email: 'a@b.fr', password: 'x', admin: true },
    });
    expect(response.status).toBe(400);
    expect(response.body.error.code).toBe('INVALID_INPUT');
  });

  it('expose la santé', async () => {
    expect((await env.call('GET', '/healthz')).body).toEqual({ status: 'ok' });
    expect((await env.call('GET', '/readyz')).body).toEqual({ status: 'ready' });
  });
});

suite('podcasts, rôles et isolation (AC-SEC-001, AC-SEC-002)', () => {
  let env: Env;
  let admin: Awaited<ReturnType<Env['user']>>;
  let producer: Awaited<ReturnType<Env['user']>>;
  let host: Awaited<ReturnType<Env['user']>>;
  let editor: Awaited<ReturnType<Env['user']>>;
  let viewer: Awaited<ReturnType<Env['user']>>;
  let outsider: Awaited<ReturnType<Env['user']>>;
  let podcastId: string;

  beforeAll(async () => {
    env = await createEnv(database ?? '');
    admin = await env.user('admin@example.org', 'Admin');
    producer = await env.user('producer@example.org', 'Producer');
    host = await env.user('host@example.org', 'Host');
    editor = await env.user('editor@example.org', 'Editor');
    viewer = await env.user('viewer@example.org', 'Viewer');
    outsider = await env.user('outsider@example.org', 'Outsider');
    podcastId = (
      await env.call('POST', '/api/podcasts', { token: admin.token, body: { name: 'Mon podcast' } })
    ).body.podcast.id;
    for (const [user, role] of [
      [producer, 'PRODUCER'],
      [host, 'HOST'],
      [editor, 'EDITOR'],
      [viewer, 'VIEWER'],
    ] as const)
      await env.call('POST', `/api/podcasts/${podcastId}/members`, {
        token: admin.token,
        body: { email: user.email, role },
      });
    await env.call('POST', '/api/podcasts', {
      token: outsider.token,
      body: { name: 'Autre podcast' },
    });
  });
  afterAll(async () => {
    await env.close();
  });

  it('le créateur est ADMIN et son catalogue est amorcé (template standard v1)', async () => {
    const me = await env.call('GET', '/api/me', { token: admin.token });
    expect(me.body.podcasts).toEqual([{ id: podcastId, name: 'Mon podcast', role: 'ADMIN' }]);
    const templates = await env.pool.query(
      'select id, version from templates where podcast_id = $1',
      [podcastId],
    );
    expect(templates.rows).toEqual([{ id: 'standard', version: 1 }]);
  });

  it('seul un ADMIN gère les membres ; un rôle inventé est refusé', async () => {
    const attempt = (token: string, role = 'ADMIN') =>
      env.call('POST', `/api/podcasts/${podcastId}/members`, {
        token,
        body: { email: outsider.email, role },
      });
    expect((await attempt(producer.token)).status).toBe(403);
    expect((await attempt(host.token)).status).toBe(403);
    expect((await attempt(admin.token, 'SUPERADMIN')).status).toBe(400);
    expect(
      (
        await env.call('POST', `/api/podcasts/${podcastId}/members`, {
          token: admin.token,
          body: { email: 'personne@example.org', role: 'VIEWER' },
        })
      ).status,
    ).toBe(404);
  });

  it('un utilisateur ne voit rien d’un podcast dont il n’est pas membre (404, pas 403)', async () => {
    const paths = [
      `/api/podcasts/${podcastId}/episodes`,
      `/api/podcasts/${podcastId}/episodes/00000000-0000-4000-8000-000000000000`,
    ];
    for (const path of paths)
      expect((await env.call('GET', path, { token: outsider.token })).status).toBe(404);
    expect(
      (
        await env.call('POST', `/api/podcasts/${podcastId}/episodes`, {
          token: outsider.token,
          body: {},
        })
      ).status,
    ).toBe(404);
    expect(
      (await env.call('GET', `/api/podcasts/not-a-uuid/episodes`, { token: outsider.token }))
        .status,
    ).toBe(404);
  });

  it('chaque rôle ne peut créer un épisode que s’il en a le droit, et les refus sont audités', async () => {
    const create = (token: string, key: string) =>
      env.call('POST', `/api/podcasts/${podcastId}/episodes`, {
        token,
        body: {
          templateId: 'standard',
          title: `Épisode ${key}`,
          date: '2026-10-06',
          idempotencyKey: `cle-${key}-0001`,
        },
      });
    expect((await create(viewer.token, 'v')).status).toBe(403);
    expect((await create(editor.token, 'e')).status).toBe(403);
    expect((await create(host.token, 'h')).status).toBe(403);
    expect((await create(producer.token, 'p')).status).toBe(201);
    expect((await create(admin.token, 'a')).status).toBe(201);
    const denied = await env.pool.query(
      "select actor_user_id from audit_log where action = 'denied:episode:create' order by id",
    );
    expect(denied.rows.map((r) => r.actor_user_id)).toEqual([viewer.id, editor.id, host.id]);
  });

  it('un VIEWER lit, un EDITOR et un HOST modifient le conducteur, un VIEWER non', async () => {
    const episode = (
      await env.call('POST', `/api/podcasts/${podcastId}/episodes`, {
        token: producer.token,
        body: {
          templateId: 'standard',
          title: 'Droits',
          date: '2026-10-06',
          idempotencyKey: 'cle-droits-0001',
        },
      })
    ).body.episode;
    const segmentId = episode.segments[0].id;
    const patch = (token: string, revision: number, notes: string) =>
      env.call('PATCH', `/api/podcasts/${podcastId}/episodes/${episode.id}/segments/${segmentId}`, {
        token,
        body: { expectedRevision: revision, patch: { notes } },
      });
    expect(
      (
        await env.call('GET', `/api/podcasts/${podcastId}/episodes/${episode.id}`, {
          token: viewer.token,
        })
      ).status,
    ).toBe(200);
    expect((await patch(viewer.token, 1, 'non')).status).toBe(403);
    const byEditor = await patch(editor.token, 1, 'notes de l’éditeur');
    expect(byEditor.status).toBe(200);
    expect(byEditor.body.episode.revision).toBe(2);
    expect((await patch(host.token, 2, 'notes de l’hôte')).status).toBe(200);
  });
});

suite('épisodes : création, idempotence, conflits', () => {
  let env: Env;
  let producer: Awaited<ReturnType<Env['user']>>;
  let intruder: Awaited<ReturnType<Env['user']>>;
  let podcastId: string;
  let otherPodcastId: string;
  const body = (key: string, extra: object = {}) => ({
    templateId: 'standard',
    title: 'Les agents IA',
    date: '2026-10-05',
    idempotencyKey: key,
    ...extra,
  });

  beforeAll(async () => {
    env = await createEnv(database ?? '');
    producer = await env.user('prod@example.org');
    intruder = await env.user('intrus@example.org');
    podcastId = (
      await env.call('POST', '/api/podcasts', { token: producer.token, body: { name: 'P1' } })
    ).body.podcast.id;
    otherPodcastId = (
      await env.call('POST', '/api/podcasts', { token: intruder.token, body: { name: 'P2' } })
    ).body.podcast.id;
  });
  afterAll(async () => {
    await env.close();
  });

  it('crée un épisode complet, persistant, avec ses quatre séquences et son origine', async () => {
    const response = await env.call('POST', `/api/podcasts/${podcastId}/episodes`, {
      token: producer.token,
      body: body('cle-creation-01'),
    });
    expect(response.status).toBe(201);
    const { episode } = response.body;
    expect((episode.segments as { title: string }[]).map((s) => s.title)).toEqual([
      'INTRO',
      'SÉQUENCE A',
      'SÉQUENCE B',
      'CONCLUSION',
    ]);
    expect(episode.origin).toMatchObject({
      templateId: 'standard',
      templateVersion: 1,
      brandThemeVersion: 1,
    });
    expect(episode.podcastId).toBe(podcastId);
    const stored = await env.pool.query('select podcast_id, revision from episodes where id = $1', [
      episode.id,
    ]);
    expect(stored.rows[0]).toEqual({ podcast_id: podcastId, revision: 1 });
    const list = await env.call('GET', `/api/podcasts/${podcastId}/episodes`, {
      token: producer.token,
    });
    expect(list.body.episodes).toHaveLength(1);
  });

  it('est idempotente : même clé, même demande = même épisode ; autre demande = conflit', async () => {
    const first = await env.call('POST', `/api/podcasts/${podcastId}/episodes`, {
      token: producer.token,
      body: body('cle-idem-0001'),
    });
    const second = await env.call('POST', `/api/podcasts/${podcastId}/episodes`, {
      token: producer.token,
      body: body('cle-idem-0001'),
    });
    expect(first.status).toBe(201);
    expect(second.status).toBe(200);
    expect(second.body.created).toBe(false);
    expect(second.body.episode.id).toBe(first.body.episode.id);
    const conflict = await env.call('POST', `/api/podcasts/${podcastId}/episodes`, {
      token: producer.token,
      body: body('cle-idem-0001', { title: 'Autre titre' }),
    });
    expect(conflict.status).toBe(409);
    expect(conflict.body.error.code).toBe('IDEMPOTENCY_KEY_CONFLICT');
  });

  it('cinq demandes simultanées avec la même clé ne créent qu’un épisode', async () => {
    const results = await Promise.all(
      Array.from({ length: 5 }, () =>
        env.call('POST', `/api/podcasts/${podcastId}/episodes`, {
          token: producer.token,
          body: body('cle-course-0001'),
        }),
      ),
    );
    expect(results.every((r) => r.status === 200 || r.status === 201)).toBe(true);
    expect(new Set(results.map((r) => r.body.episode.id)).size).toBe(1);
    expect(
      (
        await env.pool.query(
          "select count(*)::int as n from episodes where title = 'Les agents IA' and id = $1",
          [results[0]?.body.episode.id],
        )
      ).rows[0].n,
    ).toBe(1);
  });

  it('rejette un template inconnu et les entrées invalides sans rien écrire', async () => {
    const before = (await env.pool.query('select count(*)::int as n from episodes')).rows[0].n;
    expect(
      (
        await env.call('POST', `/api/podcasts/${podcastId}/episodes`, {
          token: producer.token,
          body: body('cle-inconnu-001', { templateId: 'absent' }),
        })
      ).status,
    ).toBe(404);
    expect(
      (
        await env.call('POST', `/api/podcasts/${podcastId}/episodes`, {
          token: producer.token,
          body: body('cle-vide-00001', { title: '  ' }),
        })
      ).status,
    ).toBe(400);
    expect(
      (
        await env.call('POST', `/api/podcasts/${podcastId}/episodes`, {
          token: producer.token,
          body: body('cle-date-00001', { date: '05/10/2026' }),
        })
      ).status,
    ).toBe(400);
    expect(
      (
        await env.call('POST', `/api/podcasts/${podcastId}/episodes`, {
          token: producer.token,
          body: body('cle-champ-00001', { podcastId: otherPodcastId }),
        })
      ).status,
    ).toBe(400);
    expect((await env.pool.query('select count(*)::int as n from episodes')).rows[0].n).toBe(
      before,
    );
  });

  it('le dépôt sérialise les créations simultanées de même clé même sans passer par l’API', async () => {
    const sample = (
      await env.call('POST', `/api/podcasts/${podcastId}/episodes`, {
        token: producer.token,
        body: body('cle-depot-000001'),
      })
    ).body.episode;
    const repository = new PgEpisodeRepository(env.pool);
    const results = await Promise.all(
      Array.from({ length: 8 }, (_, i) =>
        repository.createIfAbsent(podcastId, 'cle-depot-course', 'empreinte-1', {
          ...sample,
          id: `00000000-0000-4000-8000-00000000000${String(i)}`,
        }),
      ),
    );
    expect(results.filter((r) => r.kind === 'CREATED')).toHaveLength(1);
    expect(results.filter((r) => r.kind === 'EXISTING')).toHaveLength(7);
    const winner = results.find((r) => r.kind === 'CREATED');
    expect(
      results
        .filter((r) => r.kind === 'EXISTING')
        .every((r) => r.episode.id === (winner?.kind === 'CREATED' ? winner.episode.id : '')),
    ).toBe(true);
  });

  it('la même clé dans deux podcasts donne deux épisodes ; un épisode reste invisible depuis un autre podcast', async () => {
    const mine = await env.call('POST', `/api/podcasts/${podcastId}/episodes`, {
      token: producer.token,
      body: body('cle-partagee-001'),
    });
    const theirs = await env.call('POST', `/api/podcasts/${otherPodcastId}/episodes`, {
      token: intruder.token,
      body: body('cle-partagee-001'),
    });
    expect(mine.body.episode.id).not.toBe(theirs.body.episode.id);
    // Mon épisode demandé par l'identifiant, mais via le podcast de l'intrus.
    expect(
      (
        await env.call('GET', `/api/podcasts/${otherPodcastId}/episodes/${mine.body.episode.id}`, {
          token: intruder.token,
        })
      ).status,
    ).toBe(404);
    // Et l'intrus n'est pas membre de mon podcast.
    expect(
      (
        await env.call('GET', `/api/podcasts/${podcastId}/episodes/${mine.body.episode.id}`, {
          token: intruder.token,
        })
      ).status,
    ).toBe(404);
  });

  it('une nouvelle version de template ne change pas un épisode existant', async () => {
    const first = await env.call('POST', `/api/podcasts/${podcastId}/episodes`, {
      token: producer.token,
      body: body('cle-version-001'),
    });
    const template = (
      await env.pool.query(
        "select body from templates where podcast_id = $1 and id = 'standard' and version = 1",
        [podcastId],
      )
    ).rows[0].body;
    await env.pool.query(
      "insert into templates (podcast_id, id, version, body) values ($1, 'standard', 2, $2)",
      [
        podcastId,
        JSON.stringify({
          ...template,
          version: 2,
          name: 'Standard v2',
          sequences: [
            ...template.sequences,
            { key: 'bonus', title: 'BONUS', targetDurationSec: 300 },
          ],
        }),
      ],
    );
    const stored = await env.call(
      'GET',
      `/api/podcasts/${podcastId}/episodes/${first.body.episode.id}`,
      { token: producer.token },
    );
    expect(stored.body.episode.segments).toHaveLength(4);
    const second = await env.call('POST', `/api/podcasts/${podcastId}/episodes`, {
      token: producer.token,
      body: body('cle-version-002'),
    });
    expect(second.body.episode.origin.templateVersion).toBe(2);
    expect(second.body.episode.segments).toHaveLength(5);
  });

  it('la modification d’une séquence exige la bonne révision et signale le conflit', async () => {
    const episode = (
      await env.call('POST', `/api/podcasts/${podcastId}/episodes`, {
        token: producer.token,
        body: body('cle-patch-0001'),
      })
    ).body.episode;
    const segmentId = episode.segments[1].id;
    const url = `/api/podcasts/${podcastId}/episodes/${episode.id}/segments/${segmentId}`;
    const ok = await env.call('PATCH', url, {
      token: producer.token,
      body: { expectedRevision: 1, patch: { notes: 'Parler du budget', status: 'IN_PROGRESS' } },
    });
    expect(ok.status).toBe(200);
    expect(ok.body.episode.revision).toBe(2);
    expect(ok.body.episode.segments[1]).toMatchObject({
      notes: 'Parler du budget',
      status: 'IN_PROGRESS',
    });
    const stale = await env.call('PATCH', url, {
      token: producer.token,
      body: { expectedRevision: 1, patch: { notes: 'obsolète' } },
    });
    expect(stale.status).toBe(409);
    expect(stale.body.error.details).toEqual({ currentRevision: 2 });
    for (const patch of [
      {},
      { status: 'FINI' },
      { surprise: 1 },
      { title: ' ' },
      { targetDurationSec: -1 },
    ])
      expect(
        (
          await env.call('PATCH', url, {
            token: producer.token,
            body: { expectedRevision: 2, patch },
          })
        ).status,
      ).toBe(400);
    expect(
      (
        await env.call('PATCH', url.replace(segmentId, 'inconnu'), {
          token: producer.token,
          body: { expectedRevision: 2, patch: { notes: 'x' } },
        })
      ).status,
    ).toBe(404);
    const stored = await env.call('GET', `/api/podcasts/${podcastId}/episodes/${episode.id}`, {
      token: producer.token,
    });
    expect(stored.body.episode.revision).toBe(2);
  });

  it('deux modifications simultanées de la même révision : une seule gagne', async () => {
    const episode = (
      await env.call('POST', `/api/podcasts/${podcastId}/episodes`, {
        token: producer.token,
        body: body('cle-course-patch1'),
      })
    ).body.episode;
    const url = `/api/podcasts/${podcastId}/episodes/${episode.id}/segments/${episode.segments[0].id}`;
    const results = await Promise.all(
      ['a', 'b', 'c'].map((n) =>
        env.call('PATCH', url, {
          token: producer.token,
          body: { expectedRevision: 1, patch: { notes: `note ${n}` } },
        }),
      ),
    );
    expect(results.map((r) => r.status).sort()).toEqual([200, 409, 409]);
  });

  it('journalise création et modification avec la corrélation de la requête', async () => {
    const response = await env.call('POST', `/api/podcasts/${podcastId}/episodes`, {
      token: producer.token,
      body: body('cle-audit-00001'),
      headers: { 'x-correlation-id': 'corr-audit-0001' },
    });
    expect(response.status).toBe(201);
    const entries = await env.pool.query(
      "select actor_user_id, action, target, result from audit_log where correlation_id = 'corr-audit-0001'",
    );
    expect(entries.rows).toEqual([
      {
        actor_user_id: producer.id,
        action: 'episode.create',
        target: `episode:${response.body.episode.id}`,
        result: 'OK',
      },
    ]);
  });
});

suite('invitations et jetons de salle', () => {
  let env: Env;
  let producer: Awaited<ReturnType<Env['user']>>;
  let podcastId: string;
  let episodeId: string;
  const invite = async (extra: object = {}) =>
    (
      await env.call('POST', `/api/podcasts/${podcastId}/episodes/${episodeId}/invitations`, {
        token: producer.token,
        body: extra,
      })
    ).body as { token: string; expiresAt: string };

  beforeAll(async () => {
    env = await createEnv(database ?? '');
    producer = await env.user('prod@example.org');
    podcastId = (
      await env.call('POST', '/api/podcasts', { token: producer.token, body: { name: 'P' } })
    ).body.podcast.id;
    episodeId = (
      await env.call('POST', `/api/podcasts/${podcastId}/episodes`, {
        token: producer.token,
        body: {
          templateId: 'standard',
          title: 'Épisode',
          date: '2026-10-06',
          idempotencyKey: 'cle-invit-00001',
        },
      })
    ).body.episode.id;
  });
  afterAll(async () => {
    await env.close();
  });

  it('seul un membre autorisé invite, et on ne stocke que l’empreinte du jeton', async () => {
    expect(
      (
        await env.call('POST', `/api/podcasts/${podcastId}/episodes/${episodeId}/invitations`, {
          body: {},
        })
      ).status,
    ).toBe(401);
    const created = await invite({ displayName: 'Camille' });
    expect(created.token).toMatch(/^[A-Za-z0-9_-]{43}$/);
    const stored = (
      await env.pool.query('select token_hash from invitations order by created_at desc limit 1')
    ).rows[0];
    expect(stored.token_hash).not.toBe(created.token);
    expect(stored.token_hash).toMatch(/^[0-9a-f]{64}$/);
  });

  it('un invité voit l’invitation puis rejoint : identité = UUID attribué par le serveur, salle de l’épisode', async () => {
    const { token } = await invite({ displayName: 'Camille' });
    const info = await env.call('GET', `/api/invitations/${token}`);
    expect(info.body.invitation).toMatchObject({
      podcastName: 'P',
      episodeTitle: 'Épisode',
      role: 'GUEST',
      displayName: 'Camille',
    });
    const joined = await env.call('POST', `/api/invitations/${token}/join`, { body: {} });
    expect(joined.status).toBe(200);
    const participantId = joined.body.participant.id as string;
    expect(participantId).toMatch(/^[0-9a-f-]{36}$/);
    const jwt = claims(joined.body.livekit.token);
    expect(jwt['sub']).toBe(participantId);
    expect(jwt['video'].room).toBe(`ep-${episodeId}`);
    expect(jwt['video'].canPublish).toBe(true);
    expect(jwt['video'].roomAdmin).toBe(false);
    expect(joined.body.livekit.url).toBe('ws://livekit.test:7880');
    // Le même jeton redonne le même participant : une reconnexion garde la même identité.
    const again = await env.call('POST', `/api/invitations/${token}/join`, { body: {} });
    expect(again.body.participant.id).toBe(participantId);
    expect(
      (
        await env.pool.query(
          'select count(*)::int as n from participants where invitation_id is not null',
        )
      ).rows[0].n,
    ).toBeGreaterThan(0);
  });

  it('un nom hostile ne touche jamais l’identité ni un chemin : l’identité reste un UUID', async () => {
    const { token } = await invite({});
    const joined = await env.call('POST', `/api/invitations/${token}/join`, {
      body: { displayName: '../../etc/passwd\u0000' },
    });
    expect(joined.status).toBe(200);
    expect(joined.body.participant.id).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/,
    );
    expect(claims(joined.body.livekit.token)['sub']).toBe(joined.body.participant.id);
    expect(joined.body.participant.displayName).toBe('../../etc/passwd');
  });

  it('une invitation sans nom exige un nom à la première entrée', async () => {
    const { token } = await invite({});
    expect((await env.call('POST', `/api/invitations/${token}/join`, { body: {} })).status).toBe(
      404,
    );
    expect(
      (await env.call('POST', `/api/invitations/${token}/join`, { body: { displayName: '   ' } }))
        .status,
    ).toBe(404);
    expect(
      (await env.call('POST', `/api/invitations/${token}/join`, { body: { displayName: 'Sam' } }))
        .status,
    ).toBe(200);
  });

  it('refuse une invitation expirée, révoquée, inconnue ou mal formée, avec une réponse identique', async () => {
    const expired = await invite({ displayName: 'E', ttlHours: 1 });
    const revoked = await invite({ displayName: 'R' });
    env.clock.t += 2 * 3_600_000;
    const responses = [
      await env.call('GET', `/api/invitations/${expired.token}`),
      await env.call('GET', `/api/invitations/${'x'.repeat(43)}`),
      await env.call('GET', '/api/invitations/trop-court'),
    ];
    for (const r of responses) {
      expect(r.status).toBe(404);
      expect(r.body.error.code).toBe('NOT_FOUND');
    }
    expect(
      (await env.call('POST', `/api/invitations/${expired.token}/join`, { body: {} })).status,
    ).toBe(404);
    expect(
      (
        await env.call('DELETE', `/api/podcasts/${podcastId}/episodes/${episodeId}/invitations`, {
          token: producer.token,
        })
      ).body.revoked,
    ).toBeGreaterThan(0);
    expect(
      (await env.call('POST', `/api/invitations/${revoked.token}/join`, { body: {} })).status,
    ).toBe(404);
  });

  it('limite le débit des points d’entrée sans compte', async () => {
    let last = 0;
    for (let i = 0; i < 70; i += 1)
      last = (await env.call('GET', `/api/invitations/${'y'.repeat(43)}`)).status;
    expect(last).toBe(429);
  });
});

suite('studio : jeton, commandes, consentement, audit', () => {
  let env: Env;
  let producer: Awaited<ReturnType<Env['user']>>;
  let host: Awaited<ReturnType<Env['user']>>;
  let viewer: Awaited<ReturnType<Env['user']>>;
  let podcastId: string;
  let episodeId: string;
  let base: string;
  const command = (token: string, commandId: string, cmd: object, expectedVersion?: number) =>
    env.call('POST', `${base}/studio/commands`, {
      token,
      body: {
        commandId,
        command: cmd,
        ...(expectedVersion === undefined ? {} : { expectedVersion }),
      },
    });

  beforeAll(async () => {
    env = await createEnv(database ?? '');
    producer = await env.user('prod@example.org', 'Lou');
    host = await env.user('host@example.org', 'Hôte');
    viewer = await env.user('viewer@example.org', 'Lecteur');
    podcastId = (
      await env.call('POST', '/api/podcasts', { token: producer.token, body: { name: 'P' } })
    ).body.podcast.id;
    for (const [user, role] of [
      [host, 'HOST'],
      [viewer, 'VIEWER'],
    ] as const)
      await env.call('POST', `/api/podcasts/${podcastId}/members`, {
        token: producer.token,
        body: { email: user.email, role },
      });
    episodeId = (
      await env.call('POST', `/api/podcasts/${podcastId}/episodes`, {
        token: producer.token,
        body: {
          templateId: 'standard',
          title: 'Direct',
          date: '2026-10-06',
          idempotencyKey: 'cle-studio-0001',
        },
      })
    ).body.episode.id;
    base = `/api/podcasts/${podcastId}/episodes/${episodeId}`;
  });
  afterAll(async () => {
    await env.close();
  });

  it('émet un jeton de salle à un membre autorisé, pas à un lecteur, avec une identité stable', async () => {
    const first = await env.call('POST', `${base}/studio/token`, { token: producer.token });
    expect(first.status).toBe(200);
    expect(claims(first.body.livekit.token)['sub']).toBe(first.body.participantId);
    const second = await env.call('POST', `${base}/studio/token`, { token: producer.token });
    expect(second.body.participantId).toBe(first.body.participantId);
    expect((await env.call('POST', `${base}/studio/token`, { token: host.token })).status).toBe(
      200,
    );
    expect((await env.call('POST', `${base}/studio/token`, { token: viewer.token })).status).toBe(
      403,
    );
    expect((await env.call('POST', `${base}/studio/token`)).status).toBe(401);
  });

  it('seul le producteur pilote la régie ; un hôte et un lecteur sont refusés et audités', async () => {
    expect(
      (await command(host.token, 'cmd-hote-00001', { type: 'SET_AUTO_DIRECTOR', on: true })).status,
    ).toBe(403);
    expect((await command(viewer.token, 'cmd-lect-00001', { type: 'STOP_RECORDING' })).status).toBe(
      403,
    );
    const denied = await env.pool.query(
      "select actor_user_id from audit_log where action = 'denied:studio:control' order by id",
    );
    expect(denied.rows.map((r) => r.actor_user_id)).toEqual([host.id, viewer.id]);
  });

  it('exécute Preview puis Take, de façon idempotente, et persiste l’état', async () => {
    const preview = await command(producer.token, 'cmd-preview-001', {
      type: 'SET_PREVIEW',
      source: { kind: 'scene', id: 'groupe' },
    });
    expect(preview.status).toBe(200);
    expect(preview.body.state.preview).toEqual({ kind: 'scene', id: 'groupe' });
    const take = await command(producer.token, 'cmd-take-0001', {
      type: 'TAKE',
      expectPreviewId: 'groupe',
    });
    expect(take.body.state.program).toEqual({ kind: 'scene', id: 'groupe' });
    const replay = await command(producer.token, 'cmd-take-0001', {
      type: 'TAKE',
      expectPreviewId: 'groupe',
    });
    expect(replay.body.replayed).toBe(true);
    expect(replay.body.state.version).toBe(take.body.state.version);
    const state = await env.call('GET', `${base}/studio`, { token: viewer.token });
    expect(state.body.state.program).toEqual({ kind: 'scene', id: 'groupe' });
    expect((state.body.events as { type: string }[]).map((e) => e.type)).toEqual([
      'PreviewChanged',
      'ProgramSceneChanged',
    ]);
  });

  it('refuse une version attendue périmée et une commande invalide', async () => {
    const stale = await command(
      producer.token,
      'cmd-perime-001',
      { type: 'CUT', source: { kind: 'scene', id: 'focus' } },
      0,
    );
    expect(stale.status).toBe(409);
    expect(stale.body.error.code).toBe('STALE_VERSION');
    expect(
      (await command(producer.token, 'cmd-invalide-01', { type: 'FORMATER_LE_DISQUE' })).status,
    ).toBe(400);
    expect(
      (
        await command(producer.token, 'cmd-source-0001', {
          type: 'CUT',
          source: { kind: 'camion', id: 'x' },
        })
      ).status,
    ).toBe(400);
    expect(
      (
        await env.call('POST', `${base}/studio/commands`, {
          token: producer.token,
          body: { commandId: 'court', command: { type: 'STOP_RECORDING' } },
        })
      ).status,
    ).toBe(400);
  });

  it('plusieurs commandes simultanées se sérialisent sans état incohérent', async () => {
    const before = (await env.call('GET', `${base}/studio`, { token: producer.token })).body.state
      .version as number;
    const results = await Promise.all(
      Array.from({ length: 6 }, (_, i) =>
        command(producer.token, `cmd-course-${String(i).padStart(4, '0')}`, {
          type: 'SHOW_OVERLAY',
          overlayId: `bandeau-${String(i)}`,
        }),
      ),
    );
    expect(results.every((r) => r.status === 200)).toBe(true);
    const after = (await env.call('GET', `${base}/studio`, { token: producer.token })).body.state;
    expect(after.version).toBe(before + 6);
    expect(new Set(after.overlays).size).toBe(6);
    const seqs = (
      await env.pool.query('select seq from studio_events where episode_id = $1 order by seq', [
        episodeId,
      ])
    ).rows.map((r) => r.seq);
    expect(seqs).toEqual(seqs.map((_: number, i: number) => i + 1));
  });

  it('exige le consentement de tous les participants connus avant d’enregistrer (invité et producteur)', async () => {
    const { token } = (
      await env.call('POST', `${base}/invitations`, {
        token: producer.token,
        body: { displayName: 'Invitée' },
      })
    ).body as { token: string };
    await env.call('POST', `/api/invitations/${token}/join`, { body: {} });
    const blocked = await command(producer.token, 'cmd-rec-00001', {
      type: 'START_RECORDING',
      sessionId: 'session-1',
    });
    expect(blocked.status).toBe(409);
    expect(blocked.body.error.code).toBe('CONSENT_REQUIRED');
    // L'invitée consent via son invitation, le producteur via son compte.
    expect(
      (await env.call('POST', `/api/invitations/${token}/consent`, { body: {} })).body.ok,
    ).toBe(true);
    expect(
      (
        await command(producer.token, 'cmd-rec-00002', {
          type: 'START_RECORDING',
          sessionId: 'session-1',
        })
      ).body.error.code,
    ).toBe('CONSENT_REQUIRED');
    expect(
      (await env.call('POST', `${base}/studio/consent`, { token: producer.token })).body.ok,
    ).toBe(true);
    const hostBlocked = await command(producer.token, 'cmd-rec-00003', {
      type: 'START_RECORDING',
      sessionId: 'session-1',
    });
    // L'hôte a rejoint le studio plus haut : son consentement manque aussi.
    expect(hostBlocked.body.error.code).toBe('CONSENT_REQUIRED');
    expect((await env.call('POST', `${base}/studio/consent`, { token: host.token })).body.ok).toBe(
      true,
    );
    const started = await command(producer.token, 'cmd-rec-00004', {
      type: 'START_RECORDING',
      sessionId: 'session-1',
    });
    expect(started.status).toBe(200);
    expect(started.body.state.recording).toMatchObject({
      status: 'RECORDING',
      sessionId: 'session-1',
    });
    expect(
      (
        await command(producer.token, 'cmd-rec-00005', {
          type: 'START_RECORDING',
          sessionId: 'session-2',
        })
      ).body.error.code,
    ).toBe('ALREADY_RECORDING');
    expect(
      (await command(producer.token, 'cmd-rec-00006', { type: 'STOP_RECORDING' })).status,
    ).toBe(200);
  });

  it('un invité ne peut pas consentir pour un autre : le consentement est lié à son identité', async () => {
    const a = (
      await env.call('POST', `${base}/invitations`, {
        token: producer.token,
        body: { displayName: 'A' },
      })
    ).body as { token: string };
    await env.call('POST', `/api/invitations/${a.token}/join`, { body: {} });
    const consent = await env.call('POST', `/api/invitations/${a.token}/consent`, { body: {} });
    expect(consent.body.ok).toBe(true);
    const state = (await env.call('GET', `${base}/studio`, { token: producer.token })).body.state;
    const participantRows = (
      await env.pool.query("select id from participants where display_name = 'A'")
    ).rows;
    expect(Object.keys(state.consents)).toContain(participantRows[0].id);
  });

  it('le stockage refuse de rejouer deux fois la même commande au moment de l’écriture', async () => {
    const store = new PgStudioStore(env.pool);
    const state = await store.load(episodeId);
    const result = {
      ok: true as const,
      state: { ...state, version: state.version + 1, overlays: [...state.overlays, 'doublon'] },
      events: [],
    };
    expect((await store.commit(episodeId, state.version, 'cmd-doublon-001', result)).kind).toBe(
      'OK',
    );
    const again = await store.commit(episodeId, state.version + 1, 'cmd-doublon-001', result);
    expect(again.kind).toBe('DUPLICATE');
    expect((await store.load(episodeId)).version).toBe(state.version + 1);
  });

  it('le studio d’un autre podcast est introuvable', async () => {
    const other = await env.user('autre@example.org');
    const otherPodcast = (
      await env.call('POST', '/api/podcasts', { token: other.token, body: { name: 'Autre' } })
    ).body.podcast.id;
    expect(
      (
        await env.call('GET', `/api/podcasts/${otherPodcast}/episodes/${episodeId}/studio`, {
          token: other.token,
        })
      ).status,
    ).toBe(404);
    expect(
      (
        await env.call('POST', `/api/podcasts/${otherPodcast}/episodes/${episodeId}/studio/token`, {
          token: other.token,
        })
      ).status,
    ).toBe(404);
    expect(
      (
        await env.call(
          'POST',
          `/api/podcasts/${otherPodcast}/episodes/${episodeId}/studio/commands`,
          {
            token: other.token,
            body: { commandId: 'cmd-autre-0001', command: { type: 'STOP_RECORDING' } },
          },
        )
      ).status,
    ).toBe(404);
  });
});

suite('pages de l’application web', () => {
  let env: Env;
  let dir: string;
  beforeAll(async () => {
    dir = await mkdtemp(join(tmpdir(), 'web-'));
    await writeFile(join(dir, 'index.html'), '<!doctype html><title>App</title>');
    await writeFile(join(dir, 'app.js'), 'console.log(1)');
    await writeFile(join(dir, 'secret.json'), '{}');
    await mkdir(join(dir, 'api'));
    await writeFile(join(dir, 'api', 'x.js'), 'console.log(2)');
    env = await createEnv(database ?? '', { WEB_DIR: dir });
  });
  afterAll(async () => {
    await env.close();
  });

  it('sert la page et le script avec la politique de contenu stricte, sans mise en cache', async () => {
    const page = await env.call('GET', '/');
    expect(page.status).toBe(200);
    expect(page.headers['content-type']).toContain('text/html');
    expect(String(page.headers['content-security-policy'])).toContain("script-src 'self'");
    expect(String(page.headers['content-security-policy'])).not.toContain('unsafe-inline');
    expect(page.headers['cache-control']).toBe('no-cache');
    expect(page.headers['x-content-type-options']).toBe('nosniff');
    const script = await env.call('GET', '/app.js');
    expect(script.status).toBe(200);
    expect(String(script.headers['content-type'])).toContain('javascript');
  });

  it('refuse les fichiers hors liste et les traversées de chemin', async () => {
    for (const path of [
      '/secret.json',
      '/../package.json',
      '/%2e%2e/package.json',
      '/.env',
      '/app.js%00.html',
    ])
      expect((await env.call('GET', path)).status).toBe(404);
  });

  it('une route d’API inconnue répond en JSON, jamais par la page', async () => {
    const response = await env.call('GET', '/api/inconnue');
    expect(response.status).toBe(404);
    expect(response.body.error.code).toBe('NOT_FOUND');
    expect(response.headers['content-security-policy']).toBe(
      "default-src 'none'; frame-ancestors 'none'",
    );
  });

  it('un fichier placé sous /api/ n’est jamais servi par les pages', async () => {
    expect((await env.call('GET', '/api/x.js')).status).toBe(404);
    expect((await env.call('GET', '/api/x.js')).body.error.code).toBe('NOT_FOUND');
  });

  it('sans dossier configuré, rien n’est servi', async () => {
    const bare = await createEnv(database ?? '');
    try {
      expect((await bare.call('GET', '/')).status).toBe(404);
    } finally {
      await bare.close();
    }
  });
});
