import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { WebSocket } from 'ws';
import * as Y from 'yjs';
import {
  CLOSE_REVOKED,
  CLOSE_UNAUTHORIZED,
  CollabClient,
  CollabServer,
  InMemoryDocumentStore,
  type Authorize,
} from '../src/index.ts';

const DOC = 'presentation-1';

/** Jetons de test : « jeton-<utilisateur>-<droit> ». En production, un jeton signé vérifié par l'API. */
const authorize: Authorize = (token) => {
  const match = /^jeton-(\w+)-(read|write)$/.exec(token);
  if (!match?.[1] || !match[2]) return null;
  return { userId: match[1], access: match[2] as 'read' | 'write' };
};

const until = async (
  condition: () => boolean | Promise<boolean>,
  timeoutMs = 5000,
): Promise<void> => {
  const startedAt = Date.now();
  while (!(await condition())) {
    if (Date.now() - startedAt > timeoutMs) throw new Error('Condition non remplie dans le délai');
    await new Promise((resolve) => setTimeout(resolve, 10));
  }
};

let server: CollabServer;
let store: InMemoryDocumentStore;
let port: number;
const clients: CollabClient[] = [];

const newClient = (
  user: string,
  access: 'read' | 'write' = 'write',
  options: { autoPong?: boolean } = {},
): CollabClient => {
  const client = new CollabClient({
    url: `ws://127.0.0.1:${String(port)}/collab/${DOC}?token=jeton-${user}-${access}`,
    reconnectDelayMs: 50,
    ...options,
  });
  clients.push(client);
  return client;
};

async function startServer(
  options: {
    pingIntervalMs?: number;
    autosaveMs?: number;
    maxPayloadBytes?: number;
    allowedOrigins?: readonly string[];
  } = {},
): Promise<void> {
  store = new InMemoryDocumentStore();
  server = new CollabServer({ authorize, store, pingIntervalMs: 200, autosaveMs: 50, ...options });
  port = await server.listen();
}

beforeEach(async () => {
  await startServer();
});

afterEach(async () => {
  for (const client of clients.splice(0)) client.destroy();
  await server.close();
});

describe('propagation sans rafraîchissement (AC-COLLAB-001, AC-HTML-002)', () => {
  it('une modification de A apparaît chez B', async () => {
    const [a, b] = [newClient('ana'), newClient('ben')];
    a.connect();
    b.connect();
    await Promise.all([a.whenSynced(), b.whenSynced()]);
    a.doc.getText('code').insert(0, '<h1>Bonjour</h1>');
    await until(() => b.doc.getText('code').toJSON() === '<h1>Bonjour</h1>');
  });

  it('mesure la latence de propagation locale sur 200 modifications', async () => {
    const [a, b] = [newClient('ana'), newClient('ben')];
    a.connect();
    b.connect();
    await Promise.all([a.whenSynced(), b.whenSynced()]);
    const latencies: number[] = [];
    for (let i = 0; i < 200; i++) {
      const startedAt = performance.now();
      a.doc.getText('code').insert(a.doc.getText('code').length, 'x');
      await until(() => b.doc.getText('code').length === i + 1, 2000);
      latencies.push(performance.now() - startedAt);
    }
    latencies.sort((x, y) => x - y);
    const p95 = latencies[Math.floor(latencies.length * 0.95)] ?? Infinity;
    // Sur ce poste, boucle locale : le but est de détecter une régression grossière, pas de promettre un SLO.
    expect(p95).toBeLessThan(250);
  });
});

