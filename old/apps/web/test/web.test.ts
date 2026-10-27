import { describe, expect, it } from 'vitest';
import { ApiClient, ApiError, type Episode, type PodcastSummary } from '../src/api.ts';
import {
  Controller,
  type DeviceAccess,
  type RoomConnector,
  type RoomHandle,
} from '../src/controller.ts';
import { describeDeviceError, isDeviceError, summarizeDevices } from '../src/devices.ts';
import { esc, html, raw } from '../src/html.ts';
import { hrefs, parseRoute } from '../src/router.ts';
import { initialState, type AppState } from '../src/state.ts';
import { renderApp } from '../src/views.ts';

const PODCAST = '11111111-2222-4333-8444-555555555555';
const EPISODE = '66666666-7777-4888-9999-000000000000';
const TOKEN = 'a'.repeat(43);
const EVIL = '"><script>alert(1)</script><img src=x onerror=alert(2)>';

describe('gabarits HTML sûrs', () => {
  it('échappe les six caractères dangereux', () => {
    expect(esc(`<>&"'\``)).toBe('&lt;&gt;&amp;&quot;&#39;&#96;');
    expect(esc(42)).toBe('42');
  });

  it('échappe toute valeur interpolée, y compris dans un attribut', () => {
    const out = html`<a title="${EVIL}">${EVIL}</a>`.toString();
    expect(out).not.toContain('<script');
    expect(out).not.toContain('<img');
    expect(out).toContain('&lt;script&gt;');
    expect(out).toContain('title="&quot;&gt;&lt;script&gt;');
  });

  it('laisse passer un gabarit déjà sûr, aplatit les listes, ignore vide et faux', () => {
    const inner = html`<b>${'<i>'}</b>`;
    expect(html`<p>${inner}</p>`.toString()).toBe('<p><b>&lt;i&gt;</b></p>');
    expect(
      flat(
        html`<ul>
          ${['<a>', html`<li>x</li>`]}
        </ul>`,
      ),
    ).toBe('<ul>&lt;a&gt;<li>x</li></ul>');
    expect(html`[${null}|${undefined}|${false}|${''}]`.toString()).toBe('[|||]');
    expect(html`${0}`.toString()).toBe('0');
  });

  it('`raw` n’est pas échappé : réservé aux littéraux du code', () => {
    expect(html`<p ${raw('disabled')}></p>`.toString()).toContain('<p disabled>');
  });
});

describe('routes', () => {
  it('reconnaît chaque page', () => {
    expect(parseRoute('')).toEqual({ name: 'home' });
    expect(parseRoute('#/')).toEqual({ name: 'home' });
    expect(parseRoute('#/login')).toEqual({ name: 'login' });
    expect(parseRoute(`#/p/${PODCAST}`)).toEqual({ name: 'podcast', podcastId: PODCAST });
    expect(parseRoute(`#/p/${PODCAST}/e/${EPISODE}`)).toEqual({
      name: 'episode',
      podcastId: PODCAST,
      episodeId: EPISODE,
    });
    expect(parseRoute(`#/p/${PODCAST}/e/${EPISODE}/studio`)).toEqual({
      name: 'studio',
      podcastId: PODCAST,
      episodeId: EPISODE,
    });
    expect(parseRoute(`#/join/${TOKEN}`)).toEqual({ name: 'guest', token: TOKEN });
    expect(parseRoute(`#/p/${PODCAST}?x=1`)).toEqual({ name: 'podcast', podcastId: PODCAST });
  });

  it.each([
    '#/p/pas-un-uuid',
    `#/p/${PODCAST}/e/x`,
    '#/join/court',
    `#/join/${'a'.repeat(44)}`,
    '#/admin',
    `#/p/${PODCAST}/../x`,
    '#/p/<script>',
  ])('refuse %s sans l’envoyer au serveur', (hash) => {
    expect(parseRoute(hash)).toEqual({ name: 'not-found' });
  });

  it('les liens produits sont relus à l’identique', () => {
    expect(parseRoute(hrefs.studio(PODCAST, EPISODE))).toEqual({
      name: 'studio',
      podcastId: PODCAST,
      episodeId: EPISODE,
    });
    expect(parseRoute(hrefs.guest(TOKEN))).toEqual({ name: 'guest', token: TOKEN });
  });
});

