import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';

const root = import.meta.dirname;
const manifest = JSON.parse(readFileSync(path.join(root, 'jingles.json'), 'utf8'));
const preview = readFileSync(path.join(root, 'preview.html'), 'utf8');

for (const project of manifest.projects) {
  test(`${project.title} : le master, les assets et le lien de lecture existent`, {skip: process.env.SANDBOX_MEDIA_INTEGRATION !== '1'}, () => {
    const folder = path.join(root, project.folder);
    assert.equal(path.basename(project.outputFile), project.outputFile);
    for (const asset of [
      path.join('renders', project.outputFile),
      path.join('assets', project.heroFile ?? 'hero.png'),
      path.join('assets', 'music.mp3'),
      path.join('assets', 'sandbox-logov2.png'),
    ]) {
      assert.ok(existsSync(path.join(folder, asset)), `Fichier manquant : ${asset}`);
    }
    assert.ok(
      preview.includes(`${project.folder}/renders/${encodeURIComponent(project.outputFile)}`),
      'La page de lecture doit pointer vers le master livré.',
    );
  });
}

for (const project of manifest.projects) {
  test(`${project.title} : les sources du jingle restent disponibles sans médias`, () => {
    const folder = path.join(root, project.folder);
    assert.ok(existsSync(path.join(folder, 'production.html')));
    assert.equal(path.basename(project.outputFile), project.outputFile);
    assert.ok(preview.includes(`${project.folder}/renders/${encodeURIComponent(project.outputFile)}`));
  });
}