describe('modifications simultanées (AC-COLLAB-002)', () => {
  it('ne perd aucune modification de texte et converge', async () => {
    const [a, b] = [newClient('ana'), newClient('ben')];
    a.connect();
    b.connect();
    await Promise.all([a.whenSynced(), b.whenSynced()]);
    a.doc.getText('code').insert(0, 'base');
    await until(() => b.doc.getText('code').toJSON() === 'base');
    a.doc.getText('code').insert(0, 'AAA ');
    b.doc.getText('code').insert(4, ' BBB');
    await until(
      () =>
        a.doc.getText('code').toJSON() === b.doc.getText('code').toJSON() &&
        a.doc.getText('code').length === 'AAA base BBB'.length,
    );
    const final = a.doc.getText('code').toJSON();
    expect(final).toContain('AAA');
    expect(final).toContain('BBB');
    expect(final).toContain('base');
  });

  it('fusionne des ajouts simultanés à une liste', async () => {
    const [a, b] = [newClient('ana'), newClient('ben')];
    a.connect();
    b.connect();
    await Promise.all([a.whenSynced(), b.whenSynced()]);
    a.doc.getArray<string>('slides').push(['a1', 'a2']);
    b.doc.getArray<string>('slides').push(['b1', 'b2']);
    await until(
      () => a.doc.getArray('slides').length === 4 && b.doc.getArray('slides').length === 4,
    );
    expect(a.doc.getArray('slides').toJSON()).toEqual(b.doc.getArray('slides').toJSON());
    expect([...(a.doc.getArray<string>('slides').toJSON() as string[])].sort()).toEqual([
      'a1',
      'a2',
      'b1',
      'b2',
    ]);
  });

  it('converge sur une même valeur quand deux personnes changent la même clé', async () => {
    const [a, b] = [newClient('ana'), newClient('ben')];
    a.connect();
    b.connect();
    await Promise.all([a.whenSynced(), b.whenSynced()]);
    a.doc.getMap<string>('meta').set('titre', 'Titre de Ana');
    b.doc.getMap<string>('meta').set('titre', 'Titre de Ben');
    await until(() => a.doc.getMap('meta').get('titre') === b.doc.getMap('meta').get('titre'));
    expect(['Titre de Ana', 'Titre de Ben']).toContain(a.doc.getMap('meta').get('titre'));
  });

  it('converge après 2 000 modifications entrelacées de trois personnes', async () => {
    const people = [newClient('ana'), newClient('ben'), newClient('chloe')];
    for (const person of people) person.connect();
    await Promise.all(people.map((p) => p.whenSynced()));
    for (let i = 0; i < 2000; i++) {
      const person = people[i % 3];
      if (!person) throw new Error('participant manquant');
      const text = person.doc.getText('code');
      text.insert(Math.min(text.length, (i * 7) % (text.length + 1)), String(i % 10));
    }
    await until(() => {
      const lengths = people.map((p) => p.doc.getText('code').length);
      const same = new Set(people.map((p) => p.doc.getText('code').toJSON())).size === 1;
      return same && lengths[0] === 2000;
    }, 15_000);
    expect(people[0]?.doc.getText('code').length).toBe(2000);
  }, 30_000);
});

describe('reconnexion et travail hors ligne (AC-COLLAB-003, AC-RECOVERY-005)', () => {
  it('fusionne ce qui a été écrit pendant la coupure, des deux côtés', async () => {
    const [a, b] = [newClient('ana'), newClient('ben')];
    a.connect();
    b.connect();
    await Promise.all([a.whenSynced(), b.whenSynced()]);
    a.doc.getText('code').insert(0, 'début');
    await until(() => b.doc.getText('code').toJSON() === 'début');

    b.dropConnection();
    await until(() => b.status === 'disconnected');
    a.doc.getText('code').insert(0, 'A: ');
    b.doc.getText('code').insert(b.doc.getText('code').length, ' :B');
    expect(b.pendingOfflineBytes).toBeGreaterThan(0);

    await until(() => b.status === 'connected' && b.pendingOfflineBytes === 0);
    await until(() => a.doc.getText('code').toJSON() === b.doc.getText('code').toJSON());
    expect(a.doc.getText('code').toJSON()).toBe('A: début :B');
  });

  it('reprend l’état courant après une longue absence', async () => {
    const [a, b] = [newClient('ana'), newClient('ben')];
    a.connect();
    b.connect();
    await Promise.all([a.whenSynced(), b.whenSynced()]);
    b.close();
    for (let i = 0; i < 50; i++) a.doc.getText('code').insert(0, String(i % 10));
    b.connect();
    await b.whenSynced();
    await until(() => b.doc.getText('code').length === 50);
    expect(b.doc.getText('code').toJSON()).toBe(a.doc.getText('code').toJSON());
  });
});

describe('présence (AC-COLLAB-004)', () => {
  it('affiche les autres utilisateurs et retire celui qui part', async () => {
    const [a, b] = [newClient('ana'), newClient('ben')];
    a.awareness.setLocalState({ user: 'ana' });
    b.awareness.setLocalState({ user: 'ben' });
    a.connect();
    b.connect();
    await Promise.all([a.whenSynced(), b.whenSynced()]);
    await until(() => a.awareness.getStates().size === 2 && b.awareness.getStates().size === 2);
    b.close();
    await until(() => a.awareness.getStates().size === 1);
    expect([...a.awareness.getStates().values()]).toEqual([{ user: 'ana' }]);
  });

  it('retire un utilisateur dont la connexion tombe sans prévenir, après deux intervalles de test de vie', async () => {
    const [a, silent] = [newClient('ana'), newClient('ben', 'write', { autoPong: false })];
    a.awareness.setLocalState({ user: 'ana' });
    silent.awareness.setLocalState({ user: 'ben' });
    a.connect();
    silent.connect();
    await Promise.all([a.whenSynced(), silent.whenSynced()]);
    await until(() => a.awareness.getStates().size === 2);
    const startedAt = Date.now();
    await until(() => a.awareness.getStates().size === 1, 3000);
    // pingIntervalMs = 200 ms : coupé entre 200 et 600 ms environ.
    expect(Date.now() - startedAt).toBeLessThan(1500);
    expect(await server.presentUsers(DOC)).toEqual(['ana']);
  });
});

