import { describe, expect, it } from 'vitest';
import {
  correctSegment,
  createTranscript,
  findSegmentAt,
  seekTimeFor,
  validateTranscript,
  type TranscriptDocument,
  type TranscriptSegment,
} from '../src/index.ts';

const seg = (
  id: string,
  speakerId: string,
  startSec: number,
  endSec: number,
): TranscriptSegment => ({
  id,
  speakerId,
  startSec,
  endSec,
  text: `texte ${id}`,
});

const SEGMENTS = [seg('s1', 'ana', 0, 10), seg('s2', 'ben', 10, 25), seg('s3', 'ana', 25, 40)];

function document(): TranscriptDocument {
  const created = createTranscript({
    id: 't1',
    mediaRef: 'media-1',
    mediaDurationSec: 60,
    segments: SEGMENTS,
  });
  if (!created.ok) throw new Error(JSON.stringify(created.issues));
  return created.document;
}

describe('validation (AC-TRANSCRIPT-001)', () => {
  it('accepte des segments cohérents', () => {
    expect(validateTranscript(SEGMENTS, 60)).toEqual([]);
  });

  it.each([
    ['fin avant début', [seg('a', 'x', 10, 5)], 'la fin doit suivre le début'],
    ['début égal à la fin', [seg('a', 'x', 5, 5)], 'la fin doit suivre le début'],
    ['fin au-delà du média', [seg('a', 'x', 50, 61)], 'la fin dépasse la durée du média'],
    ['identifiant en double', [seg('a', 'x', 0, 5), seg('a', 'y', 5, 8)], 'identifiant en double'],
    ['désordre', [seg('a', 'x', 10, 15), seg('b', 'y', 0, 5)], 'segments non triés par début'],
    [
      'même locuteur qui se chevauche',
      [seg('a', 'x', 0, 10), seg('b', 'x', 5, 12)],
      'chevauche un autre segment du même locuteur',
    ],
  ])('refuse : %s', (_label, segments, message) => {
    expect(validateTranscript(segments, 60).map((i) => i.message)).toContain(message);
  });

  it('autorise deux locuteurs différents qui parlent en même temps', () => {
    expect(validateTranscript([seg('a', 'x', 0, 10), seg('b', 'y', 5, 12)], 60)).toEqual([]);
  });

  it('un segment qui finit exactement à la durée du média est valide', () => {
    expect(validateTranscript([seg('a', 'x', 0, 60)], 60)).toEqual([]);
  });

  it('refuse un segment hors schéma à la création (champ en trop, locuteur vide)', () => {
    const bad = createTranscript({
      id: 't',
      mediaRef: 'm',
      mediaDurationSec: 60,
      segments: [{ ...seg('a', '', 0, 5), extra: 1 } as unknown as TranscriptSegment],
    });
    expect(bad.ok).toBe(false);
  });
});

describe('navigation (AC-TRANSCRIPT-002)', () => {
  it('trouve le segment qui contient l’instant', () => {
    expect(findSegmentAt(SEGMENTS, 12, 1)?.id).toBe('s2');
    expect(findSegmentAt(SEGMENTS, 10, 1)?.id).toBe('s2');
    expect(findSegmentAt(SEGMENTS, 9.999, 1)?.id).toBe('s1');
  });

  it('prend le plus proche dans la tolérance, sinon rien', () => {
    const gaps = [seg('a', 'x', 0, 10), seg('b', 'x', 20, 30)];
    expect(findSegmentAt(gaps, 11, 2)?.id).toBe('a');
    expect(findSegmentAt(gaps, 19, 2)?.id).toBe('b');
    expect(findSegmentAt(gaps, 15, 2)).toBeNull();
    expect(findSegmentAt([], 5, 2)).toBeNull();
  });

  it('positionne le lecteur au début du segment avec une amorce, sans passer sous zéro', () => {
    expect(seekTimeFor(seg('a', 'x', 25, 40))).toBe(24.5);
    expect(seekTimeFor(seg('a', 'x', 0.2, 5))).toBe(0);
    expect(seekTimeFor(seg('a', 'x', 25, 40), 2)).toBe(23);
  });
});

