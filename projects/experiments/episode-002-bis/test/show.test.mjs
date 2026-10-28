import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath, URL } from 'node:url';
import { episode } from '../content.js';
import {
  chapters,
  scenes,
  initialState,
  normalizeState,
  transition,
  stepCount,
  indexFromHash,
  navigationActions,
} from '../model.js';
import { renderScene, escapeText } from '../visuals.js';
import { sourceMedia, videoMedia } from '../media.js';
import { publicFiles, expectedPublicFile } from '../publish.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
const publishedRoot = resolve(root, 'fixtures/site-public/episode-002-bis');
const originalRoot = resolve(root, 'fixtures/site-public/episode-002');
const html = readFileSync(resolve(originalRoot, 'index.html'), 'utf8');
const original = JSON.parse(
  html.match(/<script id="deckData" type="application\/json">([\s\S]*?)<\/script>/)[1],
);

test('les 22 contenus, notes, actions, transitions et 34 références sont conservés intégralement', () => {
  assert.deepEqual(episode.original, original);
  assert.equal(Object.keys(episode.original.sources).length, 34);
  assert.equal(episode.archive.length, 22);
  assert.deepEqual(
    scenes
      .map((s) => s.originalNumber)
      .filter(Boolean)
      .sort((a, b) => a - b),
    Array.from({ length: 22 }, (_, i) => i + 1),
  );
});
test('le parcours suit Radar, Build, Clash, Bêta conformément à la correction de Lou', () => {
  assert.deepEqual(
    chapters.map((c) => c.id),
    ['radar', 'build', 'clash', 'beta'],
  );
  assert.deepEqual([...new Set(scenes.map((s) => s.chapter))], ['radar', 'build', 'clash', 'beta']);
  for (const chapter of chapters) assert.equal(scenes[chapter.start].id, chapter.id);
});
test('chaque phrase visible de chaque écran original reste dans le dossier', () => {
  const decode = (s) =>
    s
      .replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<')
      .replace(/&gt;/g, '>')
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'")
      .replace(/&nbsp;/g, ' ');
  const sections = [...html.matchAll(/<section\b[\s\S]*?<\/section>/g)];
  sections.forEach(([section], i) =>
    assert.equal(
      episode.archive[i].text,
      decode(
        section
          .replace(/<[^>]+>/g, ' ')
          .replace(/\s+/g, ' ')
          .trim(),
      ),
    ),
  );
});
test('le Build explique les outils et usages, sans démonstration', () => {
  assert.deepEqual(
    scenes.filter((s) => s.chapter === 'build').map((s) => s.id),
    ['build', 'artisans', 'usages', 'tools', 'method'],
  );
  assert.ok(!scenes.some((s) => s.kind === 'demo'));
  assert.doesNotMatch(
    readFileSync(resolve(root, 'index.html'), 'utf8'),
    /demo-layer|Démo Anna|beta-demo/,
  );
});
test('toutes les notes de prudence et distinctions sont reprises', () => {
  assert.match(episode.original.slides[10].note, /expression de préoccupation/);
  assert.match(scenes.find((s) => s.id === 'persuasion').caution, /sous examen/);
  assert.match(scenes.find((s) => s.id === 'replication').caution, /laboratoire/);
  assert.match(scenes.find((s) => s.id === 'glasses').caution, /pas une interdiction adoptée/);
  assert.match(scenes.find((s) => s.id === 'rea').caution, /indépendante/);
});
test('la navigation ne sort jamais des limites et changer de sujet ferme la vidéo', () => {
  let state = normalizeState(initialState(), episode);
  state = transition(state, { type: 'scene', index: -10 }, episode);
  assert.equal(state.scene, 0);
  state = transition(state, { type: 'scene', index: 2 }, episode);
  state = transition(state, { type: 'media', id: 'creator' }, episode);
  assert.equal(state.media, 'creator');
  state = transition(state, { type: 'scene', index: 1000 }, episode);
  assert.equal(state.scene, 22);
  assert.equal(state.media, '');
  assert.equal(state.step, 0);
});
test('développer une étape du Build ne passe jamais automatiquement au sujet suivant', () => {
  let state = normalizeState({ scene: 15, step: 2 }, episode);
  state = transition(state, { type: 'step', delta: 1 }, episode);
  assert.equal(state.scene, 15);
  assert.equal(state.step, 2);
  assert.equal(stepCount(scenes[13], episode), 11);
  assert.equal(normalizeState({ scene: 13, step: 11 }, episode).step, 10);
  assert.equal(stepCount(scenes[14], episode), 5);
});
test('chaque actualité du Radar réunit tous ses points et Suivant change directement de sujet', () => {
  for (const [index, scene] of scenes.entries()) {
    if (scene.chapter !== 'radar' || scene.kind === 'opener') continue;
    const state = normalizeState({ scene: index, step: 2 }, episode);
    const source = episode.original.slides.find((slide) => slide.n === scene.originalNumber);
    assert.equal(stepCount(scene, episode), 1);
    assert.equal(state.step, 0);
    assert.deepEqual(navigationActions(state, 1, episode), [{ type: 'scene', index: index + 1 }]);
    for (const view of ['visual', 'zoom', 'fact']) {
      const markup = renderScene(scene, { ...state, view }, episode, chapters[0]);
      for (const [title, description] of source.items) {
        assert.ok(markup.includes(`<h2>${escapeText(title)}</h2>`));
        assert.ok(markup.includes(`<p>${escapeText(description)}</p>`));
      }
      assert.doesNotMatch(markup, /data-step=|Afficher le point|POINT 0/);
    }
  }
});
test('le Clash ne préremplit aucune opinion, conserve les positions par question et accepte les nuances', () => {
  let state = normalizeState({ scene: 17 }, episode);
  assert.deepEqual(Object.values(state.positions.tickets), ['', '', '']);
  state = transition(state, { type: 'position', host: 'Loïc', value: 'Ça dépend' }, episode);
  const copy = state;
  state = transition(state, { type: 'scene', index: 18 }, episode);
  assert.equal(state.positions.tickets['Loïc'], 'Ça dépend');
  assert.equal(state.positions.legacy['Loïc'], '');
  assert.equal(copy.scene, 17);
});
test('un état malformé ne fait pas planter le conducteur', () => {
  for (const value of [
    null,
    [],
    { scene: NaN, step: Infinity, positions: {}, speaker: 'Inconnu', timerUntil: -1 },
  ]) {
    const state = normalizeState(value, episode);
    assert.equal(state.scene, 0);
    assert.equal(state.step, 0);
    assert.equal(state.speaker, '');
    assert.equal(state.timerUntil, 0);
  }
});
test('les ancres nommées et numériques sont bornées et rejouables', () => {
  assert.equal(indexFromHash('#clash'), 16);
  assert.equal(indexFromHash('#24'), 22);
  assert.equal(indexFromHash('#slide-21'), 20);
  assert.equal(indexFromHash('#9999'), 22);
  assert.equal(indexFromHash('#inconnu'), 0);
});
test('les scènes et tous leurs points se rendent sans texte indéfini', () => {
  scenes.forEach((scene, index) => {
    for (let step = 0; step < stepCount(scene, episode); step++) {
      const state = normalizeState({ scene: index, step }, episode);
      const markup = renderScene(
        scene,
        state,
        episode,
        chapters.find((c) => c.id === scene.chapter),
      );
      assert.match(markup, /<h1>/);
      assert.doesNotMatch(markup, /undefined|NaN/);
      if (scene.kind === 'uses' && step === 10) {
        assert.match(markup, /class="big-index">11</);
        assert.doesNotMatch(markup, />010<|>011</);
      }
    }
  });
});
test('le HTML éditorial est échappé et les ressources du navigateur sont locales', () => {
  assert.equal(escapeText('<img onerror="bad">'), '&lt;img onerror=&quot;bad&quot;&gt;');
  const entry = readFileSync(resolve(root, 'index.html'), 'utf8');
  for (const [, asset] of entry.matchAll(/(?:src|href)="(\.\/[^"?#]+)"/g))
    if (!asset.startsWith('./assets/')) assert.ok(existsSync(resolve(root, asset)));
  assert.doesNotMatch(entry, /(?:src|href)="https?:/);
});

test('les dix sujets Radar disposent de captures réelles locales et attribuées', {skip: process.env.SANDBOX_MEDIA_INTEGRATION !== '1'}, () => {
  const radar = scenes.filter((scene) => scene.chapter === 'radar' && scene.kind !== 'opener');
  assert.equal(radar.length, 10);
  for (const scene of radar) {
    const media = sourceMedia[scene.id];
    assert.ok(media.publisher && media.url.startsWith('https://'));
    const bytes = readFileSync(resolve(root, `assets/sources/${scene.id}.jpg`));
    assert.equal(bytes.readUInt16BE(0), 0xffd8);
    assert.ok(bytes.length > 10000);
  }
});

test('les vidéos sont limitées au sujet Gemini et fermées au changement de sujet', () => {
  let state = normalizeState({ scene: 2, media: 'url-arbitraire' }, episode);
  assert.equal(state.media, '');
  for (const id of Object.keys(videoMedia)) {
    state = transition(state, { type: 'media', id }, episode);
    assert.equal(state.media, id);
    state = transition(state, { type: 'scene', index: 11 }, episode);
    assert.equal(state.media, '');
    state = transition(state, { type: 'media', id }, episode);
    assert.equal(state.media, '');
    state = transition(state, { type: 'scene', index: 2 }, episode);
  }
  assert.doesNotMatch(readFileSync(resolve(root, 'index.html'), 'utf8'), /<iframe/);
});

test('Suivant parcourt chaque point une seule fois et Précédent revient au même écran', () => {
  const apply = (state, direction) =>
    navigationActions(state, direction, episode).reduce(
      (current, command) => transition(current, command, episode),
      state,
    );
  let state = normalizeState(initialState(), episode);
  const visited = [];
  for (let i = 0; i < scenes.length; i++) {
    for (let step = 0; step < stepCount(scenes[i], episode); step++) {
      assert.deepEqual([state.scene, state.step], [i, step]);
      visited.push([i, step]);
      const next = apply(state, 1);
      if (i < scenes.length - 1 || step < stepCount(scenes[i], episode) - 1) {
        const back = apply(next, -1);
        assert.deepEqual([back.scene, back.step], [i, step]);
      }
      state = next;
    }
  }
  assert.equal(new Set(visited.map((entry) => entry.join(':'))).size, visited.length);
  assert.deepEqual(navigationActions(state, 1, episode), []);
  assert.deepEqual(navigationActions(normalizeState(initialState(), episode), -1, episode), []);
  assert.equal(
    stepCount(
      scenes.find((s) => s.kind === 'shop'),
      episode,
    ),
    1,
  );
  assert.equal(
    stepCount(
      scenes.find((s) => s.kind === 'comments'),
      episode,
    ),
    1,
  );
});

test('la publication contient tous les fichiers du lecteur, sans serveur ni démonstration', async () => {
  for (const file of publicFiles.filter((name) => !name.startsWith('assets/'))) {
    assert.deepEqual(readFileSync(resolve(publishedRoot, file)), await expectedPublicFile(file), file);
  }
  const entry = readFileSync(resolve(publishedRoot, 'index.html'), 'utf8');
  assert.match(entry, /name="sandbox-sync" content="browser"/);
  for (const excluded of [
    'serve.mjs',
    'publish.mjs',
    'test/show.test.mjs',
    'assets/beta-demo.html',
  ]) {
    assert.equal(existsSync(resolve(publishedRoot, excluded)), false, excluded);
  }
  for (const [, asset] of entry.matchAll(/(?:src|href)="(\.\/[^"?#]+)"/g)) {
    if (!asset.startsWith('./assets/')) assert.ok(existsSync(resolve(publishedRoot, asset)), asset);
  }
});

test('les médias locaux du deck correspondent au snapshot', {skip: process.env.SANDBOX_MEDIA_INTEGRATION !== '1'}, async () => {
  for (const file of publicFiles.filter((name) => name.startsWith('assets/'))) {
    assert.deepEqual(readFileSync(resolve(publishedRoot, file)), await expectedPublicFile(file), file);
  }
});