describe('device check', () => {
  it.each([
    ['NotAllowedError', /bloqué/],
    ['NotFoundError', /Aucune caméra/],
    ['NotReadableError', /autre application/],
    ['OverconstrainedError', /qualité/],
    ['AbortError', /interrompu/],
    ['Autre', /Impossible d'accéder/],
  ])('%s donne un message utile', (name, pattern) => {
    expect(describeDeviceError({ name })).toMatch(pattern);
  });

  it('distingue une erreur d’appareil d’une erreur réseau', () => {
    expect(isDeviceError({ name: 'NotAllowedError' })).toBe(true);
    expect(isDeviceError(new Error('réseau'))).toBe(false);
    expect(isDeviceError(null)).toBe(false);
  });

  it('résume les appareils détectés', () => {
    expect(
      summarizeDevices([{ kind: 'videoinput' }, { kind: 'audioinput' }, { kind: 'audiooutput' }]),
    ).toEqual({ cameras: 1, microphones: 1, ok: true, problems: [] });
    expect(summarizeDevices([{ kind: 'audioinput' }]).problems).toEqual([
      'Aucune caméra détectée.',
    ]);
    expect(summarizeDevices([]).problems).toHaveLength(2);
  });
});

const podcast = (role: string): PodcastSummary => ({ id: PODCAST, name: 'Mon podcast', role });
const segment = (id: string, title: string, extra: object = {}) => ({
  id,
  key: id,
  title,
  objective: 'Objectif',
  notes: '',
  questions: [],
  targetDurationSec: 600,
  status: 'TODO' as const,
  ...extra,
});
const episode = (): Episode => ({
  id: EPISODE,
  podcastId: PODCAST,
  title: 'Mon épisode',
  date: '2026-10-06',
  revision: 3,
  segments: [
    segment('b', 'SÉQUENCE B'),
    segment('a', 'INTRO', { notes: `</textarea>${EVIL}`, status: 'READY' }),
  ],
  scenes: [],
  rundown: [
    { order: 1, segmentId: 'b' },
    { order: 0, segmentId: 'a' },
  ],
});
const state = (patch: Partial<AppState>): AppState => ({
  ...initialState(),
  user: { id: 'u', email: 'u@x.fr', displayName: 'Lou' },
  podcasts: { status: 'ready', data: [podcast('PRODUCER')] },
  ...patch,
});
const render = (s: AppState): string => renderApp(s).toString();
/** Compare sans tenir compte de la mise en forme (Prettier réindente les gabarits `html`). */
const flat = (value: { toString(): string }): string =>
  value.toString().replace(/\s+/g, ' ').replace(/> /g, '>').replace(/ </g, '<').trim();

describe('vues : états et sécurité', () => {
  it('chargement, connexion, accueil vide, erreur avec référence', () => {
    expect(render({ ...initialState(), user: undefined })).toContain('Chargement');
    expect(render({ ...initialState(), user: null })).toContain('data-form="login"');
    expect(render({ ...initialState(), user: null })).not.toContain('Se déconnecter');
    expect(render(state({ podcasts: { status: 'ready', data: [] } }))).toContain('aucun podcast');
    const failed = render(
      state({ podcasts: { status: 'error', message: 'Panne', correlationId: 'corr-0001' } }),
    );
    expect(failed).toContain('role="alert"');
    expect(failed).toContain('corr-0001');
    expect(render(state({ podcasts: { status: 'loading' } }))).toContain('Chargement');
  });

  it('les noms venant du serveur ne deviennent jamais du balisage', () => {
    const out = render(
      state({
        user: { id: 'u', email: 'u@x.fr', displayName: EVIL },
        podcasts: { status: 'ready', data: [{ id: PODCAST, name: EVIL, role: 'ADMIN' }] },
        flash: { kind: 'error', text: EVIL },
      }),
    );
    for (const forbidden of ['<script', '<img']) expect(out).not.toContain(forbidden);
    expect(out).toContain('&lt;script&gt;');
  });

  it('page épisodes : le formulaire de création est réservé aux rôles autorisés', () => {
    const route = { name: 'podcast' as const, podcastId: PODCAST };
    const episodes = {
      status: 'ready' as const,
      data: [{ id: EPISODE, title: 'Ep', date: '2026-10-06', status: 'DRAFT', revision: 1 }],
    };
    expect(render(state({ route, episodes }))).toContain('data-form="create-episode"');
    const viewer = render(
      state({ route, episodes, podcasts: { status: 'ready', data: [podcast('VIEWER')] } }),
    );
    expect(viewer).not.toContain('data-form="create-episode"');
    expect(viewer).toContain('ne permet pas');
    expect(render(state({ route, episodes: { status: 'ready', data: [] } }))).toContain(
      'Aucun épisode',
    );
  });

  it('page épisode : séquences dans l’ordre du conducteur, notes échappées, droits respectés', () => {
    const route = { name: 'episode' as const, podcastId: PODCAST, episodeId: EPISODE };
    const out = render(state({ route, episode: { status: 'ready', data: episode() } }));
    expect(out.indexOf('INTRO')).toBeLessThan(out.indexOf('SÉQUENCE B'));
    expect(out).not.toContain('<script');
    expect(out).toContain('&lt;/textarea&gt;');
    expect(out).toContain('data-form="invite"');
    expect(out).toContain('Ouvrir le studio');
    const viewer = render(
      state({
        route,
        episode: { status: 'ready', data: episode() },
        podcasts: { status: 'ready', data: [podcast('VIEWER')] },
      }),
    );
    expect(viewer).not.toContain('<button type="submit">Enregistrer</button>');
    expect(viewer).toContain('readonly');
    expect(viewer).not.toContain('data-form="invite"');
    expect(viewer).not.toContain('Ouvrir le studio');
  });

  it('liens d’invitation affichés avec un avertissement', () => {
    const route = { name: 'episode' as const, podcastId: PODCAST, episodeId: EPISODE };
    const out = render(
      state({
        route,
        episode: { status: 'ready', data: episode() },
        invitationLinks: [`https://h/#/join/${TOKEN}`],
      }),
    );
    expect(out).toContain(`https://h/#/join/${TOKEN}`);
    expect(out).toContain("qu'une fois");
  });

  it('studio : la régie n’apparaît que pour un producteur ; l’état d’enregistrement est lisible', () => {
    const route = { name: 'studio' as const, podcastId: PODCAST, episodeId: EPISODE };
    const info = {
      status: 'ready' as const,
      data: {
        version: 4,
        program: { kind: 'scene', id: 'groupe' },
        preview: null,
        overlays: [],
        recording: { status: 'RECORDING' as const, sessionId: 's' },
        consents: {},
      },
    };
    const producer = render(state({ route, studio: { ...initialState().studio, info } }));
    expect(producer).toContain('data-action="rec-stop"');
    expect(producer).not.toContain('data-action="rec-start"');
    expect(producer).toContain('en cours');
    const host = render(
      state({
        route,
        studio: { ...initialState().studio, info },
        podcasts: { status: 'ready', data: [podcast('HOST')] },
      }),
    );
    expect(host).not.toContain('data-action="take"');
    expect(host).toContain('Seul un producteur');
  });

  it('page invité : consentement explicite, nom imposé par l’invitation', () => {
    const route = { name: 'guest' as const, token: TOKEN };
    const info = {
      status: 'ready' as const,
      data: {
        podcastName: EVIL,
        episodeTitle: 'Ep',
        role: 'GUEST' as const,
        displayName: 'Camille',
        expiresAt: '2026-10-09',
      },
    };
    const out = render({
      ...initialState(),
      route,
      user: null,
      guest: { ...initialState().guest, info },
    });
    expect(out).toContain('name="consent"');
    expect(out).not.toContain('name="consent" checked');
    expect(out).toContain('value="Camille"');
    expect(out).toContain('readonly');
    expect(out).not.toContain('<script');
    const bad = render({
      ...initialState(),
      route,
      user: null,
      guest: {
        ...initialState().guest,
        info: {
          status: 'error',
          message: 'Invitation introuvable ou expirée',
          correlationId: null,
        },
      },
    });
    expect(bad).toContain('introuvable ou expirée');
  });

  it('aucune sortie ne contient de gestionnaire en ligne, de script ni d’URL javascript:', () => {
    const route = { name: 'episode' as const, podcastId: PODCAST, episodeId: EPISODE };
    const outputs = [
      render({ ...initialState(), user: null }),
      render(state({})),
      render(state({ route, episode: { status: 'ready', data: episode() } })),
      render(state({ route: { name: 'studio', podcastId: PODCAST, episodeId: EPISODE } })),
      render(state({ route: { name: 'not-found' } })),
    ];
    for (const out of outputs) {
      expect(out).not.toMatch(/<[^<>]*\son[a-z]+\s*=/i);
      expect(out).not.toMatch(/<script/i);
      expect(out).not.toMatch(/javascript:/i);
      expect(out).not.toContain('style=');
    }
  });
});

// --- Contrôleur avec une fausse API (fetch) -------------------------------------------------------------------

interface Call {
  method: string;
  path: string;
  body: unknown;
  init: RequestInit;
}
type Handler = (
  call: Call,
) => { status?: number; body?: unknown } | Promise<{ status?: number; body?: unknown }>;

function harness(routes: Record<string, Handler>) {
  const calls: Call[] = [];
  const fetchFake = (async (input: string, init: RequestInit = {}) => {
    const method = init.method ?? 'GET';
    const call: Call = {
      method,
      path: input,
      body: typeof init.body === 'string' ? JSON.parse(init.body) : undefined,
      init,
    };
    calls.push(call);
    const handler = routes[`${method} ${input}`];
    if (!handler)
      return new Response(
        JSON.stringify({
          error: { code: 'NOT_FOUND', message: 'Introuvable' },
          correlationId: 'corr-x',
        }),
        { status: 404 },
      );
    const result = await handler(call);
    return new Response(result.body === undefined ? null : JSON.stringify(result.body), {
      status: result.status ?? 200,
    });
  }) as unknown as typeof fetch;
  let id = 0;
  const api = new ApiClient({
    fetch: fetchFake,
    newId: () => `id-${String(++id).padStart(8, '0')}`,
  });
  const roomEvents: string[] = [];
  const room: RoomHandle = {
    participants: () => ['Lou (vous)', 'Camille'],
    disconnect: () => {
      roomEvents.push('disconnect');
      return Promise.resolve();
    },
    onChange: () => undefined,
  };
  let connectError: Error | null = null;
  const rooms: RoomConnector = {
    connect: () => {
      roomEvents.push('connect');
      return connectError ? Promise.reject(connectError) : Promise.resolve(room);
    },
  };
  let deviceError: Error | null = null;
  const devices: DeviceAccess = {
    enumerate: () => Promise.resolve([{ kind: 'videoinput' }, { kind: 'audioinput' }]),
    test: () => (deviceError ? Promise.reject(deviceError) : Promise.resolve()),
  };
  const navigations: string[] = [];
  const controller = new Controller({
    api,
    rooms,
    devices,
    origin: 'https://studio.example',
    today: () => '2026-10-06',
    navigateTo: (hash) => navigations.push(hash),
  });
  return {
    controller,
    api,
    calls,
    roomEvents,
    navigations,
    setConnectError: (e: Error | null) => (connectError = e),
    setDeviceError: (e: Error | null) => (deviceError = e),
  };
}

const ME = {
  user: { id: 'u', email: 'u@x.fr', displayName: 'Lou' },
  podcasts: [podcast('PRODUCER')],
};
const STUDIO_STATE = {
  version: 2,
  program: null,
  preview: { kind: 'scene', id: 'groupe' },
  overlays: [],
  recording: { status: 'IDLE' as const },
  consents: {},
};

describe('client d’API', () => {
  it('envoie le cookie de même origine, un en-tête JSON seulement avec un corps, et ne touche à aucun secret', async () => {
    const h = harness({
      'GET /api/me': () => ({ body: ME }),
      'POST /api/podcasts': () => ({ status: 201, body: { podcast: podcast('ADMIN') } }),
    });
    await h.api.me();
    await h.api.createPodcast('X');
    expect(h.calls[0]?.init.credentials).toBe('same-origin');
    expect(h.calls[0]?.init.headers).toEqual({});
    expect(h.calls[1]?.init.headers).toEqual({ 'content-type': 'application/json' });
    expect(JSON.stringify(h.calls)).not.toMatch(/authorization|bearer/i);
  });

  it('traduit une erreur du serveur avec son code et sa référence', async () => {
    const h = harness({
      'GET /api/me': () => ({
        status: 403,
        body: {
          error: { code: 'FORBIDDEN', message: 'Droits insuffisants', details: ['x'] },
          correlationId: 'corr-9',
        },
      }),
    });
    const error = await h.api.me().catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      status: 403,
      code: 'FORBIDDEN',
      correlationId: 'corr-9',
      details: ['x'],
    });
  });

  it('gère une réponse qui n’est pas du JSON', async () => {
    const fetchBad = (() =>
      Promise.resolve(
        new Response('<html>502</html>', { status: 502 }),
      )) as unknown as typeof fetch;
    const api = new ApiClient({ fetch: fetchBad, newId: () => 'x' });
    await expect(api.me()).rejects.toMatchObject({ status: 502, code: 'UNKNOWN' });
  });
});