describe('corrections versionnées (AC-TRANSCRIPT-003, 004)', () => {
  it('corrige le texte et le locuteur, garde l’historique et le journal, ne touche pas au média', () => {
    const v1 = document();
    const first = correctSegment(v1, {
      segmentId: 's2',
      text: 'texte corrigé',
      actorId: 'lou',
      at: 1000,
    });
    if (!first.ok) throw new Error(first.message);
    const second = correctSegment(first.document, {
      segmentId: 's2',
      speakerId: 'chloe',
      actorId: 'sam',
      at: 2000,
    });
    if (!second.ok) throw new Error(second.message);
    const v3 = second.document;

    expect(v3.version).toBe(3);
    expect(v3.segments[1]).toMatchObject({
      text: 'texte corrigé',
      speakerId: 'chloe',
      startSec: 10,
      endSec: 25,
    });
    expect(v3.history.map((h) => h.version)).toEqual([1, 2, 3]);
    expect(v3.history[0]?.segments[1]?.text).toBe('texte s2');
    expect(v3.changes).toEqual([
      {
        version: 2,
        segmentId: 's2',
        field: 'text',
        before: 'texte s2',
        after: 'texte corrigé',
        actorId: 'lou',
        at: 1000,
      },
      {
        version: 3,
        segmentId: 's2',
        field: 'speakerId',
        before: 'ben',
        after: 'chloe',
        actorId: 'sam',
        at: 2000,
      },
    ]);
    expect(v3.mediaRef).toBe(v1.mediaRef);
    expect(v3.mediaDurationSec).toBe(v1.mediaDurationSec);
    // La version d'origine n'est pas modifiée.
    expect(v1.segments[1]?.text).toBe('texte s2');
    expect(v1.version).toBe(1);
  });

  it('journalise deux changements pour une correction du texte et du locuteur ensemble', () => {
    const result = correctSegment(document(), {
      segmentId: 's1',
      text: 'a',
      speakerId: 'zoe',
      actorId: 'lou',
      at: 5,
    });
    if (!result.ok) throw new Error(result.message);
    expect(result.document.changes.map((c) => c.field)).toEqual(['text', 'speakerId']);
    expect(result.document.version).toBe(2);
  });

  it('refuse un segment inconnu, une correction sans effet et une valeur invalide', () => {
    const doc = document();
    expect(
      correctSegment(doc, { segmentId: 'zz', text: 'x', actorId: 'lou', at: 1 }),
    ).toMatchObject({ ok: false, reason: 'SEGMENT_NOT_FOUND' });
    expect(
      correctSegment(doc, { segmentId: 's1', text: 'texte s1', actorId: 'lou', at: 1 }),
    ).toMatchObject({ ok: false, reason: 'NO_CHANGE' });
    expect(
      correctSegment(doc, { segmentId: 's1', speakerId: '', actorId: 'lou', at: 1 }),
    ).toMatchObject({ ok: false, reason: 'INVALID' });
    expect(
      correctSegment(doc, { segmentId: 's1', text: 'x'.repeat(5001), actorId: 'lou', at: 1 }),
    ).toMatchObject({ ok: false, reason: 'INVALID' });
  });

  it('refuse un changement de locuteur qui ferait chevaucher le même locuteur', () => {
    const doc = createTranscript({
      id: 't',
      mediaRef: 'm',
      mediaDurationSec: 60,
      segments: [seg('a', 'x', 0, 10), seg('b', 'y', 5, 12)],
    });
    if (!doc.ok) throw new Error('création');
    expect(
      correctSegment(doc.document, { segmentId: 'b', speakerId: 'x', actorId: 'lou', at: 1 }),
    ).toMatchObject({
      ok: false,
      reason: 'INVALID',
    });
  });
});
