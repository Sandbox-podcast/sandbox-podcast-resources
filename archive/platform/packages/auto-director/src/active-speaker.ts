import type { DirectorConfig } from './config.ts';
import type { LevelFrame, ParticipantId, SpeakerSnapshot } from './types.ts';

interface ParticipantState {
  smoothDb: number;
  aboveSinceMs: number | null;
  belowSinceMs: number | null;
  speaking: boolean;
}

const SILENCE_DB = -100;
/** Durée pendant laquelle il faut ne plus se chevaucher pour sortir de la conversation croisée. */
const CROSSTALK_EXIT_MS = 600;

/**
 * Détecte qui parle et qui est le locuteur dominant, sans changer de locuteur à chaque bruit.
 * Déterministe : le temps vient des trames, jamais de l'horloge.
 *
 * Mécanismes : lissage du niveau, seuils de début et de fin différents (hystérésis), durée
 * minimale de parole (rejette clics et chocs), temps de maintien (garde les respirations),
 * marge et durée pour remplacer le locuteur dominant, conversation croisée, duo.
 */
export class ActiveSpeakerEngine {
  private readonly config: DirectorConfig;
  private readonly participants = new Map<ParticipantId, ParticipantState>();
  private lastTimeMs: number | null = null;
  private active: ParticipantId | null = null;
  private activeSinceMs: number | null = null;
  private previousActive: ParticipantId | null = null;
  private challenger: { id: ParticipantId; sinceMs: number } | null = null;
  private multiSinceMs: number | null = null;
  private fewSinceMs: number | null = null;
  private crosstalk = false;
  private lastSpeechMs: number | null = null;
  private readonly switches: { timeMs: number; from: ParticipantId; to: ParticipantId }[] = [];

  constructor(config: DirectorConfig) {
    this.config = config;
  }

  update(frame: LevelFrame): SpeakerSnapshot {
    const now = frame.timeMs;
    const dt = this.lastTimeMs === null ? 0 : Math.max(0, now - this.lastTimeMs);
    this.lastTimeMs = now;
    const alpha = dt === 0 ? 1 : 1 - Math.exp(-dt / this.config.smoothingMs);

    // Les participants absents de la trame sont traités comme silencieux.
    const ids = new Set<ParticipantId>([
      ...this.participants.keys(),
      ...Object.keys(frame.levelsDb),
    ]);
    for (const id of ids) {
      const level = frame.levelsDb[id] ?? SILENCE_DB;
      const state = this.participants.get(id) ?? {
        smoothDb: level,
        aboveSinceMs: null,
        belowSinceMs: null,
        speaking: false,
      };
      this.participants.set(id, state);
      state.smoothDb += alpha * (level - state.smoothDb);
      this.updateSpeaking(state, now);
    }

    const speakers = [...this.participants.entries()]
      .filter(([, s]) => s.speaking)
      .map(([id]) => id);
    if (speakers.length > 0) this.lastSpeechMs = now;

    this.updateActive(speakers, now);
    this.updateCrosstalk(speakers.length, now);

    return {
      speakers,
      active: this.active,
      activeSinceMs: this.activeSinceMs,
      marginDb: this.marginDb(),
      crosstalk: this.crosstalk,
      duo: this.detectDuo(now),
      lastSpeechMs: this.lastSpeechMs,
    };
  }

  private updateSpeaking(state: ParticipantState, now: number): void {
    const { onThresholdDb, offThresholdDb, minSpeechMs, hangoverMs } = this.config;
    if (!state.speaking) {
      if (state.smoothDb >= onThresholdDb) {
        state.aboveSinceMs ??= now;
        if (now - state.aboveSinceMs >= minSpeechMs) {
          state.speaking = true;
          state.belowSinceMs = null;
        }
      } else {
        state.aboveSinceMs = null;
      }
    } else if (state.smoothDb < offThresholdDb) {
      state.belowSinceMs ??= now;
      if (now - state.belowSinceMs >= hangoverMs) {
        state.speaking = false;
        state.aboveSinceMs = null;
      }
    } else {
      state.belowSinceMs = null;
    }
  }

  private updateActive(speakers: readonly ParticipantId[], now: number): void {
    if (speakers.length === 0) {
      this.active = null;
      this.activeSinceMs = null;
      this.challenger = null;
      return;
    }
    const loudest = this.loudest(speakers);
    const currentIsSpeaking = this.active !== null && speakers.includes(this.active);

    if (!currentIsSpeaking) {
      this.setActive(loudest, now);
      return;
    }
    if (this.active !== null && loudest !== this.active) {
      const margin = this.smooth(loudest) - this.smooth(this.active);
      if (margin >= this.config.switchMarginDb) {
        if (this.challenger?.id !== loudest) this.challenger = { id: loudest, sinceMs: now };
        if (now - this.challenger.sinceMs >= this.config.switchHoldMs) this.setActive(loudest, now);
        return;
      }
    }
    this.challenger = null;
  }

  private setActive(id: ParticipantId, now: number): void {
    if (this.previousActive !== null && this.previousActive !== id) {
      this.switches.push({ timeMs: now, from: this.previousActive, to: id });
    }
    this.previousActive = id;
    this.active = id;
    this.activeSinceMs = now;
    this.challenger = null;
  }

  private updateCrosstalk(speakerCount: number, now: number): void {
    if (speakerCount >= 2) {
      this.fewSinceMs = null;
      this.multiSinceMs ??= now;
      if (now - this.multiSinceMs >= this.config.crosstalkMs) this.crosstalk = true;
      return;
    }
    this.multiSinceMs = null;
    if (!this.crosstalk) return;
    this.fewSinceMs ??= now;
    if (now - this.fewSinceMs >= CROSSTALK_EXIT_MS) {
      this.crosstalk = false;
      this.fewSinceMs = null;
    }
  }

  /** Deux personnes qui se répondent vivement, et seulement elles. */
  private detectDuo(now: number): readonly [ParticipantId, ParticipantId] | null {
    const { duoWindowMs, duoMinSwitches } = this.config;
    while (this.switches[0] && now - this.switches[0].timeMs > duoWindowMs) this.switches.shift();
    if (this.switches.length < duoMinSwitches) return null;
    const people = new Set(this.switches.flatMap((s) => [s.from, s.to]));
    if (people.size !== 2) return null;
    const [a, b] = [...people].sort();
    return a !== undefined && b !== undefined ? [a, b] : null;
  }

  private smooth(id: ParticipantId): number {
    return this.participants.get(id)?.smoothDb ?? SILENCE_DB;
  }

  private loudest(ids: readonly ParticipantId[]): ParticipantId {
    return ids.reduce(
      (best, id) => (this.smooth(id) > this.smooth(best) ? id : best),
      ids[0] ?? '',
    );
  }

  /** Écart entre le locuteur actif et le plus fort des autres, en dB (0 à 30). */
  private marginDb(): number {
    if (this.active === null) return 0;
    const others = [...this.participants.keys()].filter((id) => id !== this.active);
    const strongestOther = others.reduce((max, id) => Math.max(max, this.smooth(id)), SILENCE_DB);
    return Math.max(0, Math.min(30, this.smooth(this.active) - strongestOther));
  }
}