describe('droits vérifiés côté serveur (AC-COLLAB-005, AC-SEC-001, AC-SEC-002)', () => {
  it('refuse une connexion sans jeton valide', async () => {
    const intruder = new CollabClient({
      url: `ws://127.0.0.1:${String(port)}/collab/${DOC}?token=n-importe-quoi`,
    });
    clients.push(intruder);
    intruder.connect();
    await until(() => intruder.closeCode === CLOSE_UNAUTHORIZED);
    expect(intruder.status).toBe('disconnected');
    expect(await server.connectionCount(DOC)).toBe(0);
  });

  it('un lecteur reçoit les modifications mais ne peut rien écrire', async () => {
    const [writer, reader] = [newClient('ana'), newClient('lea', 'read')];
    writer.connect();
    reader.connect();
    await Promise.all([writer.whenSynced(), reader.whenSynced()]);

    writer.doc.getText('code').insert(0, 'contenu');
    await until(() => reader.doc.getText('code').toJSON() === 'contenu');

    reader.doc.getText('code').insert(0, 'PIRATE ');
    await until(() => reader.serverErrors.includes('READ_ONLY'));
    // Le contenu du serveur et de l'auteur n'a pas bougé.
    const serverText = (await server.document(DOC)).getText('code').toJSON();
    expect(serverText).toBe('contenu');
    expect(writer.doc.getText('code').toJSON()).toBe('contenu');
    expect(server.rejectedWrites.get(DOC)).toBeGreaterThanOrEqual(1);
  });

  it('retirer un droit d’écriture s’applique sans reconnexion', async () => {
    const [a, b] = [newClient('ana'), newClient('ben')];
    a.connect();
    b.connect();
    await Promise.all([a.whenSynced(), b.whenSynced()]);
    b.doc.getText('code').insert(0, 'avant');
    await until(() => a.doc.getText('code').toJSON() === 'avant');

    await server.setAccess(DOC, 'ben', 'read');
    b.doc.getText('code').insert(0, 'APRES ');
    await until(() => b.serverErrors.includes('READ_ONLY'));
    expect((await server.document(DOC)).getText('code').toJSON()).toBe('avant');
    expect(b.status).toBe('connected');
  });

  it('retirer tout accès ferme la connexion et empêche la reconnexion automatique', async () => {
    const [a, b] = [newClient('ana'), newClient('ben')];
    a.connect();
    b.connect();
    await Promise.all([a.whenSynced(), b.whenSynced()]);
    await server.setAccess(DOC, 'ben', null);
    await until(() => b.closeCode === CLOSE_REVOKED);
    await new Promise((resolve) => setTimeout(resolve, 300));
    expect(b.status).toBe('disconnected');
    expect(await server.presentUsers(DOC)).toEqual(['ana']);
  });
});

describe('libération des ressources', () => {
  it('décharge un document quand le dernier utilisateur part, et le recharge intact', async () => {
    const a = newClient('ana');
    a.connect();
    await a.whenSynced();
    a.doc.getText('code').insert(0, 'à décharger');
    await until(
      async () => (await server.document(DOC)).getText('code').toJSON() === 'à décharger',
    );
    a.close();
    await until(() => store.saves >= 1);
    await until(async () => (await server.connectionCount(DOC)) === 0);
    const before = store.saves;
    // Le document a été déchargé puis rechargé depuis le stockage : le contenu est intact.
    expect((await server.document(DOC)).getText('code').toJSON()).toBe('à décharger');
    expect(before).toBeGreaterThanOrEqual(1);
  });

  it('close() libère les documents et leurs minuteurs', async () => {
    const a = newClient('ana');
    a.connect();
    await a.whenSynced();
    await server.close();
    // Un second close() ne casse rien.
    await server.close();
    await startServer();
  });
});

