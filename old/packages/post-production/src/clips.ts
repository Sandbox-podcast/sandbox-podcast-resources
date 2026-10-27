import { z } from 'zod';
import type { TranscriptSegment } from './transcript.ts';

/** AC-CLIP-001 : la forme d'une suggestion. Elle peut venir d'un modèle : rien n'est supposé juste. */
export const clipSuggestionSchema = z.strictObject({
  startSec: z.number().min(0),
  endSec: z.number().min(0),
  title: z.string().trim().min(1).max(120),
  hook: z.string().trim().min(1).max(300),
  reason: z.string().trim().min(1).max(600),
  score: z.number().min(0).max(1),
});
export type ClipSuggestion = z.infer<typeof clipSuggestionSchema>;

export interface ClipRules {
  minDurationSec: number;
  maxDurationSec: number;
  /** Écart toléré entre un point proposé et la limite du segment le plus proche. */
  snapToleranceSec: number;
  /** Part de durée commune au-delà de laquelle deux suggestions sont des doublons. */
  maxOverlapRatio: number;
}

export const DEFAULT_CLIP_RULES: ClipRules = {
  minDurationSec: 15,
  maxDurationSec: 90,
  snapToleranceSec: 0.25,
  maxOverlapRatio: 0.5,
};

export interface RejectedSuggestion {
  index: number;
  reasons: string[];
}

export interface ValidatedSuggestions {
  accepted: (ClipSuggestion & { firstSegmentId: string; lastSegmentId: string })[];
  rejected: RejectedSuggestion[];
}

const nearest = (values: readonly number[], target: number): number | undefined =>
  values.reduce<number | undefined>(
    (best, v) => (best === undefined || Math.abs(v - target) < Math.abs(best - target) ? v : best),
    undefined,
  );

/**
 * AC-CLIP-005 : aucune suggestion n'est appliquée sans validation. Chaque suggestion doit respecter
 * le schéma, tenir dans la durée réelle du média, commencer au début d'un segment existant et finir à
 * la fin d'un segment existant (les points sont alors recalés exactement sur ces limites), avoir une
 * durée raisonnable, et ne pas doubler une suggestion mieux notée.
 */
export function validateSuggestions(
  raw: readonly unknown[],
  segments: readonly TranscriptSegment[],
  mediaDurationSec: number,
  rules: ClipRules = DEFAULT_CLIP_RULES,
): ValidatedSuggestions {
  const starts = segments.map((s) => s.startSec);
  const ends = segments.map((s) => s.endSec);
  const rejected: RejectedSuggestion[] = [];
  const candidates: { index: number; clip: ValidatedSuggestions['accepted'][number] }[] = [];

  raw.forEach((item, index) => {
    const parsed = clipSuggestionSchema.safeParse(item);
    if (!parsed.success) {
      rejected.push({
        index,
        reasons: parsed.error.issues.map(
          (i) => `${i.path.join('.') || 'suggestion'} : ${i.message}`,
        ),
      });
      return;
    }
    const clip = parsed.data;
    const reasons: string[] = [];
    if (clip.endSec <= clip.startSec) reasons.push('la fin doit suivre le début');
    if (clip.endSec > mediaDurationSec) reasons.push('la fin dépasse la durée du média');

    const start = nearest(starts, clip.startSec);
    const end = nearest(ends, clip.endSec);
    if (start === undefined || Math.abs(start - clip.startSec) > rules.snapToleranceSec)
      reasons.push('le début ne correspond à aucun début de segment');
    if (end === undefined || Math.abs(end - clip.endSec) > rules.snapToleranceSec)
      reasons.push('la fin ne correspond à aucune fin de segment');
    if (start !== undefined && end !== undefined) {
      const duration = end - start;
      if (duration < rules.minDurationSec)
        reasons.push(`durée sous ${String(rules.minDurationSec)} s`);
      if (duration > rules.maxDurationSec)
        reasons.push(`durée au-dessus de ${String(rules.maxDurationSec)} s`);
    }
    if (reasons.length > 0 || start === undefined || end === undefined) {
      rejected.push({ index, reasons });
      return;
    }
    const first = segments.find((s) => s.startSec === start);
    const last = segments.find((s) => s.endSec === end);
    if (!first || !last) {
      rejected.push({ index, reasons: ['segments introuvables'] });
      return;
    }
    candidates.push({
      index,
      clip: {
        ...clip,
        startSec: start,
        endSec: end,
        firstSegmentId: first.id,
        lastSegmentId: last.id,
      },
    });
  });

  // Les mieux notées d'abord ; une suggestion qui en recouvre trop une déjà retenue est un doublon.
  candidates.sort((a, b) => b.clip.score - a.clip.score || a.index - b.index);
  const accepted: ValidatedSuggestions['accepted'] = [];
  for (const { index, clip } of candidates) {
    const duplicate = accepted.some((kept) => {
      const common = Math.min(kept.endSec, clip.endSec) - Math.max(kept.startSec, clip.startSec);
      const shorter = Math.min(kept.endSec - kept.startSec, clip.endSec - clip.startSec);
      return common > 0 && common / shorter > rules.maxOverlapRatio;
    });
    if (duplicate) rejected.push({ index, reasons: ['recouvre une suggestion mieux notée'] });
    else accepted.push(clip);
  }
  accepted.sort((a, b) => a.startSec - b.startSec);
  rejected.sort((a, b) => a.index - b.index);
  return { accepted, rejected };
}

