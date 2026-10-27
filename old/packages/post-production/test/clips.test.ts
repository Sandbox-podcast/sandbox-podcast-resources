import { describe, expect, it } from 'vitest';
import {
  DEFAULT_CLIP_RULES,
  SAFE_ZONES,
  adjustClip,
  safeZoneViolations,
  validateSuggestions,
  verticalCrop,
  type TranscriptSegment,
} from '../src/index.ts';

// Segments de 20 s : 0-20, 20-40, 40-60, ...
const segments: TranscriptSegment[] = Array.from({ length: 9 }, (_, i) => ({
  id: `s${String(i + 1)}`,
  speakerId: i % 2 === 0 ? 'ana' : 'ben',
  startSec: i * 20,
  endSec: (i + 1) * 20,
  text: `texte ${String(i + 1)}`,
}));
const DURATION = 180;

const suggestion = (extra: Record<string, unknown> = {}) => ({
  startSec: 20,
  endSec: 60,
  title: 'Un bon moment',
  hook: 'Ce que personne ne dit',
  reason: 'Question suivie d’une réponse complète',
  score: 0.8,
  ...extra,
});

describe('validation des suggestions (AC-CLIP-001, AC-CLIP-005)', () => {
  it('accepte une suggestion alignée sur des segments et la rend avec ses segments', () => {
    const { accepted, rejected } = validateSuggestions([suggestion()], segments, DURATION);
    expect(rejected).toEqual([]);
    expect(accepted).toEqual([{ ...suggestion(), firstSegmentId: 's2', lastSegmentId: 's3' }]);
  });

  it('recale les points sur les limites exactes des segments', () => {
    const { accepted } = validateSuggestions(
      [suggestion({ startSec: 20.2, endSec: 59.9 })],
      segments,
      DURATION,
    );
    expect(accepted[0]).toMatchObject({ startSec: 20, endSec: 60 });
  });

  it.each([
    [
      'début qui ne correspond à aucun segment',
      { startSec: 27, endSec: 60 },
      'le début ne correspond à aucun début de segment',
    ],
    [
      'fin qui ne correspond à aucun segment',
      { startSec: 20, endSec: 67 },
      'la fin ne correspond à aucune fin de segment',
    ],
    ['fin au-delà du média', { startSec: 160, endSec: 200 }, 'la fin dépasse la durée du média'],
    ['fin avant le début', { startSec: 60, endSec: 40 }, 'la fin doit suivre le début'],
    ['trop longue', { startSec: 0, endSec: 100 }, 'durée au-dessus de 90 s'],
  ])('rejette : %s', (_label, extra, reason) => {
    const { accepted, rejected } = validateSuggestions([suggestion(extra)], segments, DURATION);
    expect(accepted).toEqual([]);
    expect(rejected[0]?.reasons).toContain(reason);
  });

  it('rejette une suggestion plus courte que le minimum configuré', () => {
    const { accepted, rejected } = validateSuggestions(
      [suggestion({ startSec: 20, endSec: 40 })],
      segments,
      DURATION,
      {
        ...DEFAULT_CLIP_RULES,
        minDurationSec: 30,
      },
    );
    expect(accepted).toEqual([]);
    expect(rejected[0]?.reasons).toEqual(['durée sous 30 s']);
  });

  it('un timecode inventé (hors de tout segment, dans un média plus court) est refusé', () => {
    const { accepted } = validateSuggestions(
      [suggestion({ startSec: 1000, endSec: 1040 })],
      segments,
      DURATION,
    );
    expect(accepted).toEqual([]);
  });

  it.each([
    ['titre vide', { title: '   ' }],
    ['score hors de 0 à 1', { score: 1.5 }],
    ['score négatif', { score: -0.1 }],
    ['raison absente', { reason: undefined }],
    ['champ inconnu', { extra: 'x' }],
    ['temps non fini', { startSec: Number.NaN }],
  ])('rejette un objet hors schéma : %s', (_label, extra) => {
    const { accepted, rejected } = validateSuggestions([suggestion(extra)], segments, DURATION);
    expect(accepted).toEqual([]);
    expect(rejected).toHaveLength(1);
  });

  it('rejette ce qui n’est pas un objet, sans planter, et garde les bons éléments', () => {
    const { accepted, rejected } = validateSuggestions(
      [null, 'texte', 42, suggestion()],
      segments,
      DURATION,
    );
    expect(accepted).toHaveLength(1);
    expect(rejected.map((r) => r.index)).toEqual([0, 1, 2]);
  });

  it('écarte le doublon moins bien noté et garde les deux suggestions distinctes', () => {
    const { accepted, rejected } = validateSuggestions(
      [
        suggestion({ startSec: 20, endSec: 80, score: 0.6 }),
        suggestion({ startSec: 40, endSec: 80, score: 0.9 }),
        suggestion({ startSec: 120, endSec: 160, score: 0.5 }),
      ],
      segments,
      DURATION,
    );
    expect(accepted.map((a) => [a.startSec, a.endSec])).toEqual([
      [40, 80],
      [120, 160],
    ]);
    expect(rejected).toEqual([{ index: 0, reasons: ['recouvre une suggestion mieux notée'] }]);
  });

  it('un recouvrement faible n’est pas un doublon', () => {
    const { accepted } = validateSuggestions(
      [
        suggestion({ startSec: 0, endSec: 40, score: 0.9 }),
        suggestion({ startSec: 20, endSec: 60, score: 0.8 }),
      ],
      segments,
      DURATION,
      { ...DEFAULT_CLIP_RULES, maxOverlapRatio: 0.5 },
    );
    expect(accepted).toHaveLength(2);
  });

  it('une transcription vide ne laisse rien passer', () => {
    expect(validateSuggestions([suggestion()], [], DURATION).accepted).toEqual([]);
  });
});

