import { describe, expect, it } from 'vitest';
import {
  DEFAULT_RETRY,
  ScriptedProvider,
  attemptTranscription,
  newTranscriptionJob,
  resetJob,
  type TranscriptionJob,
} from '../src/index.ts';

const job = (): TranscriptionJob =>
  newTranscriptionJob({ id: 'j1', mediaRef: 'media-1', mediaDurationSec: 100 });
const ran = (result: Awaited<ReturnType<typeof attemptTranscription>>): TranscriptionJob => {
  if (result.kind !== 'RAN') throw new Error(`pas d'essai : ${result.kind}`);
  return result.job;
};

describe('transcription (AC-TRANSCRIPT-005)', () => {
  it('réussit et produit une transcription versionnée valide', async () => {
    const provider = new ScriptedProvider({ speakers: ['ana', 'ben'], turnSec: 20 });
    const done = ran(await attemptTranscription(job(), provider, 0));
    expect(done.status).toBe('SUCCEEDED');
    expect(done.document?.version).toBe(1);
    expect(done.document?.segments).toHaveLength(5);
    expect(done.document?.segments.map((s) => s.speakerId)).toEqual([
      'ana',
      'ben',
      'ana',
      'ben',
      'ana',
    ]);
    expect(done.lastError).toBeNull();
  });

  it('un échec du fournisseur donne un état clair, un nouvel essai différé, et le média reste accessible', async () => {
    const provider = new ScriptedProvider({
      speakers: ['ana'],
      failures: [new Error('quota dépassé')],
    });
    const failed = ran(await attemptTranscription(job(), provider, 1000));
    expect(failed).toMatchObject({
      status: 'FAILED_RETRYABLE',
      attempts: 1,
      lastError: 'scripted : quota dépassé',
      mediaAccessible: true,
      document: null,
      nextAttemptAtMs: 1000 + DEFAULT_RETRY.baseDelayMs,
    });
  });

  it('refuse de réessayer avant le délai, puis réessaie et réussit', async () => {
    const provider = new ScriptedProvider({ speakers: ['ana'], failures: [new Error('panne')] });
    const failed = ran(await attemptTranscription(job(), provider, 0));
    const early = await attemptTranscription(failed, provider, DEFAULT_RETRY.baseDelayMs - 1);
    expect(early).toEqual({ kind: 'TOO_EARLY', retryAtMs: DEFAULT_RETRY.baseDelayMs });
    expect(provider.calls).toBe(1);
    const retried = ran(await attemptTranscription(failed, provider, DEFAULT_RETRY.baseDelayMs));
    expect(retried.status).toBe('SUCCEEDED');
    expect(retried.attempts).toBe(2);
  });

  it('double le délai à chaque échec, plafonné', async () => {
    const provider = new ScriptedProvider({
      speakers: ['ana'],
      failures: Array.from({ length: 8 }, () => new Error('panne')),
    });
    const policy = { maxAttempts: 10, baseDelayMs: 1000, maxDelayMs: 5000 };
    let current = job();
    let now = 0;
    const delays: number[] = [];
    for (let i = 0; i < 5; i += 1) {
      current = ran(await attemptTranscription(current, provider, now, policy));
      delays.push(current.nextAttemptAtMs - now);
      now = current.nextAttemptAtMs;
    }
    expect(delays).toEqual([1000, 2000, 4000, 5000, 5000]);
  });

  it('devient un échec final au bout des essais permis, puis refuse de continuer', async () => {
    const provider = new ScriptedProvider({
      speakers: ['ana'],
      failures: Array.from({ length: 5 }, () => new Error('panne')),
    });
    const policy = { maxAttempts: 2, baseDelayMs: 10, maxDelayMs: 100 };
    let current = ran(await attemptTranscription(job(), provider, 0, policy));
    current = ran(await attemptTranscription(current, provider, 10, policy));
    expect(current).toMatchObject({ status: 'FAILED_FINAL', attempts: 2, mediaAccessible: true });
    expect(await attemptTranscription(current, provider, 99999, policy)).toEqual({
      kind: 'NOT_RUNNABLE',
      status: 'FAILED_FINAL',
    });
    expect(provider.calls).toBe(2);
    // Relance manuelle : repart de zéro.
    expect(resetJob(current)).toMatchObject({ status: 'QUEUED', attempts: 0, lastError: null });
    expect(resetJob({ ...current, status: 'SUCCEEDED' }).status).toBe('SUCCEEDED');
  });

  it('une transcription réussie n’est pas relancée', async () => {
    const provider = new ScriptedProvider({ speakers: ['ana'] });
    const done = ran(await attemptTranscription(job(), provider, 0));
    expect(await attemptTranscription(done, provider, 1)).toEqual({
      kind: 'NOT_RUNNABLE',
      status: 'SUCCEEDED',
    });
  });

  it.each([
    ['sortie qui n’est pas une liste', () => ({ segments: [] })],
    ['segment sans texte', () => [{ id: 'a', speakerId: 'x', startSec: 0, endSec: 5 }]],
    [
      'temps en dehors du média',
      () => [{ id: 'a', speakerId: 'x', startSec: 90, endSec: 130, text: 't' }],
    ],
    ['fin avant le début', () => [{ id: 'a', speakerId: 'x', startSec: 10, endSec: 5, text: 't' }]],
  ])('rejette une sortie invalide du fournisseur (%s) comme un échec', async (_label, output) => {
    const provider = new ScriptedProvider({ speakers: ['ana'], output });
    const failed = ran(await attemptTranscription(job(), provider, 0));
    expect(failed.status).toBe('FAILED_RETRYABLE');
    expect(failed.document).toBeNull();
    expect(failed.lastError).toMatch(/sortie (invalide|incohérente)/);
  });
});