export type ClipFormat = '16:9' | '9:16' | '1:1';

export interface ClipEdit {
  startSec: number;
  endSec: number;
  format: ClipFormat;
}

export type AdjustResult = { ok: true; clip: ClipEdit } | { ok: false; reasons: string[] };

/** AC-CLIP-003 : l'utilisateur déplace les points IN/OUT et choisit le format ; bornes vérifiées. */
export function adjustClip(
  edit: ClipEdit,
  mediaDurationSec: number,
  rules: ClipRules = DEFAULT_CLIP_RULES,
): AdjustResult {
  const reasons: string[] = [];
  if (!Number.isFinite(edit.startSec) || !Number.isFinite(edit.endSec))
    return { ok: false, reasons: ['points non numériques'] };
  if (edit.startSec < 0) reasons.push('IN avant le début du média');
  if (edit.endSec > mediaDurationSec) reasons.push('OUT après la fin du média');
  const duration = edit.endSec - edit.startSec;
  if (duration <= 0) reasons.push('OUT doit suivre IN');
  else {
    if (duration < rules.minDurationSec)
      reasons.push(`durée sous ${String(rules.minDurationSec)} s`);
    if (duration > rules.maxDurationSec)
      reasons.push(`durée au-dessus de ${String(rules.maxDurationSec)} s`);
  }
  return reasons.length > 0 ? { ok: false, reasons } : { ok: true, clip: edit };
}

export interface Rect {
  x: number;
  y: number;
  width: number;
  height: number;
}

/**
 * Zones de sécurité d'un preset vertical, en part de la hauteur ou de la largeur de l'image.
 * Valeurs INDICATIVES (interfaces des plateformes qui masquent le haut, le bas et le côté) :
 * à valider avec les plateformes visées avant toute promesse.
 */
export interface SafeZone {
  top: number;
  bottom: number;
  left: number;
  right: number;
}

export const SAFE_ZONES: Record<string, SafeZone> = {
  'vertical-9x16': { top: 0.1, bottom: 0.2, left: 0.05, right: 0.1 },
};

const clamp = (value: number, min: number, max: number): number =>
  Math.min(max, Math.max(min, value));

/**
 * Cadrage 9:16 dans une source 16:9 : fenêtre de la hauteur complète, centrée sur le sujet (sa boîte,
 * en pixels de la source) puis recalée dans l'image. `manualCenterX` remplace le centrage automatique
 * (correction manuelle, AC-CLIP-006).
 */
export function verticalCrop(
  source: { width: number; height: number },
  subject: Rect,
  manualCenterX?: number,
): Rect {
  const width = Math.round((source.height * 9) / 16);
  const centerX = manualCenterX ?? subject.x + subject.width / 2;
  const x = Math.round(clamp(centerX - width / 2, 0, source.width - width));
  return { x, y: 0, width, height: source.height };
}

/** Le sujet reste-t-il entièrement dans la zone de sécurité du cadrage ? Retourne les dépassements. */
export function safeZoneViolations(crop: Rect, subject: Rect, zone: SafeZone): string[] {
  const issues: string[] = [];
  const left = crop.x + crop.width * zone.left;
  const right = crop.x + crop.width * (1 - zone.right);
  const top = crop.y + crop.height * zone.top;
  const bottom = crop.y + crop.height * (1 - zone.bottom);
  if (subject.x < left) issues.push('le sujet dépasse la zone de sécurité à gauche');
  if (subject.x + subject.width > right)
    issues.push('le sujet dépasse la zone de sécurité à droite');
  if (subject.y < top) issues.push('le sujet dépasse la zone de sécurité en haut');
  if (subject.y + subject.height > bottom)
    issues.push('le sujet dépasse la zone de sécurité en bas');
  return issues;
}