describe('contrôleur', () => {
  it('démarre sans session : page de connexion ; avec session : accueil chargé', async () => {
    const anonymous = harness({
      'GET /api/me': () => ({
        status: 401,
        body: { error: { code: 'UNAUTHENTICATED', message: 'Authentification requise' } },
      }),
    });
    await anonymous.controller.start('#/');
    expect(anonymous.controller.state.user).toBeNull();
    const logged = harness({ 'GET /api/me': () => ({ body: ME }) });
    await logged.controller.start('#/');
    expect(logged.controller.state.user?.displayName).toBe('Lou');
    expect(logged.controller.state.podcasts).toEqual({ status: 'ready', data: ME.podcasts });
  });

  it('connexion réussie puis échec : message sobre, état propre, jamais d’exception', async () => {
    let ok = false;
    const h = harness({
      'POST /api/auth/login': () =>
        ok
          ? { body: { user: ME.user } }
          : {
              status: 401,
              body: {
                error: {
                  code: 'INVALID_CREDENTIALS',
                  message: 'Adresse ou mot de passe incorrect',
                },
                correlationId: 'corr-1',
              },
            },
      'GET /api/me': () => ({ body: ME }),
    });
    h.controller.state = { ...h.controller.state, user: null };
    await h.controller.submit('login', { email: 'a@b.fr', password: 'x' });
    expect(h.controller.state.user).toBeNull();
    expect(h.controller.state.flash).toMatchObject({ kind: 'error' });
    expect(h.controller.state.flash?.text).toContain('Adresse ou mot de passe incorrect');
    expect(h.controller.state.busy).toBe(false);
    ok = true;
    await h.controller.submit('login', { email: 'a@b.fr', password: 'x' });
    expect(h.controller.state.user?.email).toBe('u@x.fr');
    expect(h.navigations).toEqual(['#/']);
  });

  it('une seule action à la fois : la seconde, lancée pendant la première, est ignorée', async () => {
    let release: () => void = () => undefined;
    const gate = new Promise<void>((resolve) => {
      release = resolve;
    });
    const h = harness({
      'POST /api/podcasts': async () => {
        await gate;
        return { status: 201, body: { podcast: podcast('ADMIN') } };
      },
    });
    h.controller.state = { ...h.controller.state, user: ME.user };
    const first = h.controller.submit('create-podcast', { name: 'A' });
    const second = h.controller.submit('create-podcast', { name: 'A' });
    release();
    await Promise.all([first, second]);
    expect(h.calls.filter((c) => c.method === 'POST')).toHaveLength(1);
  });

  it('la création d’épisode garde la même clé d’idempotence pour la même demande, même après un échec', async () => {
    let attempt = 0;
    const h = harness({
      [`POST /api/podcasts/${PODCAST}/episodes`]: () => {
        attempt += 1;
        return attempt === 1
          ? {
              status: 500,
              body: {
                error: { code: 'INTERNAL', message: 'Erreur interne' },
                correlationId: 'corr-2',
              },
            }
          : { status: 201, body: { episode: episode(), created: true } };
      },
      [`GET /api/podcasts/${PODCAST}/episodes`]: () => ({ body: { episodes: [] } }),
    });
    h.controller.state = {
      ...h.controller.state,
      user: ME.user,
      route: { name: 'podcast', podcastId: PODCAST },
    };
    await h.controller.submit('create-episode', { title: 'Mon épisode', date: '2026-10-06' });
    expect(h.controller.state.flash?.text).toContain('corr-2');
    await h.controller.submit('create-episode', { title: 'Mon épisode', date: '2026-10-06' });
    await h.controller.submit('create-episode', { title: 'Autre épisode', date: '2026-10-06' });
    const keys = h.calls
      .filter((c) => c.method === 'POST')
      .map((c) => (c.body as { idempotencyKey: string }).idempotencyKey);
    expect(keys[0]).toBe(keys[1]);
    expect(keys[2]).not.toBe(keys[0]);
  });

  it('l’enregistrement d’une séquence envoie la révision connue et signale un conflit', async () => {
    const url = `PATCH /api/podcasts/${PODCAST}/episodes/${EPISODE}/segments/a`;
    let conflict = false;
    const h = harness({
      [url]: () =>
        conflict
          ? {
              status: 409,
              body: {
                error: { code: 'CONFLICT', message: "L'épisode a changé depuis votre lecture" },
              },
            }
          : { body: { episode: { ...episode(), revision: 4 } } },
    });
    h.controller.state = {
      ...h.controller.state,
      user: ME.user,
      route: { name: 'episode', podcastId: PODCAST, episodeId: EPISODE },
      episode: { status: 'ready', data: episode() },
    };
    await h.controller.submit('segment', { segmentId: 'a', notes: 'note', status: 'IN_PROGRESS' });
    expect(h.calls[0]?.body).toEqual({
      expectedRevision: 3,
      patch: { notes: 'note', status: 'IN_PROGRESS' },
    });
    expect(h.controller.state.episode).toMatchObject({ status: 'ready', data: { revision: 4 } });
    conflict = true;
    await h.controller.submit('segment', { segmentId: 'a', notes: 'autre', status: 'WTF' });
    expect(h.calls[1]?.body).toEqual({ expectedRevision: 4, patch: { notes: 'autre' } });
    expect(h.controller.state.flash?.text).toContain('a changé');
    expect(h.controller.state.episode).toMatchObject({ status: 'ready', data: { revision: 4 } });
  });

  it('un lien d’invitation est construit avec l’adresse du site et le jeton reçu', async () => {
    const h = harness({
      [`POST /api/podcasts/${PODCAST}/episodes/${EPISODE}/invitations`]: () => ({
        status: 201,
        body: { token: TOKEN, expiresAt: '2026-10-09' },
      }),
    });
    h.controller.state = {
      ...h.controller.state,
      user: ME.user,
      route: { name: 'episode', podcastId: PODCAST, episodeId: EPISODE },
    };
    await h.controller.submit('invite', { displayName: ' Camille ' });
    expect(h.controller.state.invitationLinks).toEqual([`https://studio.example#/join/${TOKEN}`]);
    expect(h.calls[0]?.body).toEqual({ role: 'GUEST', displayName: 'Camille' });
  });

  it('studio : régie, message de consentement, version périmée rechargée, session expirée', async () => {
    const base = `/api/podcasts/${PODCAST}/episodes/${EPISODE}/studio`;
    let mode: 'consent' | 'stale' | 'expired' | 'ok' = 'consent';
    const h = harness({
      [`GET ${base}`]: () => ({ body: { state: STUDIO_STATE } }),
      [`POST ${base}/commands`]: () => {
        if (mode === 'consent')
          return {
            status: 409,
            body: { ok: false, error: { code: 'CONSENT_REQUIRED', message: 'x' } },
          };
        if (mode === 'stale')
          return {
            status: 409,
            body: { ok: false, error: { code: 'STALE_VERSION', message: 'x' } },
          };
        if (mode === 'expired')
          return { status: 401, body: { error: { code: 'UNAUTHENTICATED', message: 'x' } } };
        return {
          body: {
            ok: true,
            state: {
              ...STUDIO_STATE,
              version: 3,
              recording: { status: 'RECORDING', sessionId: 's' },
            },
          },
        };
      },
    });
    h.controller.state = {
      ...h.controller.state,
      user: ME.user,
      route: { name: 'studio', podcastId: PODCAST, episodeId: EPISODE },
    };
    await h.controller.navigate(`#/p/${PODCAST}/e/${EPISODE}/studio`);
    expect(h.controller.knownStudioVersion).toBe(2);
    await h.controller.act('rec-start');
    expect(h.controller.state.flash?.text).toContain('consentir');
    mode = 'stale';
    const before = h.calls.length;
    await h.controller.act('take');
    expect(h.calls.length).toBeGreaterThan(before);
    expect(h.controller.state.flash?.text).toContain('rechargé');
    mode = 'ok';
    await h.controller.act('rec-start');
    expect(h.controller.state.studio.info).toMatchObject({ status: 'ready', data: { version: 3 } });
    expect(h.controller.knownStudioVersion).toBe(3);
    mode = 'expired';
    await h.controller.act('rec-stop');
    expect(h.controller.state.user).toBeNull();
    expect(h.controller.state.flash?.text).toContain('expiré');
  });

  it('« passer à l’antenne » sans Preview ne contacte pas le serveur', async () => {
    const h = harness({});
    h.controller.state = {
      ...h.controller.state,
      user: ME.user,
      route: { name: 'studio', podcastId: PODCAST, episodeId: EPISODE },
      studio: {
        ...h.controller.state.studio,
        info: { status: 'ready', data: { ...STUDIO_STATE, preview: null } },
      },
    };
    await h.controller.act('take');
    expect(h.calls).toHaveLength(0);
    expect(h.controller.state.flash?.text).toContain('Preview');
  });

  it('rejoindre la salle : jeton, connexion, participants ; échec réseau signalé sans planter', async () => {
    const base = `/api/podcasts/${PODCAST}/episodes/${EPISODE}/studio`;
    const h = harness({
      [`POST ${base}/token`]: () => ({
        body: { participantId: 'p-1', livekit: { url: 'ws://x', room: 'ep-1', token: 't' } },
      }),
    });
    h.controller.state = {
      ...h.controller.state,
      user: ME.user,
      route: { name: 'studio', podcastId: PODCAST, episodeId: EPISODE },
    };
    await h.controller.act('studio-connect');
    expect(h.controller.state.studio.room).toEqual({
      status: 'connected',
      participants: ['Lou (vous)', 'Camille'],
      message: null,
    });
    expect(h.controller.state.studio.participantId).toBe('p-1');
    h.setConnectError(new Error('réseau'));
    await h.controller.act('studio-connect');
    expect(h.controller.state.studio.room.status).toBe('error');
    expect(h.controller.state.studio.room.message).toContain('réseau');
  });

  it('invité : sans consentement rien n’est envoyé ; avec, rejoint puis consent puis se connecte', async () => {
    const h = harness({
      [`GET /api/invitations/${TOKEN}`]: () => ({
        body: {
          invitation: {
            podcastName: 'P',
            episodeTitle: 'E',
            role: 'GUEST',
            displayName: null,
            expiresAt: '2026-10-09',
          },
        },
      }),
      [`POST /api/invitations/${TOKEN}/join`]: () => ({
        body: {
          participant: { id: 'p-2', displayName: 'Sam' },
          livekit: { url: 'ws://x', room: 'r', token: 't' },
        },
      }),
      [`POST /api/invitations/${TOKEN}/consent`]: () => ({ body: { ok: true } }),
    });
    await h.controller.start(`#/join/${TOKEN}`);
    expect(h.controller.state.user).toBeNull();
    expect(h.controller.state.guest.info.status).toBe('ready');
    await h.controller.submit('guest-join', { displayName: 'Sam' });
    expect(h.controller.state.flash?.text).toContain('consentement');
    expect(h.calls.filter((c) => c.method === 'POST')).toHaveLength(0);
    await h.controller.submit('guest-join', { displayName: 'Sam', consent: 'on' });
    expect(h.calls.filter((c) => c.method === 'POST').map((c) => c.path)).toEqual([
      `/api/invitations/${TOKEN}/join`,
      `/api/invitations/${TOKEN}/consent`,
    ]);
    expect(h.controller.state.guest.room.status).toBe('connected');
    expect(h.roomEvents).toEqual(['connect']);
  });

  it('invitation expirée : message clair, aucune connexion', async () => {
    const h = harness({
      [`GET /api/invitations/${TOKEN}`]: () => ({
        status: 404,
        body: { error: { code: 'NOT_FOUND', message: 'Invitation introuvable ou expirée' } },
      }),
    });
    await h.controller.start(`#/join/${TOKEN}`);
    expect(h.controller.state.guest.info).toMatchObject({
      status: 'error',
      message: 'Invitation introuvable ou expirée',
    });
  });

  it('device check : succès, appareil bloqué, erreur inconnue', async () => {
    const h = harness({});
    h.controller.state = { ...h.controller.state, route: { name: 'guest', token: TOKEN } };
    await h.controller.act('device-check');
    expect(h.controller.state.guest.devices?.ok).toBe(true);
    expect(h.controller.state.guest.deviceMessage).toContain('Caméra et micro détectés');
    h.setDeviceError(Object.assign(new Error('bloqué'), { name: 'NotAllowedError' }));
    await h.controller.act('device-check');
    expect(h.controller.state.guest.devices).toBeNull();
    expect(h.controller.state.guest.deviceMessage).toContain('bloqué');
  });

  it('déconnexion : quitte les salles et efface les données de la session', async () => {
    const base = `/api/podcasts/${PODCAST}/episodes/${EPISODE}/studio`;
    const h = harness({
      [`POST ${base}/token`]: () => ({
        body: { participantId: 'p-1', livekit: { url: 'ws://x', room: 'r', token: 't' } },
      }),
      'POST /api/auth/logout': () => ({ body: { ok: true } }),
    });
    h.controller.state = {
      ...h.controller.state,
      user: ME.user,
      podcasts: { status: 'ready', data: ME.podcasts },
      route: { name: 'studio', podcastId: PODCAST, episodeId: EPISODE },
      invitationLinks: ['x'],
    };
    await h.controller.act('studio-connect');
    await h.controller.act('logout');
    expect(h.roomEvents).toEqual(['connect', 'disconnect']);
    expect(h.controller.state.user).toBeNull();
    expect(h.controller.state.podcasts.status).toBe('idle');
    expect(h.controller.state.invitationLinks).toEqual([]);
  });

  it('une session expirée pendant une navigation renvoie à la connexion', async () => {
    const h = harness({
      [`GET /api/podcasts/${PODCAST}/episodes`]: () => ({
        status: 401,
        body: { error: { code: 'UNAUTHENTICATED', message: 'Authentification requise' } },
      }),
    });
    h.controller.state = { ...h.controller.state, user: ME.user };
    await h.controller.navigate(`#/p/${PODCAST}`);
    expect(h.controller.state.user).toBeNull();
    expect(h.controller.state.flash?.text).toContain('expiré');
  });

  it('une page non autorisée donne une erreur lisible, pas un écran vide', async () => {
    const h = harness({
      [`GET /api/podcasts/${PODCAST}/episodes`]: () => ({
        status: 404,
        body: { error: { code: 'NOT_FOUND', message: 'Introuvable' }, correlationId: 'corr-404' },
      }),
    });
    h.controller.state = { ...h.controller.state, user: ME.user };
    await h.controller.navigate(`#/p/${PODCAST}`);
    expect(h.controller.state.episodes).toEqual({
      status: 'error',
      message: 'Introuvable',
      correlationId: 'corr-404',
    });
    expect(render(h.controller.state)).toContain('corr-404');
  });
});
