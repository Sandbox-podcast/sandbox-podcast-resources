import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
import path from 'node:path';
const root = path.resolve(import.meta.dirname, '..');
const localMedia = process.env.SANDBOX_MEDIA_INTEGRATION === '1';
const timeline = JSON.parse(readFileSync(root + '/timeline.json', 'utf8'));
const integrity = JSON.parse(readFileSync(root + '/source-integrity.json', 'utf8'));

test('Lou, Loïc, Nico et le narrateur ont quatre voix et fichiers distincts', {skip: !localMedia}, () => {
  const edit = JSON.parse(readFileSync(root + '/voice-edit.json', 'utf8'));
  assert.equal(new Set(Object.values(edit.catalogVoices)).size, 4);
  const hashes = Object.keys(edit.catalogVoices).map((id) =>
    createHash('sha256')
      .update(readFileSync(root + '/public/voices/' + id + '-elevenlabs.mp3'))
      .digest('hex'),
  );
  assert.equal(new Set(hashes).size, 4);
  assert.equal(timeline.audio, edit.output);
  assert.notEqual(timeline.audio, 'public/original.m4a');
});

test('Les 23 répliques restent dans leur fenêtre sans chevauchement ni accélération excessive', {skip: !localMedia}, () => {
  const edit = JSON.parse(readFileSync(root + '/voice-edit.json', 'utf8'));
  const report = JSON.parse(readFileSync(root + '/analysis/voice-mix-report.json', 'utf8'));
  assert.equal(report.duration, timeline.duration);
  assert.equal(report.segments.length, 23);
  assert.ok(report.peakDbFS <= -1.49);
  for (const [index, line] of report.segments.entries()) {
    assert.ok(line.start >= 0 && line.end <= timeline.duration);
    assert.ok(line.renderedDuration <= line.end - line.start + 1 / edit.sampleRate);
    assert.ok(line.speed >= 1 && line.speed <= 1.3);
    assert.ok(edit.replaceWindows.some(([a, b]) => a <= line.start && b >= line.end));
    assert.ok(line.file.startsWith('public/voices/aligned/'));
    assert.equal(line.file.includes('\\'), false, 'Le rapport doit rester lisible sur Linux.');
    assert.equal(path.posix.normalize(line.file), line.file);
    assert.ok(existsSync(root + '/' + line.file));
    if (index) assert.ok(report.segments[index - 1].end <= line.start);
  }
  for (const [voice, start] of [
    ['lou', 14.96],
    ['loic', 20.88],
    ['nico', 26.88],
  ]) {
    const line = report.segments.find((item) => item.id === voice + '-replique');
    assert.equal(line.voice, voice);
    assert.equal(line.start, start);
  }
});
test('Lou utilise le portrait de face avec ses proportions natives', {skip: !localMedia}, () => {
  const portrait = readFileSync(root + '/public/lou.png');
  assert.deepEqual([portrait.readUInt32BE(16), portrait.readUInt32BE(20)], [560, 715]);
  const provenance = JSON.parse(readFileSync(root + '/public/portrait-provenance.json', 'utf8'));
  const lou = provenance.find((p) => p.id === 'lou');
  assert.ok(lou.source.endsWith('/Lou sandbox.png'));
  assert.equal(lou.width, 1334);
  assert.equal(lou.height, 1179);
});
test('Les deux nouveaux portraits de Loïc gardent leurs proportions natives', {skip: !localMedia}, () => {
  const primary = readFileSync(root + '/public/loic.png');
  const alternate = readFileSync(root + '/public/loic-alt.png');
  assert.deepEqual([primary.readUInt32BE(16), primary.readUInt32BE(20)], [565, 700]);
  assert.deepEqual([alternate.readUInt32BE(16), alternate.readUInt32BE(20)], [566, 802]);
  const provenance = JSON.parse(readFileSync(root + '/public/portrait-provenance.json', 'utf8'));
  assert.ok(provenance.find((p) => p.id === 'loic').source.endsWith('loic 2.png'));
  assert.ok(provenance.find((p) => p.id === 'loic-alt').source.endsWith('loic 3.png'));
});
test('La timeline couvre la source entière, sans trou ni chevauchement', () => {
  assert.equal(timeline.scenes.length, 9);
  assert.equal(timeline.scenes[0].start, 0);
  assert.equal(timeline.scenes.at(-1).end, timeline.duration);
  assert.equal(timeline.duration * timeline.fps, timeline.durationInFrames);
  for (let i = 0; i < timeline.scenes.length; i++) {
    const s = timeline.scenes[i];
    assert.ok(s.end > s.start);
    assert.ok(s.punchline >= s.start && s.punchline < s.end);
    assert.ok(s.firstWord >= s.start && s.lastWord <= s.end);
    if (i > 0) assert.equal(timeline.scenes[i - 1].end, s.start);
  }
});
test('Les trois annonces et quatre rubriques suivent les repères ASR de la source', () => {
  const expected = {
    lou: 10.56,
    loic: 16.72,
    nico: 22.72,
    radar: 33.28,
    build: 37.84,
    clash: 43.04,
    beta: 46.8,
    finale: 51.68,
  };
  for (const [id, start] of Object.entries(expected))
    assert.equal(timeline.scenes.find((s) => s.id === id).start, start);
});
test('La copie de travail audio est identique au M4A original et les vrais visages sont présents', {skip: !localMedia}, () => {
  const hash = (p) => createHash('sha256').update(readFileSync(p)).digest('hex');
  const originalAudio = path.resolve(
    root,
    '../../../.local/legacy/media/audio/suno/76c021b3-a4dc-4890-b561-b8a775f2e623/1 - Générique Sandbox.m4a',
  );
  const originalLogo = path.resolve(root, '../../../assets/brand/logo.png');
  assert.equal(
    hash(root + '/public/original.m4a'),
    existsSync(originalAudio) ? hash(originalAudio) : integrity.audio,
  );
  assert.equal(
    hash(root + '/public/logo.png'),
    existsSync(originalLogo) ? hash(originalLogo) : integrity.logo,
  );
  for (const [host, fingerprint] of Object.entries(integrity.portraits))
    assert.equal(hash(root + '/public/originals/' + host + '.png'), fingerprint);
  for (const host of ['lou', 'loic', 'nico'])
    assert.ok(existsSync(root + '/public/' + host + '.png'));
});