describe('ajustement IN/OUT et format (AC-CLIP-003)', () => {
  it('accepte des points libres dans le média, avec le format choisi', () => {
    expect(adjustClip({ startSec: 23.5, endSec: 71, format: '9:16' }, DURATION)).toEqual({
      ok: true,
      clip: { startSec: 23.5, endSec: 71, format: '9:16' },
    });
  });

  it.each([
    [{ startSec: -1, endSec: 30, format: '16:9' as const }, 'IN avant le début du média'],
    [{ startSec: 100, endSec: 181, format: '16:9' as const }, 'OUT après la fin du média'],
    [{ startSec: 50, endSec: 50, format: '16:9' as const }, 'OUT doit suivre IN'],
    [{ startSec: 50, endSec: 60, format: '16:9' as const }, 'durée sous 15 s'],
    [{ startSec: 0, endSec: 120, format: '16:9' as const }, 'durée au-dessus de 90 s'],
  ])('refuse %j', (edit, reason) => {
    const result = adjustClip(edit, DURATION);
    expect(result.ok).toBe(false);
    expect(!result.ok && result.reasons).toContain(reason);
  });

  it('accepte exactement les bornes de durée et de média', () => {
    expect(adjustClip({ startSec: 0, endSec: 15, format: '1:1' }, DURATION).ok).toBe(true);
    expect(adjustClip({ startSec: 90, endSec: 180, format: '1:1' }, DURATION).ok).toBe(true);
  });

  it('refuse des points non numériques', () => {
    expect(adjustClip({ startSec: Number.NaN, endSec: 30, format: '16:9' }, DURATION).ok).toBe(
      false,
    );
  });
});

describe('cadrage vertical et zones de sécurité (AC-CLIP-006)', () => {
  const source = { width: 1920, height: 1080 };
  const zone = SAFE_ZONES['vertical-9x16'] ?? { top: 0, bottom: 0, left: 0, right: 0 };

  it('découpe une fenêtre 9:16 de la hauteur complète, centrée sur le sujet', () => {
    const crop = verticalCrop(source, { x: 900, y: 200, width: 200, height: 300 });
    expect(crop).toEqual({ x: 696, y: 0, width: 608, height: 1080 });
  });

  it('recale la fenêtre dans l’image quand le sujet est au bord', () => {
    expect(verticalCrop(source, { x: 0, y: 200, width: 100, height: 300 }).x).toBe(0);
    expect(verticalCrop(source, { x: 1800, y: 200, width: 120, height: 300 }).x).toBe(1920 - 608);
  });

  it('la correction manuelle remplace le centrage automatique', () => {
    expect(verticalCrop(source, { x: 900, y: 200, width: 200, height: 300 }, 400).x).toBe(96);
  });

  it('un sujet centré dans la zone de sécurité ne déclenche rien', () => {
    const subject = { x: 900, y: 300, width: 200, height: 400 };
    expect(safeZoneViolations(verticalCrop(source, subject), subject, zone)).toEqual([]);
  });

  it('signale chaque bord dépassé', () => {
    const crop = { x: 0, y: 0, width: 608, height: 1080 };
    expect(safeZoneViolations(crop, { x: 0, y: 500, width: 100, height: 100 }, zone)).toEqual([
      'le sujet dépasse la zone de sécurité à gauche',
    ]);
    expect(safeZoneViolations(crop, { x: 300, y: 500, width: 300, height: 100 }, zone)).toEqual([
      'le sujet dépasse la zone de sécurité à droite',
    ]);
    expect(safeZoneViolations(crop, { x: 200, y: 20, width: 100, height: 100 }, zone)).toEqual([
      'le sujet dépasse la zone de sécurité en haut',
    ]);
    expect(safeZoneViolations(crop, { x: 200, y: 800, width: 100, height: 200 }, zone)).toEqual([
      'le sujet dépasse la zone de sécurité en bas',
    ]);
  });
});
