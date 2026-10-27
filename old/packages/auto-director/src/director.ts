import { ActiveSpeakerEngine } from './active-speaker.ts';
import { DEFAULT_CONFIG, type DirectorConfig } from './config.ts';
import type {
  DecisionSource,
  DirectorDecision,
  LevelFrame,
  ParticipantId,
  SceneCatalog,
  Shot,
  SpeakerSnapshot,
} from './types.ts';

export interface ControlEvent {
  timestampMs: number;
  type: 'AUTO_ENABLED' | 'AUTO_DISABLED';
}

const clamp01 = (value: number): number => Math.max(0, Math.min(1, value));

/**
 * Réalisateur automatique : transforme le flux des niveaux audio en décisions de plan
 * (GROUP, SPEAKER_FOCUS, DUO, PRESENTATION) et journalise chacune avec sa raison.
 *
 * Règles, par ordre de priorité : présentation, réalisation manuelle, conversation croisée,
 * duo, locuteur stable, silence prolongé. Un plan dure au moins `minShotMs`.
 */
export class AutoDirector {
  readonly journal: DirectorDecision[] = [];
  readonly events: ControlEvent[] = [];

  private readonly config: DirectorConfig;
  private readonly catalog: SceneCatalog;
  private readonly engine: ActiveSpeakerEngine;
  private auto = true;
  private presentationActive = false;
  private current: Shot | null = null;
  private lastCutMs: number | null = null;
  private lastSnapshot: SpeakerSnapshot | null = null;

  constructor(catalog: SceneCatalog, config: DirectorConfig = DEFAULT_CONFIG) {
    this.catalog = catalog;
    this.config = config;
    this.engine = new ActiveSpeakerEngine(config);
  }

  get shot(): Shot | null {
    return this.current;
  }

  get isAuto(): boolean {
    return this.auto;
  }

  /** Analyse une trame de niveaux. Retourne la décision prise, s'il y en a une. */
  tick(frame: LevelFrame): DirectorDecision | null {
    const snapshot = this.engine.update(frame);
    this.lastSnapshot = snapshot;
    if (!this.auto) return null;
    const now = frame.timeMs;

    if (this.current === null)
      return this.commit(this.groupShot(), 'AUTO', now, snapshot, 'plan initial', 1);
    if (this.presentationActive) {
      return this.current.mode === 'PRESENTATION'
        ? null
        : this.commit(this.presentationShot(), 'AUTO', now, snapshot, 'présentation en cours', 1);
    }
    if (this.lastCutMs !== null && now - this.lastCutMs < this.config.minShotMs) return null;

    const wanted = this.decide(snapshot, now);
    if (wanted === null || this.sameShot(wanted.shot, this.current)) return null;
    return this.commit(wanted.shot, 'AUTO', now, snapshot, wanted.reason, wanted.confidence);
  }

  /** Le Producer désactive ou réactive la réalisation automatique. Effet immédiat. */
  setAuto(auto: boolean, timeMs: number): void {
    if (auto === this.auto) return;
    this.auto = auto;
    this.events.push({ timestampMs: timeMs, type: auto ? 'AUTO_ENABLED' : 'AUTO_DISABLED' });
    // En reprenant la main, on laisse au plan courant sa durée minimale.
    if (auto) this.lastCutMs = timeMs;
  }

  /** Prise manuelle d'un plan. Désactive la réalisation automatique. */
  manualTake(shot: Shot, timeMs: number): DirectorDecision {
    this.setAuto(false, timeMs);
    return this.commit(shot, 'MANUAL', timeMs, this.lastSnapshot, 'prise manuelle du Producer', 1);
  }

  /** Une présentation commence ou se termine (décidé par la régie). */
  setPresentation(active: boolean, timeMs: number): DirectorDecision | null {
    if (active === this.presentationActive) return null;
    this.presentationActive = active;
    if (!this.auto) return null;
    if (active) {
      return this.commit(
        this.presentationShot(),
        'AUTO',
        timeMs,
        this.lastSnapshot,
        'présentation en cours',
        1,
      );
    }
    return this.commit(
      this.groupShot(),
      'AUTO',
      timeMs,
      this.lastSnapshot,
      'fin de la présentation',
      1,
    );
  }

  private decide(
    snapshot: SpeakerSnapshot,
    now: number,
  ): { shot: Shot; reason: string; confidence: number } | null {
    if (snapshot.crosstalk) {
      return { shot: this.groupShot(), reason: 'conversation croisée', confidence: 0.8 };
    }
    if (snapshot.duo) {
      const [a, b] = snapshot.duo;
      return {
        shot: this.duoShot(a, b),
        reason: `échanges rapides entre ${a} et ${b}`,
        confidence: 0.7,
      };
    }
    if (snapshot.active !== null && snapshot.activeSinceMs !== null) {
      const activeFor = now - snapshot.activeSinceMs;
      if (activeFor >= this.config.focusAfterMs) {
        const confidence = clamp01(
          0.5 + Math.min(5, activeFor / 2000) * 0.06 + snapshot.marginDb / 60,
        );
        return {
          shot: this.focusShot(snapshot.active),
          reason: `locuteur stable depuis ${String(Math.round(activeFor))} ms`,
          confidence: Number(confidence.toFixed(2)),
        };
      }
      return null;
    }
    if (
      snapshot.speakers.length === 0 &&
      this.current?.mode !== 'GROUP' &&
      snapshot.lastSpeechMs !== null &&
      now - snapshot.lastSpeechMs >= this.config.silenceToGroupMs
    ) {
      return { shot: this.groupShot(), reason: 'silence prolongé', confidence: 0.9 };
    }
    return null;
  }

  private commit(
    shot: Shot,
    source: DecisionSource,
    timeMs: number,
    snapshot: SpeakerSnapshot | null,
    reason: string,
    confidence: number,
  ): DirectorDecision {
    const decision: DirectorDecision = {
      timestampMs: timeMs,
      shot,
      source,
      speakerId: snapshot?.active ?? null,
      reason,
      confidence,
    };
    this.current = shot;
    this.lastCutMs = timeMs;
    this.journal.push(decision);
    return decision;
  }

  private sameShot(a: Shot, b: Shot): boolean {
    return a.sceneId === b.sceneId;
  }

  private groupShot(): Shot {
    return { mode: 'GROUP', participants: [], sceneId: this.catalog.group };
  }
  private focusShot(id: ParticipantId): Shot {
    return { mode: 'SPEAKER_FOCUS', participants: [id], sceneId: this.catalog.focus(id) };
  }
  private duoShot(a: ParticipantId, b: ParticipantId): Shot {
    return { mode: 'DUO', participants: [a, b], sceneId: this.catalog.duo(a, b) };
  }
  private presentationShot(): Shot {
    return { mode: 'PRESENTATION', participants: [], sceneId: this.catalog.presentation };
  }
}
