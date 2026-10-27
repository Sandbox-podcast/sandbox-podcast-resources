/* global process, fetch */
import test from 'node:test';
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { setTimeout as delay } from 'node:timers/promises';
import { URL, fileURLToPath } from 'node:url';
import { sourceMedia } from '../media.js';

const port = 4345;
const origin = `http://127.0.0.1:${port}`;
const endpoint = `${origin}/episode-002-bis/api/state?session=tests`;
const child = spawn(process.execPath, [fileURLToPath(new URL('../serve.mjs', import.meta.url))], {
  env: { ...process.env, SANDBOX_BIS_PORT: String(port) },
  stdio: ['ignore', 'pipe', 'pipe'],
  windowsHide: true,
});
let output = '';
child.stdout.on('data', (chunk) => {
  output += chunk.toString();
});
child.stderr.on('data', (chunk) => {
  output += chunk.toString();
});
const post = (action, headers = { Origin: origin, 'Content-Type': 'application/json' }) =>
  fetch(endpoint, { method: 'POST', headers, body: JSON.stringify(action) });

test('serveur local isolé, commandes et protections', async (t) => {
  t.after(() => {
    child.kill();
  });
  await Promise.race([
    once(child.stdout, 'data'),
    once(child, 'exit').then(() => {
      throw new Error(output);
    }),
    delay(10000).then(() => {
      throw new Error('Démarrage du serveur trop long');
    }),
  ]);
  await t.test(
    'les deux URL BIS répondent, les anciennes routes ne sont pas servies par ce processus',
    async () => {
      for (const path of ['/episode-002-bis/', '/episode-002-bis/index.html'])
        assert.equal((await fetch(origin + path)).status, 200);
      assert.equal((await fetch(origin + '/episode-002/index.html')).status, 404);
      assert.equal((await fetch(origin + '/episode-002-bis/serve.mjs')).status, 404);
      assert.equal((await fetch(origin + '/episode-002-bis/test/show.test.mjs')).status, 404);
    },
  );
  await t.test(
    'une commande est reçue par un lecteur indépendant et une nouvelle connexion',
    async () => {
      assert.equal((await post({ type: 'scene', index: 17 })).status, 200);
      await post({ type: 'position', host: 'Lou', value: 'Ça dépend' });
      const state = (await (await fetch(endpoint)).json()).state;
      assert.equal(state.scene, 17);
      assert.equal(state.positions.tickets.Lou, 'Ça dépend');
      await delay(600);
      assert.deepEqual((await (await fetch(endpoint)).json()).state, state);
    },
  );
  await t.test('les sessions restent indépendantes', async () => {
    const other = await (await fetch(endpoint.replace('tests', 'other'))).json();
    assert.equal(other.state.scene, 0);
    assert.equal(other.state.positions.tickets.Lou, '');
  });
  await t.test(
    'les cas 10 et 11 restent directement accessibles et le retour au premier fonctionne',
    async () => {
      await post({ type: 'scene', index: 13 });
      assert.equal((await post({ type: 'step', delta: 9 })).status, 200);
      assert.equal((await (await fetch(endpoint)).json()).state.step, 9);
      await post({ type: 'step', delta: -9 });
      assert.equal((await post({ type: 'step', delta: 10 })).status, 200);
      assert.equal((await (await fetch(endpoint)).json()).state.step, 10);
      assert.equal((await post({ type: 'step', delta: -10 })).status, 200);
      assert.equal((await (await fetch(endpoint)).json()).state.step, 0);
      assert.equal((await post({ type: 'step', delta: 100 })).status, 400);
    },
  );
  await t.test(
    'commandes malformées, origine externe et corps excessifs sont refusés',
    async () => {
      assert.equal((await post({ type: 'scene', index: 999 })).status, 400);
      assert.equal((await post({ type: 'toggle', key: 'admin' })).status, 400);
      assert.equal((await post({ type: 'toggle', key: 'demo' })).status, 400);
      assert.equal((await post({ type: 'media', id: 'https://example.com' })).status, 400);
      assert.equal(
        (
          await post(
            { type: 'scene', index: 1 },
            { Origin: 'https://example.com', 'Content-Type': 'application/json' },
          )
        ).status,
        403,
      );
      assert.equal(
        (await post({ type: 'scene', index: 1 }, { 'Content-Type': 'application/json' })).status,
        403,
      );
      assert.equal(
        (await post({ type: 'scene', index: 1, padding: 'x'.repeat(70000) })).status,
        413,
      );
      assert.equal((await fetch(endpoint.replace('tests', 'bad%20session'))).status, 400);
    },
  );

  await t.test('toutes les dépendances nécessaires sont locales et accessibles', async () => {
    for (const name of [
      'show.js',
      'show.css',
      'model.js',
      'content.js',
      'visuals.js',
      'media.js',
      ...Object.keys(sourceMedia).map((id) => `assets/sources/${id}.jpg`),
      'assets/sources/persuasion-zoom.jpg',
      'assets/logo.png',
      'assets/archivo.woff2',
      'assets/radar-hero.png',
      'assets/build-hero.png',
      'assets/clash-hero.png',
      'assets/beta-hero.png',
    ]) {
      const response = await fetch(`${origin}/episode-002-bis/${name}`);
      assert.equal(response.status, 200, name);
      assert.equal(response.headers.get('cache-control'), 'no-store');
    }
  });
});
