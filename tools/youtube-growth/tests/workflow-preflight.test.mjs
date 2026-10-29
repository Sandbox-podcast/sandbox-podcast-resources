import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { describe, it } from 'node:test';

const readWorkflow = (name) =>
  readFileSync(new URL(`../../../.github/workflows/${name}.yml`, import.meta.url), 'utf8');

describe('GitHub contrôle les sources ; la production reste sur les postes', () => {
  it('conserve les tests Python sur push et PR', () => {
    const youtube = readWorkflow('youtube-growth');
    assert.match(youtube, /  push:/);
    assert.match(youtube, /  pull_request:/);
    assert.match(youtube, /python -m unittest discover -s tools\/youtube-growth\/tests -v/);
  });

  it('ne lance aucun traitement de chaîne et ne téléverse aucun média', () => {
    for (const name of ['ci', 'youtube-growth']) {
      const workflow = readWorkflow(name);
      assert.doesNotMatch(workflow, /workflow_dispatch:|schedule:|\n  poll:/);
      assert.doesNotMatch(workflow, /actions\/upload-artifact|YOUTUBE_OAUTH_TOKEN_JSON|YOUTUBE_EXECUTE_ACTIONS/);
      assert.doesNotMatch(workflow, /run: python -m youtube_growth\s*$/m);
    }
  });

  it('active la recette média synthétique dans la même étape que la suite Python', () => {
    const youtube = readWorkflow('youtube-growth');
    const testStep = youtube.match(/- name: Exécuter les tests Python\n([\s\S]*?)(?=\n      - |$)/)?.[1];
    assert.ok(testStep, 'Étape de tests Python requise');
    assert.match(testStep, /FACTORY_MEDIA_INTEGRATION: ['"]?1['"]?\s*\n/);
    assert.match(testStep, /python -m unittest discover -s tools\/youtube-growth\/tests -v/);
    assert.match(youtube, /apt-get install -y ffmpeg/);
  });

  it('vérifie les fichiers suivis pour refuser les livrables ajoutés de force', () => {
    const ci = readWorkflow('ci');
    assert.match(ci, /python tools\/repository\/check_repository.py/);
    assert.match(ci, /python -m unittest discover -s tools\/repository -v/);
  });
});