describe('sauvegarde automatique et restauration (AC-RECOVERY-001, AC-RECOVERY-002)', () => {
  it('sauvegarde seule après une modification', async () => {
    const a = newClient('ana');
    a.connect();
    await a.whenSynced();
    a.doc.getText('code').insert(0, 'à sauvegarder');
    await until(() => store.saves >= 1);
    const saved = await store.load(DOC);
    expect(saved).not.toBeNull();
    const copy = new Y.Doc();
    Y.applyUpdate(copy, saved ?? new Uint8Array());
    expect(copy.getText('code').toJSON()).toBe('à sauvegarder');
  });

  it('un nouveau serveur retrouve le dernier état sauvegardé', async () => {
    const a = newClient('ana');
    a.connect();
    await a.whenSynced();
    a.doc.getText('code').insert(0, 'persistant');
    await new Promise((resolve) => setTimeout(resolve, 20));
    await server.flush();
    a.close();
    await server.close();

    server = new CollabServer({ authorize, store, pingIntervalMs: 200, autosaveMs: 50 });
    port = await server.listen();
    const b = newClient('ben');
    b.connect();
    await b.whenSynced();
    await until(() => b.doc.getText('code').toJSON() === 'persistant');
  });

  it('restaure une version sans effacer l’historique (AC-HTML-003, AC-HTML-004)', async () => {
    const a = newClient('ana');
    a.connect();
    await a.whenSynced();
    a.doc.getText('code').insert(0, 'version un');
    await until(async () => (await server.document(DOC)).getText('code').toJSON() === 'version un');
    const first = await server.createVersion(DOC, 'brouillon', 'ana');

    a.doc.getText('code').delete(0, a.doc.getText('code').length);
    a.doc.getText('code').insert(0, 'version deux');
    await until(
      async () => (await server.document(DOC)).getText('code').toJSON() === 'version deux',
    );
    await server.createVersion(DOC, 'publiée', 'ana');

    await server.restoreVersion(DOC, first, 'ana', { code: 'text' });
    await until(() => a.doc.getText('code').toJSON() === 'version un');

    const versions = await store.versions(DOC);
    expect(versions.map((v) => v.label)).toEqual([
      'brouillon',
      'publiée',
      'avant restauration de brouillon',
      'restauration de brouillon',
    ]);
    // L'état « publiée » reste lisible : la restauration n'a rien supprimé.
    const published = new Y.Doc();
    Y.applyUpdate(published, versions[1]?.state ?? new Uint8Array());
    expect(published.getText('code').toJSON()).toBe('version deux');
  });
});

describe('durcissement de la connexion (menaces : détournement de WebSocket, message démesuré)', () => {
  const connectRaw = (
    origin: string | undefined,
  ): Promise<{ code: number | null; gotMessage: boolean; socket: WebSocket }> =>
    new Promise((resolve) => {
      const socket = new WebSocket(
        `ws://127.0.0.1:${String(port)}/collab/${DOC}?token=jeton-ana-write`,
        origin === undefined ? {} : { origin },
      );
      let gotMessage = false;
      socket.on('message', () => {
        gotMessage = true;
        resolve({ code: null, gotMessage, socket });
      });
      socket.on('close', (code) => {
        resolve({ code, gotMessage, socket });
      });
    });

  it('refuse une origine non autorisée, accepte une origine autorisée et un client sans origine', async () => {
    await server.close();
    await startServer({ allowedOrigins: ['https://studio.example'] });
    const bad = await connectRaw('https://evil.example');
    expect(bad.code).toBe(CLOSE_UNAUTHORIZED);
    expect(bad.gotMessage).toBe(false);
    expect(server.rejectedOrigins).toBe(1);
    const good = await connectRaw('https://studio.example');
    expect(good.gotMessage).toBe(true);
    good.socket.close();
    const noOrigin = await connectRaw(undefined);
    expect(noOrigin.gotMessage).toBe(true);
    noOrigin.socket.close();
    expect(server.rejectedOrigins).toBe(1);
  });

  it('sans liste d’origines, aucun contrôle d’origine (comportement d’avant)', async () => {
    const any = await connectRaw('https://autre.example');
    expect(any.gotMessage).toBe(true);
    any.socket.close();
    expect(server.rejectedOrigins).toBe(0);
  });

  it('coupe une connexion qui envoie un message plus grand que la limite, sans gêner les autres', async () => {
    await server.close();
    await startServer({ maxPayloadBytes: 4096 });
    const abuser = await connectRaw(undefined);
    const closed = new Promise<number>((resolve) => {
      abuser.socket.on('close', (code) => {
        resolve(code);
      });
    });
    abuser.socket.send(new Uint8Array(100_000));
    expect(await closed).toBe(1009);
    const a = newClient('ana');
    a.connect();
    await a.whenSynced();
    a.doc.getText('code').insert(0, 'toujours là');
    await until(
      async () => (await server.document(DOC)).getText('code').toJSON() === 'toujours là',
    );
  });
});
