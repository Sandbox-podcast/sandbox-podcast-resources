import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { describe, it } from 'node:test';

const readWorkflow = (name) =>
  readFileSync(new URL(`../../../.github/workflows/${name}.yml`, import.meta.url), 'utf8').replaceAll('\r\n', '\n');
const youtube = readWorkflow('youtube-growth');
const poll = youtube.split('\n  poll:\n')[1];
const preflight = poll
  ?.split('        run: |\n')[1]
  ?.split('\n      - uses:')[0]
  ?.replace(/^ {10}/gm, '');
if (!preflight) throw new Error('Contrôle de configuration YouTube introuvable.');
const bash = process.platform === 'win32'
  ? join(process.env['ProgramFiles'] ?? 'C:/Program Files', 'Git/bin/bash.exe')
  : 'bash';

function runPreflight(configuration = {}) {
  const directory = mkdtempSync(join(tmpdir(), 'sandbox-workflow-'));
  const outputPath = join(directory, 'output').replaceAll('\\', '/');
  const summaryPath = join(directory, 'summary').replaceAll('\\', '/');
  try {
    const result = spawnSync(bash, ['--noprofile', '--norc', '-s'], {
      encoding: 'utf8',
      input: preflight,
      env: {
        ...process.env,
        YOUTUBE_OAUTH_TOKEN_JSON: '',
        YOUTUBE_EXECUTE_ACTIONS: '',
        YOUTUBE_INITIAL_REVIEW_CONFIRMED: '',
        YOUTUBE_JOURNAL_DATABASE_URL: '',
        ...configuration,
        GITHUB_OUTPUT: outputPath,
        GITHUB_STEP_SUMMARY: summaryPath,
      },
    });
    const content = (path) => {
      try {
        return readFileSync(path, 'utf8');
      } catch (error) {
        if (error instanceof Error && 'code' in error && error.code === 'ENOENT') return '';
        throw error;
      }
    };
    return { ...result, output: content(outputPath), summary: content(summaryPath) };
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
}

describe('polling YouTube avant installation', () => {
  it('exécute le traitement uniquement sur demande manuelle et garde les tests push/PR', () => {
    assert.equal(youtube.includes('  schedule:'), false);
    assert.equal(youtube.includes('  workflow_dispatch:'), true);
    assert.equal(poll?.includes("if: github.event_name == 'workflow_dispatch' && github.ref == format('refs/heads/{0}', github.event.repository.default_branch)"), true);
    assert.equal(poll?.includes("github.event_name == 'schedule'"), false);
    assert.equal(youtube.includes("if: github.event_name == 'push' || github.event_name == 'pull_request'"), true);
  });

  it('signale le passage sans effet sans OAuth', () => {
    const result = runPreflight();
    assert.equal(result.error, undefined);
    assert.equal(result.status, 0);
    assert.equal(result.output, 'ready=false\n');
    assert.match(result.summary, /aucune dépendance installée/);
  });

  it('autorise la lecture avec OAuth sans activer les écritures', () => {
    const result = runPreflight({ YOUTUBE_OAUTH_TOKEN_JSON: 'fixture-token-not-real' });
    assert.equal(result.status, 0);
    assert.equal(result.output, 'ready=true\n');
    assert.doesNotMatch(result.stdout + result.stderr + result.output + result.summary, /fixture-token/);
  });

  for (const enabled of ['true', '1', 'yes', 'on', ' TRUE ']) {
    it(`refuse les écritures ${enabled} sans configuration complète`, () => {
      for (const missing of ['YOUTUBE_OAUTH_TOKEN_JSON', 'YOUTUBE_INITIAL_REVIEW_CONFIRMED', 'YOUTUBE_JOURNAL_DATABASE_URL']) {
        const result = runPreflight({
          YOUTUBE_EXECUTE_ACTIONS: enabled,
          YOUTUBE_OAUTH_TOKEN_JSON: 'fixture-token-not-real',
          YOUTUBE_INITIAL_REVIEW_CONFIRMED: 'true',
          YOUTUBE_JOURNAL_DATABASE_URL: 'fixture-database-not-real',
          [missing]: '',
        });
        assert.equal(result.status, 1);
        assert.equal(result.output, '');
        assert.doesNotMatch(result.stdout + result.stderr, /fixture-token|fixture-database/);
      }
    });
  }

  it('laisse les contrôles applicatifs vérifier la configuration complète', () => {
    const result = runPreflight({
      YOUTUBE_EXECUTE_ACTIONS: 'true',
      YOUTUBE_OAUTH_TOKEN_JSON: 'fixture-token-not-real',
      YOUTUBE_INITIAL_REVIEW_CONFIRMED: 'true',
      YOUTUBE_JOURNAL_DATABASE_URL: 'fixture-database-not-real',
    });
    assert.equal(result.output, 'ready=true\n');
  });

  it('conditionne toutes les étapes coûteuses et garde un verrou propre au polling', () => {
    const steps = poll?.split(/\n {6}- /).slice(2) ?? [];
    assert.equal(steps.length, 6);
    for (const step of steps) assert.ok(step.includes("steps.configuration.outputs.ready == 'true'"));
    assert.ok(poll?.includes('group: youtube-growth-main'));
    assert.ok(poll?.includes('cancel-in-progress: false'));
    assert.ok(youtube.split('\n  poll:\n')[0].includes('group: youtube-quality-${{ github.ref }}'));
  });
});
